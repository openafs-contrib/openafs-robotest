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

"""Helper to build OpenAFS for development and testing."""

import logging
import os
import sys
import re
import shlex
import platform

from afsutil.system import sh, CommandFailed, file_should_exist
import afsutil.service

logger = logging.getLogger(__name__)

DEFAULT_CF = [
    '--enable-debug',
    '--enable-debug-kernel',
    '--disable-optimize',
    '--disable-optimize-kernel',
    '--without-dot',
]

def _sanity_check_dir():
    msg = "Missing '%s'; are you in the OpenAFS source top-level directory?"
    for d in ('src', 'src/afs', 'src/viced'):
        if not os.path.isdir(d):
            raise AssertionError(msg % (d))

def _allow_git_clean():
    clean = False
    try:
        output = sh('git', 'config', '--bool', '--get', 'afsutil.clean', output=True)
        if output[0] == 'true':
            clean = True
    except CommandFailed as e:
        if e.code == 1:
            logger.info("To enable git clean before builds:")
            logger.info("    git config --local afsutil.clean true");
        else:
            raise e
    return clean

def _clean():
    if os.path.isdir('.git'):
        if _allow_git_clean():
            sh('git', 'clean', '-f', '-d', '-x', '-q')
    else:
        if os.path.isfile('./Makefile'):
            sh('make', 'clean')

def _make_srpm(jobs=1):
    # Get the filename of the generated source rpm from the output of the
    # script. The source rpm filename is needed to build the rpms.
    output = sh('make', '-j', jobs, 'srpm', output=True)
    for line in output:
        if line.startswith('SRPM is '):
            return line.split()[2]
    raise CommandFailed(['make', '-j', jobs, 'srpm'], 1, '', 'Failed to get the srpm filename.')

def _make_rpm(srpm):
    # These commands should probably be moved to the OpenAFS Makefile.
    # Note: The spec file does not support parallel builds (make -j) yet.
    cwd = os.getcwd()
    arch = os.uname()[4]
    # Build kmod packages.
    packages = sh('rpm', '-q', '-a', 'kernel-devel', output=True)
    for package in packages:
        kernvers = package.lstrip('kernel-devel-')
        logger.info("Building kmod rpm for kernel version %s." % (kernvers))
        sh('rpmbuild',
            '--rebuild',
            '-ba',
            '--target=%s' % (arch),
            '--define', '_topdir %s/packages/rpmbuild' % (cwd),
            '--define', 'build_userspace 0',
            '--define', 'build_modules 1',
            '--define', 'kernvers %s' % (kernvers),
            'packages/%s' % (srpm))
    # Build userspace packages.
    logger.info("Building userspace rpms.")
    sh('rpmbuild',
        '--rebuild',
        '-ba',
        '--target=%s' % (arch),
        '--define', '_topdir %s/packages/rpmbuild' % (cwd),
        '--define', 'build_userspace 1',
        '--define', 'build_modules 0',
        'packages/%s' % (srpm))
    logger.info("Packages written to %s/packages/rpmbuild/RPMS/%s" % (cwd, arch))

def _debian_getdeps():
    sh('sudo', '-n', 'apt-get', '-y', 'build-dep', 'openafs')
    sh('sudo', '-n', 'apt-get', '-y', 'install', 'linux-headers-%s' % platform.release())

def _centos_getdeps():
    sh('sudo', '-n', 'yum', 'install', '-y',
       'gcc',
       'autoconf',
       'automake',
       'libtool',
       'make',
       'flex',
       'bison',
       'glibc-devel',
       'krb5-devel',
       'perl-devel',
       'ncurses-devel',
       'pam-devel',
       'fuse-devel',
       'kernel-devel-%s' % platform.release(),
       'perl-devel',
       'perl-ExtUtils-Embed',
       'wget',
       'rpm-build',
       'redhat-rpm-config')

def _fedora_getdeps():
    rel = platform.dist()[1]
    if rel >= 22:
        package_manager = 'dnf'
    else:
        package_manager = 'yum'
    sh('sudo', '-n', package_manager, 'install', '-y',
       'gcc',
       'autoconf',
       'automake',
       'libtool',
       'make',
       'flex',
       'bison',
       'glibc-devel',
       'krb5-devel',
       'perl-devel',
       'ncurses-devel',
       'pam-devel',
       'fuse-devel',
       'kernel-devel-%s' % platform.release(),
       'perl-devel',
       'perl-ExtUtils-Embed',
       'wget',
       'rpm-build',
       'redhat-rpm-config')

def getdeps(**kwargs):
    """Install build dependencies for this platform."""
    system = platform.system()
    if system == 'Linux':
        dist = platform.dist()[0]
        if dist == 'debian':
            _debian_getdeps()
        elif dist == 'centos':
            _centos_getdeps()
        elif dist == 'fedora':
            _fedora_getdeps()
        else:
            raise AssertionError("Unsupported dist: %s" % (dist))
    elif system == 'SunOS':
        raise NotImplementedError()
    else:
        raise AssertionError("Unsupported operating system: %s" % (system))

def build(**kwargs):
    """Build the OpenAFS binaries.

    Build the transarc-path compatible bins by default, which are
    deprecated, but old habits die hard.
    """
    sysname = os.uname()[0]
    cf = kwargs.get('cf', None)
    target = kwargs.get('target', 'all')
    clean = kwargs.get('clean', True)
    transarc_paths = kwargs.get('transarc_paths', True)
    modern_kmod_name = kwargs.get('modern_kmod_name', True)
    jobs = kwargs.get('jobs', 1)

    if cf is not None:
        cf = shlex.split(cf)  # Note: shlex handles quoting properly.
    else:
        cf = DEFAULT_CF
        if sysname == "Linux":
            if not '--disable-checking' in cf:
                cf.append('--enable-checking')
            if modern_kmod_name:
                cf.append('--enable-linux-kernel-packaging')
        if transarc_paths and not '--enable-transarc-paths' in cf:
            cf.append('--enable-transarc-paths')

    # Sadly, the top-level target depends on the mode we are
    # building.
    if target == 'all' and '--enable-transarc-paths' in cf:
        target = 'dest'

    _sanity_check_dir()
    if clean:
        _clean()
    sh('./regen.sh')
    sh('./configure', *cf)
    _make(jobs, target)

def _linux_kernel_packaging():
    """Returns true if built with --with-linux-kernel-packaging."""
    value = False
    with open('src/config/Makefile.config', 'r') as f:
        for line in f.readlines():
            m = re.search(r'^LINUX_KERNEL_PACKAGING = (\S+)', line)
            if m:
                value = (m.group(1) == 'yes')
                break
    return value

def _linux_libafs_name():
    """Get the libafs filename."""
    sysname, nodename, release, version, machine = os.uname()
    if _linux_kernel_packaging():
        libafs = 'openafs.ko'
    else:
        mp = '.mp' if 'SMP' in version else ''
        libafs = "libafs-%s%s.ko" % (release, mp)
    return libafs

def _linux_modload_name():
    """Get the modload directory name."""
    sysname, nodename, release, version, machine = os.uname()
    if _linux_kernel_packaging():
        modload = "MODLOAD-%s-SP" % (release)
    else:
        mp = 'MP' if 'SMP' in version else 'SP'
        modload = "MODLOAD-%s-%s" % (release, mp)
    return modload

def _kmod():
    """Get the kernel module file name in the build tree."""
    sysname = os.uname()[0]
    if sysname == 'Linux':
        libafs = _linux_libafs_name()
        modload = _linux_modload_name()
        kmod = os.path.abspath("src/libafs/%s/%s" % (modload, libafs))
    elif sysname == 'SunOS':
        kmod = os.path.abspath("src/libafs/MODLOAD64/libafs.o")
    else:
        raise AssertionError("Unsupported operating system: %s" % (sysname))
    return kmod

def _client_setup():
    """Get the client setup object for this os."""
    uname = os.uname()[0]
    if uname == "Linux":
        cs = afsutil.transarc.LinuxClientSetup()
    elif uname == "SunOS":
        cs = afsutil.transarc.SolarisClientSetup()
    else:
        raise AssertionError("Unsupported operating system: %s" % (uname))
    return cs

def _make(jobs, target):
    uname = os.uname()[0]
    if uname == "Linux":
        sh('make', '-j', jobs, target)
    elif uname == "SunOS":
        sh('make', target)
    else:
        raise AssertionError("Unsupported operating system: %s" % (uname))

def modreload(**kwargs):
    """Reload the kernel module and restart the cache manager after a build.

    This is a helper for testing and debugging the afs kernel module and afsd
    without resorting to a full reinstallation after every code change. The cache
    manager must be installed at least once, then can be reloaded after each code
    change and build with this function.

    This should be run as root in the top level source directory. At this time,
    only transarc-style installations are supported by modreload.

    A typical workflow, using the afsutil front-end script:

        $ sudo afsutil install --dist transarc [options]
        $ sudo afsutil start client
        ... test/debug/etc ...
        ... edit files in src/afs ...

        $ make libafs
        $ sudo afsutil reload
        ... test/debug/etc ...
        ... edit files in src/afs ...

        $ make libafs
        $ sudo afsutil reload
        ... repeat ...
    """
    _sanity_check_dir() # Run this in the top level source directory.
    cs = _client_setup()
    afsd = os.path.abspath('src/afsd/afsd')
    kmod = _kmod()
    file_should_exist(afsd)        # Check before stopping.
    file_should_exist(kmod)
    afsutil.service.stop(components=['client'])
    cs.install_afsd(afsd)
    cs.install_kmod(kmod)
    afsutil.service.start(components=['client'])

def package(**kwargs):
    """Build the OpenAFS rpm packages."""
    # The rpm spec file contains the configure options for the actual build.
    # We run configure here just to bootstrap the process.
    clean = kwargs.get('clean', True)
    package = kwargs.get('package', None)
    jobs = kwargs.get('jobs', 1)
    if clean:
        _clean()
    sh('./regen.sh', '-q')
    sh('./configure')
    sh('make', '-j', jobs, 'dist')
    srpm = _make_srpm(jobs)
    _make_rpm(srpm)


#
# Test driver.
#
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) < 2:
        sys.stderr.write("usage: python build.py build\n")
        sys.stderr.write("       python build.py package\n")
        sys.stderr.write("       python build.py modreload\n")
        sys.exit(1)
    if sys.argv[1] == 'build':
        build()
    elif sys.argv[1] == 'package':
        package()
    else:
        if os.geteuid() != 0:
            sys.stderr.write("Must run as root!\n")
            sys.exit(1)
        modreload()
