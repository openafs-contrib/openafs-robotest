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
import shlex
from afsutil.system import sh, CommandFailed, \
                           is_afs_mounted, afs_umount, \
                           unload_module, load_module

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

def build(**kwargs):
    """Build the OpenAFS binaries.

    Build the transarc-path compatible bins by default, which are
    deprecated, but old habits die hard.
    """
    cf = kwargs.get('cf', None)
    target = kwargs.get('target', 'all')
    clean = kwargs.get('clean', True)
    transarc = kwargs.get('transarc', True)
    jobs = kwargs.get('jobs', 1)

    if cf is not None:
        cf = shlex.split(cf)  # Note: shlex handles quoting properly.
    else:
        cf = DEFAULT_CF
        if os.uname()[0] == "Linux" and not '--disable-checking' in cf:
            cf.append('--enable-checking')
        if transarc and not '--enable-transarc-paths' in cf:
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
    sh('make', '-j', jobs, target)

def _kmod():
    uname = os.uname()[0]
    kernel = os.uname()[2]
    if uname == 'Linux':
        kmod = os.path.abspath("./src/libafs/MODLOAD-%s-MP/libafs-%s.mp.ko" % (kernel, kernel))
    elif uname == 'SunOS':
        kmod = os.path.abspath("./src/libafs/MODLOAD64/libafs.o")
    else:
        raise AssertionError("Unsuppored platform: %s" % (uname))
    return kmod

def modreload(**kwargs):
    """Reload the kernel module and restart the cache manager after a build.
    Should be run as root in the top level directory."""

    _sanity_check_dir() # Run this in the top level source directory.
    afsd = os.path.abspath("./src/afsd/afsd")
    kmod = _kmod()
    for f in (afsd, kmod):
        if not os.path.exists(f):
            raise AssertionError("File not found: %s" % (f))
    if is_afs_mounted():
        for rc in ("/etc/init.d/openafs-client", "/etc/init.d/afs"):
            if os.path.isfile(rc):
                sh(rc, 'stop')
                break
    if is_afs_mounted():
        try:
            sh(afsd, '-shutdown')  # may return non-zero!
        except CommandFailed:
            pass
        afs_umount()
    if is_afs_mounted():
        logger.error("Unable to umount afs.")
        return 1
    unload_module()

    logger.info("Loading kernel module: %s" % (kmod))
    load_module(kmod)
    logger.info("Starting the cache manager.")
    sh(afsd, '-dynroot', '-fakestat', '-afsdb')  # xxx: how to set these?

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
