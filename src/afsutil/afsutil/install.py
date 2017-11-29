# Copyright (c) 2014-2015 Sine Nomine Associates
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""Install and remove Transarc-style OpenAFS distributions."""

import logging
import os
import re
import shutil
import socket
import glob
import pprint
import shlex

from afsutil.system import file_should_exist, \
                           directory_should_exist, \
                           directory_should_not_exist, \
                           network_interfaces, \
                           mkdirp, touch, cat, sh

from afsutil.misc import lists2dict

logger = logging.getLogger(__name__)


def is_afs_path(path):
    """Returns true if this is one of ours."""
    return path.startswith("/usr/afs/") or \
           path.startswith("/usr/afsws/") or \
           path.startswith("/usr/vice/")

def copy_files(src, dst, symlinks=True, force=False):
    """Copy a tree of files."""
    def _ignore_symlinks(path, names):
        ignore = []
        for name in names:
            if os.path.islink(os.path.join(path, name)):
                ignore.append(name)
        return ignore

    directory_should_exist(src, "Source directory '%s' does not exist!" % src)
    if force:
        if os.path.exists(dst):
            if not is_afs_path(dst):
                raise AssertionError("Refusing to remove unrecognized directory %s" % (dst))
            logger.info("Removing previous '%s' directory.", dst)
            shutil.rmtree(dst)
    else:
        directory_should_not_exist(dst, "Destination directory '%s' already exists! "
                                        "(use --force to override)" % dst)
    logger.info("Installing files from '%s' to '%s'." % (src, dst))
    if symlinks:
        shutil.copytree(src, dst)
    else:
        shutil.copytree(src, dst, ignore=_ignore_symlinks)

def remove_file(path):
    """Remove a single file."""
    if os.path.exists(path):
        logger.info("Removing %s", path)
        os.remove(path)

def remove_files(path, quiet=False):
    """Remove a tree of files."""
    if not os.path.exists(path):
        return
    if not is_afs_path(path):
        raise AssertionError("Refusing to remove unrecognized directory %s" % (path))
    if not quiet:
        logger.info("Removing %s", path)
    shutil.rmtree(path)

class Installer(object):
    """Base class for OpenAFS installers."""

    def __init__(self,
                 dirs=None,
                 components=None,
                 cell='localcell',
                 hosts=None,
                 realm=None,
                 csdb=None,
                 force=False,
                 purge=False,
                 verbose=False,
                 options=None,
                 pre_install=None,
                 post_install=None,
                 pre_remove=None,
                 post_remove=None,
                 **kwargs):
        """
        dirs: directories for pre/post installation/removal
        components: a list of strings, e.g., ['client', 'server']
        cell: afs cell name to be configured
        hosts: hosts to set in CellServDB files, detect if None
        realm: kerberos realm name, if different than the cell name
        csdb:  path to optional CellServDB.dist listing foreign cells
        force: overwrite existing files, otherwise raise an AssertionError
        purge: delete config, volumes, and cache too.
        verbose: log more information
        options: the command options for bosserver, afsd, etc
        pre_install: an optional command to run before installation
        post_install: an optional command to run after installation
        pre_remove: an optional command to run before removal
        post_remove: an optional command to run after removal
        """
        if dirs is None: # Default to transarc-style.
            dirs = {
                'AFS_CONF_DIR': "/usr/afs/etc",
                'AFS_DATA_DIR': "/usr/vice/etc",
                'AFS_CACHE_DIR': "/usr/vice/cache",
                'AFS_MOUNT_DIR': "/afs",
            }
        if components is None: # Default to all.
            components = ['client', 'server']
        if realm is None:
            realm = cell.upper()
        self.dirs = dirs
        self.do_server = 'server' in components
        self.do_client = 'client' in components
        self.cell = cell
        self.realm = realm
        self.csdb = csdb
        self.force = force
        self.purge = purge
        self.verbose = verbose
        self.hostnames = hosts
        self.cellhosts = None # Defer to pre-install.
        self.options = lists2dict(options)
        self.scripts = {
            'pre_install': pre_install,
            'post_install': post_install,
            'pre_remove': pre_remove,
            'post_remove': post_remove,
        }

    def install(self):
        """This sould be implemented by the children."""
        raise AssertionError("Not implemented.")

    def remove(self):
        """This sould be implemented by the children."""
        raise AssertionError("Not implemented.")

    def _lookup_cellhosts(self, hostnames):
        """Create a list of (address,hostname) tuples from a list of hostnames.
        If hostnames is None, then detect the (address,hostname) for the local
        system by checking the network interfaces on this system."""
        cellhosts = set()
        # Use the addresses from the DNS lookup of the given hostnames.
        # We do not want loopback addresses in the CellServDB file.
        for name in hostnames: # hosts is a list of names or quad-dot-address strings.
            logger.info("Looking up ip address of hostname %s." % (name))
            addr = socket.gethostbyname(name)
            if addr.startswith('127.'):
                raise AssertionError("Loopback address %s given for hostname %s."
                                     " Please check your /etc/hosts file." % (addr,name))
            cellhosts.add((addr, name))
        return list(cellhosts)

    def _detect_cellhosts(self):
        # No hosts given; Assume we are using this host. First try to get a
        # non-loopback IP address from the DNS lookup; Fall back to getting
        # an addess from the network interface.  If this host has multiple
        # interfaces, there's no good way to detect which ones are internal
        # only, so at this point we have to give up.
        cellhosts = set()
        name = os.uname()[1]
        logger.info("Trying to detect cellhosts.")
        logger.info("Looking up ip address of hostname %s." % (name))
        addr = socket.gethostbyname(name)
        if addr.startswith('127.'):
            logger.info("Looking up ip address from network interfaces.")
            addrs = network_interfaces()  # should return non-loopback ip addresses.
            if len(addrs) == 0:
                raise AssertionError("No network interfaces found.")
            if len(addrs) > 1:
                raise AssertionError("Multiple network interfaces present."
                                     " Please specify a hostname.")
            addr = addrs[0]
            if addr.startswith('127.'):
                raise AssertionError("Loopback address returned by network_interfaces.")
        cellhosts.add((addr, name))
        return list(cellhosts)

    def _make_vice_dirs(self):
        """Create test vice directories."""
        parts = ('a', 'b')
        vicedirs =  ['/vicep'+p for p in parts]
        for path in vicedirs:
            if not os.path.exists(path):
                logger.info("Making vice partition '%s'.", path)
                os.mkdir(path)
                touch(os.path.join(path, "AlwaysAttach"))
                touch(os.path.join(path, "PURGE_VOLUMES"))

    def _set_cell_config(self, path, cell, hosts, ext=""):
        """Write a default CellServDB and ThisCell file."""
        # The bosserver creates symlinks for the client side configuration. Be
        # sure to remove the symlinks so we do not clobber the server
        # configuration.
        mkdirp(path)
        os.chmod(path, 0755)  # Make the bosserver happy.
        cellservdb = os.path.join(path, "CellServDB%s" % (ext))
        thiscell = os.path.join(path, "ThisCell")
        if os.path.islink(cellservdb):
            os.remove(cellservdb)
        if os.path.islink(thiscell):
            os.remove(thiscell)
        with open(cellservdb, 'w') as f:
            f.write(">%s    #Cell name\n" % (cell))
            for addr,name in hosts:
                f.write("%s         #%s\n"  % (addr,name))
        with open(thiscell, 'w') as f:
            f.write(cell)

    def _set_krb_config(self, path, cell, realm):
        """Write the krb.conf file if needed."""
        if cell.lower() != realm.lower():
            with open(os.path.join(path, "krb.conf"), 'w') as f:
                f.write("%s\n" % (realm))

    def _set_cache_info(self, path, root, cache, size):
        """Create the cacheinfo file."""
        dst = os.path.join(path, 'cacheinfo')
        with open(dst, 'w') as f:
            f.write("%s:%s:%d\n" % (root, cache, size))

    def _purge_volumes(self):
        for part in glob.glob('/vicep*'):
            if re.match(r'/vicep([a-z]|[a-h][a-z]|i[a-v])$', part):
                if not os.path.exists(os.path.join(part, "PURGE_VOLUMES")):
                    logger.info("Skipping volume purge in '%s'; PURGE_VOLUMES file not found.", part)
                else:
                    logger.info("Purging volume data in '%s'.", part)
                    for vol in glob.glob(os.path.join(part, "*.vol")):
                        os.remove(vol)
                    afsidat = os.path.join(part, 'AFSIDat')
                    if os.path.exists(afsidat):
                        shutil.rmtree(afsidat)

    def _purge_cache(self):
        if os.path.exists("/usr/vice/cache"):
            logger.info("Removing cache item files.")
            remove_file("/usr/vice/cache/CacheItems")
            remove_file("/usr/vice/cache/CellItems")
            remove_file("/usr/vice/cache/VolumeItems")
            logger.info("Removing /usr/vice/cache/D* files.")
            for d in os.listdir("/usr/vice/cache"):
                if re.match(r'^D\d+$', d):
                    remove_files("/usr/vice/cache/%s" % (d), quiet=(not self.verbose))

    def pre_install(self):
        """Pre installation steps."""
        # Get name and IP address of the cell hosts. Use the local hostname
        # and local interface if the cell hosts are not specified. Do this
        # before we start installing to catch errors early.
        logger.debug("pre_install")
        if self.scripts['pre_install']:
            logger.info("Running pre-install script.")
            args = shlex.split(self.scripts['pre_install'])
            sh(*args, output=False)
        if self.cellhosts is None:
            if self.hostnames:
                self.cellhosts = self._lookup_cellhosts(self.hostnames)
            else:
                self.cellhosts = self._detect_cellhosts()
            logger.info("Cell hosts are: %s", pprint.pformat(self.cellhosts))
        if self.do_server:
            self._make_vice_dirs()
        if self.do_client:
            if self.csdb is not None:
                file_should_exist(self.csdb)

    def post_install(self):
        """Post installation steps."""
        logger.debug("post_install")
        if self.do_server:
            self._set_cell_config(self.dirs['AFS_CONF_DIR'], self.cell, self.cellhosts)
            self._set_krb_config(self.dirs['AFS_CONF_DIR'], self.cell, self.realm)
        if self.do_client:
            # Create the CellServDB and ThisCell files. Remove any symlinks that
            # may have been created by the bosserver. Combine the optional CellServDB.dist
            # to access other cells.
            csdb = os.path.join(self.dirs['AFS_DATA_DIR'], "CellServDB")
            local = os.path.join(self.dirs['AFS_DATA_DIR'], "CellServDB.local")
            dist = os.path.join(self.dirs['AFS_DATA_DIR'], "CellServDB.dist")
            self._set_cell_config(self.dirs['AFS_DATA_DIR'], self.cell, self.cellhosts, ext=".local")
            if self.csdb:
                shutil.copyfile(self.csdb, dist)
            else:
                touch(dist)
            cat([local, dist], csdb)
            # Set the cache info parameters.
            # XXX: size should be calculated from partition, if mounted.
            cache_size = 102000  # k blocks
            self._set_cache_info(
                self.dirs['AFS_DATA_DIR'],
                self.dirs['AFS_MOUNT_DIR'],
                self.dirs['AFS_CACHE_DIR'],
                cache_size)
        if self.scripts['post_install']:
            logger.info("Running post-install script.")
            args = shlex.split(self.scripts['post_install'])
            sh(*args, output=False)

    def pre_remove(self):
        """Pre remove steps."""
        logger.debug("pre_remove")
        if self.scripts['pre_remove']:
            logger.info("Running pre-remove script.")
            args = shlex.split(self.scripts['pre_remove'])
            sh(*args, output=False)

    def post_remove(self):
        """Post remove steps."""
        logger.debug("post_remove")
        if self.purge:
            if self.do_server:
                remove_files("/usr/afs/")
                self._purge_volumes()
            if self.do_client:
                self._purge_cache()
        if self.scripts['post_remove']:
            logger.info("Running post-remove script.")
            args = shlex.split(self.scripts['post_remove'])
            sh(*args, output=False)

def installer(dist='transarc', **kwargs):
    if dist == 'transarc':
        from afsutil.transarc import TransarcInstaller
        return TransarcInstaller(**kwargs)
    elif dist == 'rpm':
        from afsutil.rpm import RpmInstaller
        return RpmInstaller(**kwargs)
    else:
        raise ValueError("Unsupported 'dist' option: {0}".format(dist))

def install(dist='transarc', **kwargs):
    installer(dist, **kwargs).install()

def remove(dist='transarc', **kwargs):
    installer(dist, **kwargs).remove()
