# Copyright (c) 2014-2016 Sine Nomine Associates
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
import shutil
import glob
import pkg_resources
import tempfile
import urllib2

from afsutil.install import Installer, \
                            copy_files, remove_file, remove_files

from afsutil.system import sh, directory_should_exist, \
                           configure_dynamic_linker, \
                           is_loaded, is_running, mkdirp, path_join, \
                           untar

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

class TransarcClientSetup(object):
    """Transarc client specific setup functions."""

    def install_afsd(self, afsd):
        """Install the afsd file."""
        # Common for linux an solaris.
        src = afsd
        dst = AFS_KERNEL_DIR
        logger.info("Installing afsd from '%s' to '%s'.", src, dst)
        mkdirp(dst)
        shutil.copy2(src, dst)
        os.chmod(dst, 0755)

class LinuxClientSetup(TransarcClientSetup):
    """Linux specific setup functions."""

    def install_init_script(self, dest, afsd_options):
        """Install a client init script on linux.

        Does not configure the system to run the init script automatically on
        reboot.
        """
        # Install the init script.
        mkdirp("/var/lock/subsys/")
        src = pkg_resources.resource_filename('afsutil', 'data/openafs-client-linux.init')
        dst = "/etc/init.d/openafs-client"
        logger.info("Installing client init script from '%s' to '%s'.", src, dst)
        shutil.copy2(src, dst)
        os.chmod(dst, 0755)
        # Set afsd options.
        dst = path_join(SYSCONFIG, "openafs-client")
        logger.info("Writing afsd startup options to file '%s'." % (dst))
        mkdirp(os.path.dirname(dst))
        with open(dst, 'w') as f:
            f.write('AFSD_OPTIONS="%s"\n' % (afsd_options))

    def _install_openafs_ko(self, kmod):
        """Install the openafs.ko file and run depmod."""
        release = os.uname()[2]
        src = kmod
        dst = path_join("/lib/modules", release, "extra/openafs/openafs.ko")
        logger.info("Installing kernel module from '%s' to '%s'.", src, dst)
        mkdirp(os.path.dirname(dst))
        shutil.copy2(src, dst)
        sh('/sbin/depmod', '-a')

    def install_driver(self, dest, force=False):
        #
        # If available, install the openafs.ko to a path loadable by modprobe.
        # Use the openafs configure option --with-linux-kernel-packaging to build
        # openafs.ko instead of libafs${version}.ko
        #
        # Note: libafs${version}.ko was already installed by copying all the files from
        #       dest/root.client/usr/vice/etc to /usr/vice/etc.
        #
        release = os.uname()[2]
        kmod = path_join(dest, "root.client", "lib/modules", release, "extra/openafs/openafs.ko")
        if os.path.exists(kmod):
            self._install_openafs_ko(kmod)

    def remove_driver(self):
        release = os.uname()[2]
        src = path_join("/lib/modules", release, "extra/openafs/openafs.ko")
        if os.path.exists(src):
            remove_file(src)

    def install_kmod(self, kmod):
        """Install the kernel module by filename."""
        if os.path.basename(kmod) == 'openafs.ko':
            self._install_openafs_ko(kmod)
        elif os.path.basename(kmod).startswith('libafs'):
            src = kmod
            dst = path_join(AFS_KERNEL_DIR, 'modload')
            logger.info("Installing kernel module from '%s' to '%s'.", src, dst)
            shutil.copy2(src, dst)
        else:
            raise ValueError("Unknown kernel module name: %s" % (kmod))

class SolarisClientSetup(TransarcClientSetup):
    """Solaris specific setup functions."""

    def install_init_script(self, dest, afsd_options):
        """Install a client init script on solaris.

        Does not configure the system to run the init script automatically on
        reboot.  Changes the init script to avoid starting the bosserver
        by default."""
        osrel = os.uname()[2]
        src = pkg_resources.resource_filename('afsutil', 'data/openafs-client-solaris-%s.init' % (osrel))
        dst = "/etc/init.d/openafs-client"
        logger.info("Installing client init script from '%s' to '%s'.", src,dst)
        shutil.copy2(src, dst)
        os.chmod(dst, 0755)
        # Set afsd options.
        config = '/usr/vice/etc/config'
        dst = path_join(config, 'afsd.options')
        logger.info("Writing afsd startup options to file '%s'." % (dst))
        mkdirp(os.path.dirname(dst))
        with open(dst, 'w') as f:
            f.write(afsd_options) # Not sourced.

    def _afs_driver(self):
        """Return the name of the afs driver for the current platform."""
        osrel = os.uname()[2]
        if osrel == '5.10':
            return self._afs_driver_510()
        elif osrel == '5.11':
            return self._afs_driver_511()
        else:
            raise AssertionError("Unsupported operating system: %s" % (osrel))

    def _afs_driver_510(self):
        output = sh('/bin/isalist')[0]
        if 'amd64' in output:
            driver = '/kernel/fs/amd64/afs'
        elif 'sparcv9' in output:
            driver = '/kernel/fs/sparcv9/afs'
        else:
            driver = '/kernel/fs/afs'
        return driver

    def _afs_driver_511(self):
        output = sh('/bin/isalist')[0]
        if 'amd64' in output:
            driver = '/kernel/drv/amd64/afs'
        elif 'sparcv9' in output:
            driver = '/kernel/drv/sparcv9/afs'
        else:
            driver = '/kernel/drv/afs'
        return driver

    def install_driver(self, dest):
        afs = "libafs64.o"
        kmod = path_join(dest, "root.client", AFS_KERNEL_DIR, "modload", afs)
        self.install_kmod(kmod)

    def remove_driver(self):
        remove_file(self._afs_driver())
        remove_file('/kernel/drv/afs.conf')

    def install_kmod(self, kmod):
        """Install the kernel module by filename."""
        src = kmod
        dst = self._afs_driver()
        logger.info("Installing kernel driver from '%s' to '%s'.", src, dst)
        shutil.copy2(src, dst)

class TransarcInstaller(Installer):
    """Install a Transarc-style distribution of OpenAFS on linux or solaris."""

    def __init__(self, **kwargs):
        """Initialize the Transarc-style installer.

        """
        Installer.__init__(self, **kwargs)
        self.bins = kwargs.get('dir', None)
        self.tmpfile = None
        self.tmpdir = None
        self.url = None
        self.tarball = None
        self.dest = None
        uname = os.uname()[0]
        if uname == "Linux":
            self.client_setup = LinuxClientSetup()
        elif uname == "SunOS":
            self.client_setup = SolarisClientSetup()
        else:
            raise AssertionError("Unsupported operating system: %s" % (uname))
        self.installed = {'libs':False, 'client':False, 'server':False, 'ws':False}

    def _detect_dest(self):
        user = os.getenv('SUDO_USER') # The user who invoked sudo.
        patterns = ["./*/dest"]
        if user:
            patterns.append("/home/{user}/openafs/*/dest".format(**locals()))
            patterns.append("/home/{user}/src/openafs/*/dest".format(**locals()))
        for pattern in patterns:
            logger.debug("Searching for dest in '%s'", pattern)
            paths = glob.glob(pattern)
            if len(paths) > 1:
                raise AssertionError("Unable to find dest directory: too many sysnames in '%s'!" % (pattern))
            if len(paths) == 1:
                path = os.path.abspath(paths[0])
                logger.debug("Found dest: '%s'", path)
                return path
        raise AssertionError("Unable to find dest directory.")

    def _check_dest(self, dest):
        """Verify the dest directory looks sane."""
        directory_should_exist(dest)
        directory_should_exist(path_join(dest, 'root.server'))
        directory_should_exist(path_join(dest, 'root.client'))
        directory_should_exist(path_join(dest, 'lib'))

    def _install_shared_libs(self, src, dst):
        """Install the shared libraries."""
        if self.installed['libs']:
            logger.debug("Skipping shared libs install; already done.")
        else:
            copy_files(src, dst, symlinks=False, force=self.force)
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
        src = pkg_resources.resource_filename('afsutil', 'data/openafs-server.init')
        dst = "/etc/init.d/openafs-server"
        if os.path.exists(dst) and not self.force:
            raise AssertionError("Refusing to overwrite '%s'.", dst)
        shutil.copy2(src, dst)
        os.chmod(dst, 0755)
        mkdirp("/var/lock/subsys/")  # needed by the init script
        # Set the bosserver command line options.
        dst = path_join(SYSCONFIG, "openafs-server")
        logger.info("Writing bosserver startup options to file '%s'." % (dst))
        mkdirp(os.path.dirname(dst))
        with open(dst, 'w') as f:
            f.write('BOSSERVER_OPTIONS="%s"\n' % (self.options.get('bosserver', '')))

    def _install_workstation_binaries(self):
        """Install workstation binaries from a Transarc-style distribution."""
        if self.installed['ws']:
            logger.debug("Skipping workstation files install; already done.")
        else:
            for d in ('bin', 'etc', 'include', 'man'):
                src = path_join(self.dest, d)
                dst = path_join(AFS_WS_DIR, d)
                copy_files(src, dst, force=self.force)
            self.installed['ws'] = True
        src = path_join(self.dest, 'lib')
        dst = path_join(AFS_WS_DIR, 'lib')
        self._install_shared_libs(src, dst)

    def _install_server(self):
        """Install server binaries."""
        logger.info("Installing server binaries")
        src = path_join(self.dest, "root.server", AFS_SRV_BIN_DIR)
        copy_files(src, AFS_SRV_BIN_DIR, force=self.force)
        self._install_shared_libs(path_join(self.dest, 'lib'), AFS_SRV_LIB_DIR)
        self._install_workstation_binaries() # rxdebug is in the ws directory.
        self._install_server_rc()
        self.installed['server'] = True
        logger.info("Servers installed.")

    def _install_client(self):
        """Install client binaries."""
        logger.info("Installing client binaries")
        src = path_join(self.dest, "root.client", AFS_KERNEL_DIR)
        copy_files(src, AFS_KERNEL_DIR, force=self.force) # also installs libafs.ko
        self._install_workstation_binaries() # including libs, unless already installed
        self.client_setup.install_driver(self.dest)
        self.client_setup.install_init_script(self.dest, self.options.get('afsd', ''))
        mkdirp(AFS_MOUNT_DIR)
        mkdirp(AFS_CACHE_DIR)
        self.installed['client'] = True
        logger.info("Client installed.")

    def _remove_server(self):
        """Remove the server binaries."""
        if is_running('bosserver'):
            raise AssertionError("Refusing to remove: bosserver is running.")
        remove_files("/usr/afs/bin/")
        remove_files("/usr/afs/lib/")
        remove_file("/etc/init.d/openafs-server")

    def _remove_client(self):
        """Remove the client binaries."""
        if is_running('afsd'):
            raise AssertionError("Refusing to remove: afsd is running.")
        if is_loaded('libafs'):
            raise AssertionError("Refusing to remove: libafs is loaded.")
        # is /afs mounted?
        remove_files("/usr/vice/etc/")
        remove_files("/usr/afsws/")
        remove_file("/etc/init.d/openafs-client")
        remove_file("/etc/sysconfig/afs")
        self.client_setup.remove_driver()

    def install(self):
        """Install Transarc-style distribution OpenAFS binaries.

        self.bins specifies the bins to be installed.
        * None: Install the bins under <sysname>/dest in the current directory.
        * a directory path:  Install the bins found in the given dest directory.
        * a path to a tarball: Untar the tarball in a temporary directory and
          install the bins found under <sysname>/dest.
        * url path: Download the tarball file at the given url, untar the tarball,
          and install the bins found under <sysname>/dest.
        """
        def _untar(tarball):
            self.tmpdir = tempfile.mkdtemp()
            logger.info("Untarring %s into %s", self.bins, self.tmpdir)
            untar(tarball, chdir=self.tmpdir)
            return glob.glob("%s/*/dest" % (self.tmpdir))[0] # must have a dest dir.

        def _download(url):
            BLOCK_SIZE = 4 * 1024
            rsp = urllib2.urlopen(url)
            (fh, self.tmpfile) = tempfile.mkstemp(suffix='.tar.gz')
            logger.info("Downloading %s to %s", url, self.tmpfile)
            with open(self.tmpfile, 'wb') as tarball:
                block = rsp.read(BLOCK_SIZE)
                while block:
                    tarball.write(block)
                    block = rsp.read(BLOCK_SIZE)
            os.close(fh)
            return self.tmpfile

        if self.bins is None:
            self.dest = self._detect_dest()
        elif os.path.isdir(self.bins):
            self.dest = self.bins
        elif (self.bins.startswith('http://') or self.bins.startswith('https://')) and self.bins.endswith('.tar.gz'):
            self.dest = _untar(_download(self.bins))
        elif os.path.isfile(self.bins) and self.bins.endswith('.tar.gz'):
            self.dest = _untar(self.bins)
        else:
            raise AssertionError("Unrecognized path to installation files: %s" % (self.bins))
        self._check_dest(self.dest)
        self.pre_install()
        if self.do_server:
            self._install_server()
        if self.do_client:
            self._install_client()
        self.post_install()
        if self.tmpfile:
            logger.info("Removing tmp file %s", self.tmpfile)
            os.remove(self.tmpfile)
        if self.tmpdir:
            logger.info("Removing tmp dir %s", self.tmpdir)
            shutil.rmtree(self.tmpdir)

    def remove(self):
        """Remove Transarc-style distribution OpenAFS binaries."""
        self.pre_remove()
        if self.do_client:
            self._remove_client()
        if self.do_server:
            self._remove_server()
        self.post_remove()

#
# Test Driver
#
class _Test(object):
    def __init__(self, dest):
        self.dest = dest

    def test_install(self):
        i = TransarcInstaller(dest=self.dest, force=True)
        i.install()

    def test_remove(self):
        i = TransarcInstaller(dest=self.dest, purge=True)
        i.remove()

    def test_install_server(self):
        i = TransarcInstaller(dest=self.dest, force=True, components=['server'])
        i.install()

    def test_remove_server(self):
        i = TransarcInstaller(dest=self.dest, force=True, components=['server'])
        i.remove()

    def test_install_client(self):
        i = TransarcInstaller(dest=self.dest, force=True, components=['client'])
        i.install()

    def test_remove_client(self):
        i = TransarcInstaller(dest=self.dest, force=True, components=['client'])
        i.remove()

    def test(self):
        logging.basicConfig(level=logging.DEBUG)
        self.test_remove()
        self.test_install_server()
        self.test_install_client()
        self.test_remove_server() # leaves common packages
        self.test_remove_client() # removes common packages
