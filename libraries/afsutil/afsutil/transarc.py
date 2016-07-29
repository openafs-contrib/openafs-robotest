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

from afsutil.install import Installer, \
                            copy_files, remove_file, remove_files

from afsutil.system import sh, directory_should_exist, \
                           configure_dynamic_linker, \
                           is_loaded, is_running, mkdirp \

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

BOSSERVER_OPTIONS=""
SYSCNF=${SYSCNF:-/etc/sysconfig/openafs-server}
if [ -f $SYSCNF ] ; then
    . $SYSCNF
fi

BOS=${BOS:-/usr/afs/bin/bos}
BOSSERVER=${BOSSERVER:-/usr/afs/bin/bosserver}

start() {
    if [ ! "$afs_rh" -o ! -f /var/lock/subsys/openafs-server ]; then
        if test -x $BOSSERVER ; then
            echo "Starting AFS servers..... "
            $BOSSERVER $BOSSERVER_OPTIONS
            test "$afs_rh" && touch /var/lock/subsys/openafs-server
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
    if [ ! "$afs_rh" -o -f /var/lock/subsys/openafs-server ]; then
        if  test -x $BOS ; then
            echo "Stopping AFS servers..... "
            $BOS shutdown localhost -localauth -wait
            pkill -HUP bosserver
        fi
        rm -f /var/lock/subsys/openafs-server
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

class LinuxClientSetup(object):
    """Linux specific setup functions."""

    def install_init_script(self, dest, force=False):
        """Install a client init script on linux.

        Does not configure the system to run the init script automatically on
        reboot.
        """
        # Install the init script.
        mkdirp("/var/lock/subsys/")
        src = pkg_resources.resource_filename('afsutil', 'data/openafs-client-linux.init')
        dst = "/etc/init.d/openafs-client"
        if os.path.exists(dst) and not force:
            raise AssertionError("Refusing to overwrite '%s'.", dst)
        logger.info("Installing client init script from '%s' to '%s'.", src, dst)
        shutil.copy2(src, dst)
        os.chmod(dst, 0755)
        # Install the default startup configuration.
        kdir = AFS_KERNEL_DIR.lstrip('/')
        src = os.path.join(dest, "root.client", kdir, "afs.conf")
        dst = os.path.join(SYSCONFIG, "afs")
        logger.info("Writing client startup options to file '%s'.", dst)
        mkdirp(SYSCONFIG)
        shutil.copy2(src, dst)

    def install_driver(self, dest, force=False):
        # If available, install the openafs.ko to a path loadable by modprobe.
        # Use the openafs configure option --with-linux-kernel-packaging to build
        # openafs.ko instead of libafs-....ko
        release = os.uname()[2]
        src = os.path.join(dest, "root.client", "lib/modules/%s/extra/openafs/openafs.ko" % (release))
        dst = "/lib/modules/%s/extra/openafs/openafs.ko" % (release)
        if os.path.exists(src):
            mkdirp(os.path.dirname(dst))
            logger.info("Installing kernel module from '%s' to '%s'.", src, dst)
            shutil.copy2(src, dst)
            sh('/sbin/depmod', '-a')

    def remove_driver(self):
        release = os.uname()[2]
        src = "/lib/modules/%s/extra/openafs/openafs.ko" % (release)
        if os.path.exists(src):
            remove_file(src)

class SolarisClientSetup(object):
    """Solaris specific setup functions."""

    def _afs_driver(self):
        """Return the name of the afs driver for the current platform."""
        output = sh('/bin/isalist', output=True)[0]
        if 'amd64' in output:
            driver = '/kernel/drv/amd64/afs'
        elif 'sparcv9' in output:
            driver = '/kernel/drv/sparcv9/afs'
        else:
            driver = '/kernel/drv/afs'
        return driver

    def install_driver(self, dest, force=False):
        kdir = AFS_KERNEL_DIR.lstrip('/')
        afs = "libafs64.o"
        src = os.path.join(dest, "root.client", kdir, "modload", afs)
        dst = self._afs_driver()
        if os.path.exists(dst) and not force:
            raise AssertionError("Refusing to overwrite '%s'.", dst)
        logger.info("Installing kernel driver from '%s' to '%s'.", src, dst)
        shutil.copy2(src, dst)

    def remove_driver(self):
        remove_file(self._afs_driver())

    def install_init_script(self, dest, force=False):
        """Install a client init script on solaris.

        Does not configure the system to run the init script automatically on
        reboot.  Changes the init script to avoid starting the bosserver
        by default."""
        src = pkg_resources.resource_filename('afsutil', 'data/openafs-client-solaris.init')
        dst = "/etc/init.d/openafs-client"
        if os.path.exists(dst) and not force:
            raise AssertionError("Refusing to overwrite '%s'.", dst)
        logger.info("Installing client init script from '%s' to '%s'.", src,dst)
        shutil.copy2(src, dst)
        os.chmod(dst, 0755)
        # Setup afsd options.
        CONFIG = "/usr/vice/etc/config"
        AFSDOPT = os.path.join(CONFIG, "afsd.options")
        mkdirp(CONFIG)
        with open(AFSDOPT, 'w') as f:
            f.write("-dynroot -fakestat")

class TransarcInstaller(Installer):
    """Install a Transarc-style distribution of OpenAFS on linux or solaris."""

    def __init__(self, dir=None, **kwargs):
        """Initialize the Transarc-style installer.

        dest: path to the 'dest' directory created by previous make dest
              If None, try to detect the sysname and find the dest directory
              in the current working directory.
        """
        Installer.__init__(self, **kwargs)
        self.dest = dir # defer detection/checks until install().
        uname = os.uname()[0]
        if uname == "Linux":
            self.client_setup = LinuxClientSetup()
        elif uname == "SunOS":
            self.client_setup = SolarisClientSetup()
        else:
            raise AssertionError("Unsupported operating system: %s" % (uname))
        self.installed = {'libs':False, 'client':False, 'server':False, 'ws':False}

    def _detect_sysname(self):
        """Try to detect the sysname from the previous build output."""
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

    def _detect_dest(self):
        """Try to detect the dest directory from the previous build.
        This is used to install bins after building binaries."""
        dest = None
        sysname = self._detect_sysname()
        if sysname:
            dest = "%s/dest" % (sysname)
        else:
            raise ValueError("Unable to find dest directory.")
        return dest

    def _check_dest(self, dest):
        """Verify the dest directory looks sane."""
        directory_should_exist(dest)
        directory_should_exist(os.path.join(dest, 'root.server'))
        directory_should_exist(os.path.join(dest, 'root.client'))
        directory_should_exist(os.path.join(dest, 'lib'))

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
        mkdirp("/var/lock/subsys/")
        dst = "/etc/init.d/openafs-server"
        if os.path.exists(dst) and not self.force:
            raise AssertionError("Refusing to overwrite '%s'.", dst)
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
                copy_files(src, dst, force=self.force)
            self.installed['ws'] = True
        src = os.path.join(self.dest, 'lib')
        dst = os.path.join(AFS_WS_DIR, 'lib')
        self._install_shared_libs(src, dst)

    def _install_server(self):
        """Install server binaries."""
        logger.info("Installing server binaries")
        src = os.path.join(self.dest, "root.server", AFS_SRV_BIN_DIR.lstrip('/'))
        copy_files(src, AFS_SRV_BIN_DIR, force=self.force)
        self._install_shared_libs(os.path.join(self.dest, 'lib'), AFS_SRV_LIB_DIR)
        self._install_workstation_binaries() # rxdebug is in the ws directory.
        self._install_server_rc()
        self.installed['server'] = True
        logger.info("Servers installed.")

    def _install_client(self):
        """Install client binaries."""
        logger.info("Installing client binaries")
        kdir = AFS_KERNEL_DIR.lstrip('/')
        src = os.path.join(self.dest, "root.client", kdir)
        copy_files(src, AFS_KERNEL_DIR, force=self.force)
        self._install_workstation_binaries() # including libs, unless already installed
        self.client_setup.install_driver(self.dest, force=self.force)
        self.client_setup.install_init_script(self.dest, force=self.force)
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
        """Install Transarc-style distribution OpenAFS binaries."""
        # Verify we have the dest directory before starting.
        if self.dest is None:
            self.dest = self._detect_dest()
        self._check_dest(self.dest)
        self.pre_install()
        if self.do_server:
            self._install_server()
        if self.do_client:
            self._install_client()
        self.post_install()

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

def main():
    if len(sys.argv) != 2:
        sys.stderr.write("usage: python transarc.py <dest>\n")
        sys.exit(1)
    if os.geteuid() != 0:
        sys.stderr.write("Must run as root!\n")
        sys.exit(1)
    t = _Test(sys.argv[1])
    t.test()

if __name__ == '__main__':
    main()

