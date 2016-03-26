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

import errno
import logging
import os
import re
import shutil
import sys
import socket
import glob

from afsutil.system import file_should_exist, directory_should_exist, directory_should_not_exist, \
                           is_loaded, is_running, mkdirp, run, touch, cat, \
                           network_interfaces, configure_dynamic_linker

logger = logging.getLogger(__name__)

#
# Transarc style install paths.
#
AFS_CONF_DIR = "/usr/afs/etc"
AFS_KERNEL_DIR = "/usr/vice/etc"
AFS_SRV_BIN_DIR =  "/usr/afs/bin"
AFS_SRV_SBIN_DIR = "/usr/afs/bin"
AFS_SRV_LIBEXEC_DIR = "/usr/afs/bin"
AFS_SRV_LIB_DIR = "/usr/afs/lib"
AFS_DB_DIR = "/usr/afs/db"
AFS_LOGS_DIR = "/usr/afs/logs"
AFS_LOCAL_DIR = "/usr/afs/local"
AFS_BACKUP_DIR = "/usr/afs/backup"
AFS_BOS_CONFIG_DIR = "/usr/afs/local"
AFS_DATA_DIR = "/usr/vice/etc"
AFS_CACHE_DIR = "/usr/vice/cache"
AFS_MOUNT_DIR = "/afs"
AFS_WS_DIR = "/usr/afsws"
SYSCONFIG = "/etc/sysconfig"

#
# Fully qualified AFS command paths for Transarc style installs.
#
AKLOG = "/usr/afsws/bin/aklog"
ASETKEY = "/usr/afs/bin/asetkey"
BOS = "/usr/afs/bin/bos"
FS = "/usr/afs/bin/fs"
PTS = "/usr/afs/bin/pts"
RXDEBUG = "/usr/afsws/etc/rxdebug"
TOKENS = "/usr/afsws/bin/tokens"
UDEBUG = "/usr/afs/bin/udebug"
UNLOG = "/usr/afsws/bin/unlog"
VOS = "/usr/afs/bin/vos"

# Basic init script to start and stop the servers
# independently from the client.
AFS_SERVER_RC = """#!/bin/bash
# Basic init script to start/stop the OpenAFS servers.
# chkconfig: 2345 49 51

if [ -f /etc/rc.d/init.d/functions ] ; then
    . /etc/rc.d/init.d/functions
    afs_rh=1
else
    # special (RedHat) functions not available...
    function echo_failure () { echo -n " - failed." ; }
    function echo_success () { echo -n " - successful." ; }
fi

is_on() {
    if  test "$1" = "on" ; then return 0
    else return 1
    fi
}

SYSCNF=${SYSCNF:-/etc/sysconfig/afs}
if [ -f $SYSCNF ] ; then
    . $SYSCNF
fi

BOS=${BOS:-/usr/afs/bin/bos}
BOSSERVER=${BOSSERVER:-/usr/afs/bin/bosserver}

start() {
    if [ ! "$afs_rh" -o ! -f /var/lock/subsys/afs-server ]; then
        if test -x $BOSSERVER ; then
            echo "Starting AFS servers..... "
            $BOSSERVER
            test "$afs_rh" && touch /var/lock/subsys/afs-server
            if is_on $WAIT_FOR_SALVAGE; then
                sleep 10
                while $BOS status localhost fs 2>&1 | grep 'Auxiliary.*salvaging'; do
                    echo "Waiting for salvager to finish..... "
                    sleep 10
                done
            fi
        fi
    fi
}

stop() {
    if [ ! "$afs_rh" -o -f /var/lock/subsys/afs-server ]; then
        if  test -x $BOS ; then
            echo "Stopping AFS servers..... "
            $BOS shutdown localhost -localauth -wait
            pkill -HUP bosserver
        fi
        rm -f /var/lock/subsys/afs-server
    fi
}

case "$1" in
  start)
      start
      ;;
  stop)
      stop
      ;;
  restart)
      $0 stop
      $0 start
      ;;
  *)
      echo $"Usage: $0 {start|stop|restart}"
      exit 1
esac
"""

def _solaris_afs_driver():
    """Return the name of the afs driver for the current platform."""
    out = run('/bin/isalist')
    if 'amd64' in out:
        driver = '/kernel/drv/amd64/afs'
    elif 'sparcv9' in out:
        driver = '/kernel/drv/sparcv9/afs'
    else:
        driver = '/kernel/drv/afs'
    return driver

def _detect_sysname():
    sysname = None
    try:
        with open("src/config/Makefile.config", "r") as f:
            for line in f.readlines():
                match = re.match(r'SYS_NAME\s*=\s*(\S+)', line)
                if match:
                    sysname = match.group(1)
                    break
    except IOError as e:
        pass
    return sysname

def _detect_dest():
    dest = None
    sysname = _detect_sysname()
    if sysname:
        dest = "%s/dest" % (sysname)
    return dest

def _check_dest(dest):
    if dest is None:
        raise ValueError("Unable to find dest in current directory.")
    if not os.path.exists(dest):
        raise ValueError("dest dir '%s' not found." % dest)

class TransarcInstaller(object):
    """Install a Transarc-style distribution of OpenAFS on linux or solaris."""

    def __init__(self, dest=None, cell='localcell', hosts=None, realm=None, csdb=None, force=False, **kwargs):
        """Initialize the Transarc-style installer.

        dest: path to the 'dest' directory created by previous make dest
              If None, try to detect the sysname and find the dest directory
              in the current working directory.
        cell: afs cell name to be configured
        hosts: hosts to set in CellServDB files. If none, use the current
               machine (non-loopback) address
        realm: kerberos realm name, if different than the cell naem
        force: overwrite existing files, otherwise raise an AssertionError
        csdb:  path to optional CellServDB.dist listing foreign cells
        """
        if dest is None:
            dest = _detect_dest()
        _check_dest(dest)
        if realm is None:
            realm = cell.upper()
        directory_should_exist(dest)
        directory_should_exist(os.path.join(dest, 'root.server'))
        directory_should_exist(os.path.join(dest, 'root.client'))
        directory_should_exist(os.path.join(dest, 'lib'))
        if csdb is not None:
            file_should_exist(csdb)
        self.installed = {'libs':False, 'client':False, 'server':False, 'ws':False}
        self.dest = dest
        self.cell = cell
        self.realm = realm
        self.force = force
        self.csdb = csdb
        if hosts is None or len(hosts) == 0:
            self.hosts = [(network_interfaces()[0], os.uname()[1])]
        else:
            self.hosts = []
            for name in hosts:
                addr = socket.gethostbyname(name) # works for quad-dot too
                self.hosts.append((addr, name))

    def _ignore_symlinks(self, path, names):
        ignore = []
        for name in names:
            if os.path.islink(os.path.join(path, name)):
                ignore.append(name)
        return ignore

    def _copy_files(self, src, dst, symlinks=True):
        directory_should_exist(src, "Source directory '%s' does not exist!" % src)
        if self.force:
            if os.path.exists(dst):
                if not (dst.startswith("/usr/afs/") or
                        dst.startswith("/usr/afsws/") or
                        dst.startswith("/usr/vice/")):
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
            shutil.copytree(src, dst, ignore=self._ignore_symlinks)

    def _install_shared_libs(self, src, dst):
        if self.installed['libs']:
            logger.debug("Skipping shared libs install; already done.")
        else:
            self._copy_files(src, dst, symlinks=False)
            configure_dynamic_linker(dst)
            self.installed['libs'] = True

    def _install_server_rc(self):
        """Install a server init script.

        The Transarc-style distributions provide a single init script which
        optionally starts the bosserver. This is an historical relic left over
        from the pre-namei fileserver days. Instead, install a simple, separate
        init script to start and stop the bosserver.

        Does not configure the system to run the init script automatically on
        reboot.
        """
        mkdirp("/var/lock/subsys/")
        dst = "/etc/init.d/openafs-server"
        if os.path.exists(dst) and not self.force:
            raise AssertionError("Refusing to overwrite '%s'. (use --force to override)", dst)
        with open(dst, 'w') as f:
            f.write(AFS_SERVER_RC)
        os.chmod(dst, 0755)

    def _install_workstation_binaries(self):
        """Install workstation binaries from a Transarc-style distribution."""
        if self.installed['ws']:
            logger.debug("Skipping workstation files install; already done.")
        else:
            for d in ('bin', 'etc', 'include', 'man'):
                src = os.path.join(self.dest, d)
                dst = os.path.join(AFS_WS_DIR, d)
                self._copy_files(src, dst)
            self.installed['ws'] = True
        src = os.path.join(self.dest, 'lib')
        dst = os.path.join(AFS_WS_DIR, 'lib')
        self._install_shared_libs(src, dst)

    def _linux_install_client_rc(self):
        """Install a client init script on linux.

        Does not configure the system to run the init script automatically on
        reboot.
        """
        # Install the init script.
        mkdirp("/var/lock/subsys/")
        kdir = AFS_KERNEL_DIR.lstrip('/')
        src = os.path.join(self.dest, "root.client", kdir, "afs.rc")
        dst = "/etc/init.d/openafs-client"
        if os.path.exists(dst) and not self.force:
            raise AssertionError("Refusing to overwrite '%s'. (use --force to override)", dst)
        logger.info("Installing client init script from '%s' to '%s'.", src, dst)
        shutil.copy2(src, dst)
        # Install the default startup configuration.
        src = os.path.join(self.dest, "root.client", kdir, "afs.conf")
        dst = os.path.join(SYSCONFIG, "afs")
        logger.info("Writing client startup options to file '%s'.", dst)
        mkdirp(SYSCONFIG)
        shutil.copy2(src, dst)

    def _solaris_install_driver(self):
        kdir = AFS_KERNEL_DIR.lstrip('/')
        afs = "libafs64.o"
        src = os.path.join(self.dest, "root.client", kdir, "modload", afs)
        dst = _solaris_afs_driver()
        if os.path.exists(dst) and not self.force:
            raise AssertionError("Refusing to overwrite '%s'. (use --force to override)", dst)
        logger.info("Installing kernel driver from '%s' to '%s'.", src, dst)
        shutil.copy2(src, dst)

    def _solaris_install_client_rc(self):
        """Install a client init script on solaris.

        Does not configure the system to run the init script automatically on
        reboot.  Changes the init script to avoid starting the bosserver
        by default."""
        kdir = AFS_KERNEL_DIR.lstrip('/')
        src = os.path.join(self.dest, "root.client", kdir, "modload", "afs.rc")
        dst = "/etc/init.d/openafs-client"
        if os.path.exists(dst) and not self.force:
            raise AssertionError("Refusing to overwrite '%s'. (use --force to override)", dst)
        logger.info("Installing client init script from '%s' to '%s'.", src,dst)
        with open(src, 'r') as f:
            script = f.read()
        with open(dst, 'w') as f:
            for line in script.splitlines():
                line = line.replace(
                    'if [ -x /usr/afs/bin/bosserver ]; then',
                    'if [ "${AFS_SERVER}" = "on" -a -x /usr/afs/bin/bosserver ]; then')
                line = line.replace(
                    'if [ "${bosrunning}" != "" ]; then',
                    'if [ "${AFS_SERVER}" = "on" -a "${bosrunning}" != "" ]; then')
                f.write(line)
                f.write("\n")
        os.chmod(dst, 0755)
        # Setup afsd options.
        CONFIG = "/usr/vice/etc/config"
        AFSDOPT = os.path.join(CONFIG, "afsd.options")
        mkdirp(CONFIG)
        with open(AFSDOPT, 'w') as f:
            f.write("-dynroot -fakestat")

    def _set_cell_config(self, path, ext=""):
        """Write a default CellServDB and ThisCell file."""
        # The bosserver creates symlinks for the client side configuration. Be
        # sure to remove the symlinks so we do not clobber the server
        # configuration.
        mkdirp(path)
        cellservdb = os.path.join(path, "CellServDB%s" % (ext))
        if os.path.islink(cellservdb):
            os.remove(cellservdb)
        with open(cellservdb, 'w') as f:
            f.write(">%s    #Cell name\n" % (self.cell))
            for addr,name in self.hosts:
                f.write("%s         #%s\n"  % (addr,name))
        thiscell = os.path.join(path, "ThisCell")
        if os.path.islink(thiscell):
            os.remove(thiscell)
        with open(thiscell, 'w') as f:
            f.write(self.cell)

    def _set_cache_info(self, path, root, cache, size):
        """Create the cacheinfo file."""
        dst = os.path.join(path, 'cacheinfo')
        with open(dst, 'w') as f:
            f.write("%s:%s:%d\n" % (root, cache, size))

    def install_server(self):
        """Install server binaries."""
        for path in ["/vicepa", "/vicepb"]:
            if not os.path.exists(path):
                logger.info("Making vice partition '%s'.", path)
                os.mkdir(path)
                touch(os.path.join(path, "AlwaysAttach"))
        src = os.path.join(self.dest, "root.server", AFS_SRV_BIN_DIR.lstrip('/'))
        self._copy_files(src, AFS_SRV_BIN_DIR)
        self._install_shared_libs(os.path.join(self.dest, 'lib'), AFS_SRV_LIB_DIR)
        # rxdebug is in the ws directory; be sure to install one on the server.
        self._install_workstation_binaries()
        self._set_cell_config(AFS_CONF_DIR)
        if self.cell != self.realm.lower():
            with open(os.path.join(AFS_CONF_DIR, "krb.conf"), 'w') as f:
                f.write("%s\n" % (self.realm))
        os.chmod(AFS_CONF_DIR, 0755)  # Make the bosserver happy.
        self._install_server_rc()
        self.installed['server'] = True
        logger.info("Servers installed.")

    def install_client(self):
        """Install client binaries."""
        kdir = AFS_KERNEL_DIR.lstrip('/')
        uname = os.uname()[0]
        src = os.path.join(self.dest, "root.client", kdir)
        self._copy_files(src, AFS_KERNEL_DIR)
        self._install_workstation_binaries() # including libs, unless already installed
        # Create the CellServDB and ThisCell files. Remove any symlinks that
        # my have been created by the bosserver. Combine the optional CellServDB.dist
        # to access other cells.
        csdb = os.path.join(AFS_DATA_DIR, "CellServDB")
        local = os.path.join(AFS_DATA_DIR, "CellServDB.local")
        dist = os.path.join(AFS_DATA_DIR, "CellServDB.dist")
        self._set_cell_config(AFS_DATA_DIR, ext=".local")
        if self.csdb:
            shutil.copyfile(self.csdb, dist)
        else:
            touch(dist)
        cat([local, dist], csdb)
        # Create the required directories, if not already present.
        mkdirp(AFS_MOUNT_DIR)
        mkdirp(AFS_CACHE_DIR)
        # The cachesize will be updated by the init script by default.
        # (At least on linux)
        self._set_cache_info(AFS_DATA_DIR, AFS_MOUNT_DIR, AFS_CACHE_DIR, 102400)
        if uname == "Linux":
            self._linux_install_client_rc()
        elif uname == "SunOS":
            self._solaris_install_driver()
            self._solaris_install_client_rc()
        else:
            raise AssertionError("Unsupported operating system: %s" % (uname))
        self.installed['client'] = True
        logger.info("Client installed.")

class TransarcUninstaller(object):
    """Remove a Transarc-style distribution of OpenAFS."""
    def __init__(self, purge=False, **kwargs):
        self.purge = purge
        self.verbose = kwargs.get('verbose', False)

    def _remove_file(self, path):
        if os.path.exists(path):
            logger.info("Removing %s", path)
            os.remove(path)

    def _remove_files(self, path, quiet=False):
        if not os.path.exists(path):
            return
        if not (path.startswith("/usr/afs/") or
                path.startswith("/usr/afsws/") or
                path.startswith("/usr/vice/")):
            raise AssertionError("Refusing to remove unrecognized directory %s" % (path))
        if not quiet:
            logger.info("Removing %s", path)
        shutil.rmtree(path)

    def _purge_volumes(self, path):
        logger.info("Purging volume data in '%s'.", path)
        afsidat = os.path.join(path, 'AFSIDat')
        if os.path.exists(afsidat):
            shutil.rmtree(afsidat)
        for vol in glob.glob(os.path.join(path, "*.vol")):
            os.remove(vol)

    def _purge_cache(self):
        if os.path.exists("/usr/vice/cache"):
            self._remove_file("/usr/vice/cache/CacheItems")
            self._remove_file("/usr/vice/cache/CellItems")
            self._remove_file("/usr/vice/cache/VolumeItems")
            logger.info("Removing /usr/vice/cache/D* files.")
            for d in os.listdir("/usr/vice/cache"):
                if re.match(r'^D\d+$', d):
                    self._remove_files("/usr/vice/cache/%s" % (d), quiet=(not self.verbose))

    def remove_server(self):
        if is_running('bosserver'):
            raise AssertionError("Refusing to remove: bosserver is running.")
        self._remove_files("/usr/afs/bin/")
        self._remove_files("/usr/afs/lib/")
        self._remove_file("/etc/init.d/openafs-server")
        if self.purge:
            self._remove_files("/usr/afs/")
            for part in glob.glob('/vicep*'):
                if re.match(r'/vicep([a-z]|[a-h][a-z]|i[a-v])$', part):
                    self._purge_volumes(part)

    def remove_client(self):
        uname = os.uname()[0]
        if is_running('afsd'):
            raise AssertionError("Refusing to remove: afsd is running.")
        if is_loaded('libafs'):
            raise AssertionError("Refusing to remove: libafs is loaded.")
        # is /afs mounted?
        self._remove_files("/usr/vice/etc/")
        self._remove_files("/usr/afsws/")
        self._remove_file("/etc/init.d/openafs-client")
        self._remove_file("/etc/sysconfig/afs")
        if uname == "SunOS":
            self._remove_file(_solaris_afs_driver())
        if self.purge:
            self._purge_cache()

