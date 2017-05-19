# Copyright (c) 2014-2017 Sine Nomine Associates
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
import urllib2
import tempfile
import glob

from afsutil.system import sh, CommandFailed, file_should_exist, tar
import afsutil.service

logger = logging.getLogger(__name__)

DEFAULT_CF = [
    '--enable-debug',
    '--enable-debug-kernel',
    '--disable-optimize',
    '--disable-optimize-kernel',
    '--without-dot',
]

def _detect_sysname():
    """Try to detect the sysname from the previous build output."""
    sysname = None
    if os.path.exists("src/config/Makefile.config"):
        with open("src/config/Makefile.config", "r") as f:
            for line in f.readlines():
                match = re.match(r'SYS_NAME\s*=\s*(\S+)', line)
                if match:
                    sysname = match.group(1)
                    break
    return sysname

def _sanity_check_dir():
    msg = "Missing '%s'; are you in the OpenAFS source top-level directory?"
    for d in ('src', 'src/afs', 'src/viced'):
        if not os.path.isdir(d):
            raise AssertionError(msg % (d))

def _allow_git_clean(gitdir):
    clean = False
    try:
        output = sh('git', '--git-dir', gitdir, 'config', '--bool', '--get', 'afsutil.clean', output=True)
        if output[0] == 'true':
            clean = True
    except CommandFailed as e:
        if e.code == 1:
            logger.info("To enable git clean before builds:")
            logger.info("    git config --local afsutil.clean true");
        else:
            raise e
    return clean

def _clean(srcdir):
    if not os.path.exists(srcdir):
        raise AssertionError("srcdir not found: %s" % (srcdir))
    gitdir = '%s/.git' % (srcdir)
    if os.path.isdir(gitdir):
        if _allow_git_clean(gitdir):
            sh('git', '--git-dir', gitdir, '--work-tree', srcdir, 'clean', '-f', '-d', '-x', '-q')
    else:
        if os.path.isfile('./Makefile'): # Maybe out of tree, not in srcdir.
            sh('make', 'clean')

def _detect_solariscc():
    search = [
        '/opt/developerstudio*/bin',
        '/opt/solarisstudio*/bin',
    ]
    for pattern in search:
        paths = sorted(glob.glob(pattern), reverse=True)
        if len(paths) != 0:
            return paths[0]
    return None

def _setenv_solaris():
    need = [
        '/usr/perl5/bin',   # for pod2man
    ]
    # Update the path to the solaris studio cc.
    if not 'SOLARISCC' in os.environ:
        ccpath = _detect_solariscc()
        if ccpath:
            need.append(ccpath)
            logger.info("Adding '%s' to SOLARISCC." % (ccpath))
            os.environ['SOLARISCC'] = os.path.join(ccpath, 'cc')
        else:
            logger.warning("Failed to find path to solaris cc!")
    # Update the PATH.
    paths = os.getenv('PATH', '').split(':')
    for path in need:
        if not path in paths:
            logger.info("Adding '%s' to PATH." % (path))
            paths.append(path)
    os.environ['PATH'] = ':'.join(paths)

def _setenv():
    system = platform.system()
    if system == 'SunOS':
        _setenv_solaris()

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
    sh('apt-get', '-y', 'build-dep', 'openafs')
    sh('apt-get', '-y', 'install', 'linux-headers-%s' % platform.release())
    sh('apt-get', '-y', 'install', 'libtool')

def _centos_getdeps():
    sh('yum', 'install', '-y',
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
       'perl-ExtUtils-Embed',
       'wget',
       'rpm-build',
       'redhat-rpm-config')

def _opensuse_getdeps():
    sh('zypper', 'install', '-y',
       'gcc',
       'autoconf',
       'automake',
       'libtool',
       'make',
       'flex',
       'bison',
       'glibc-devel',
       'krb5-devel',
       'ncurses-devel',
       'pam-devel',
       'fuse-devel',
       'kernel-devel',
       'wget',
       'rpm-build',
    )
    #'perl-devel',
    #'perl-ExtUtils-Embed',
    #'redhat-rpm-config',

def _fedora_getdeps():
    rel = platform.dist()[1]
    if rel >= 22:
        package_manager = 'dnf'
    else:
        package_manager = 'yum'
    sh(package_manager, 'install', '-y',
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
       'perl-ExtUtils-Embed',
       'wget',
       'rpm-build',
       'redhat-rpm-config')


def _download(baseurl, filename, path):
    url = os.path.join(baseurl, filename)
    dst = os.path.join(path, filename)
    rsp = urllib2.urlopen(url)
    logger.info("Downloading %s to %s", url, dst)
    with open(dst, 'wb') as fh:
        fh.write(rsp.read())

def _compare_versions(a, b):
    def _normalize(s):
        return [int(x) for x in s.split('.')]
    return cmp(_normalize(a), _normalize(b))

def _sol11_getdeps(**kwargs):
    """Install solaris studio and development packages.

    Before running this function, create an account on the Oracle Technology Network
    and follow the instructions to create and download the key and certificate files.
    Place the key and cert file in a local directory or at a private url.  The
    default location of the key and cert files is /root/creds. Set the 'creds'
    keyward argurment to specify a different path or a url.
    """
    creds = kwargs.get('creds', '/root/creds')
    key = kwargs.get('key', 'pkg.oracle.com.key.pem')
    cert = kwargs.get('cert', 'pkg.oracle.com.certificate.pem')
    path = None
    tmpdir = None

    try:
        if creds.startswith('http://') or creds.startswith('https://'):
            path = tmpdir = tempfile.mkdtemp()
            _download(creds, key, tmpdir)
            _download(creds, cert, tmpdir)
        elif os.path.exists(creds):
            path = creds
        else:
            raise ValueError("creds path '%s' not found." % creds)

        logger.info("Setting publisher for solarisstudio.")
        sh('pkg', 'set-publisher',   # Will refresh if already set.
       	   '-k', os.path.join(path, key),
       	   '-c', os.path.join(path, cert),
       	   '-G', '*',
           '-g', 'https://pkg.oracle.com/solarisstudio/release', 'solarisstudio')

        logger.info("Getting available solarisstudio packages.")
        output = sh('pkg', 'list', '-H', '-a', '-v', '--no-refresh', 'pkg://solarisstudio/*', output=True, quiet=True)
        packages = {}
        installed = False # alread installed?
        for line in output:
            # Extract the root package name, version, and install state.
            # Example:
            # 'pkg://solarisstudio/developer/developerstudio-125@12.5,5.11-1.0.0.0:20160614T214517Z ---'
            # name='developerstudio-125'; version='12.5'; installed=False
            fmri,ifo = line.split()
            pkg,vt = fmri.split('@')
            v,t = vt.split(':')
            version = v.split(',')[0]
            name = pkg.replace('pkg://solarisstudio/developer/','')
            istate = ifo[0] == 'i'
            if not '/' in name:
                # skip non-root ones, e.g. 'developerstudio-125/cc'
                logger.info("Found package %s, version %s, installed %s" % (name, version, istate))
                packages[name] = {'version':version, 'installed':istate}
                if istate:
                    installed = True

        if installed:
            logger.info("Skipping solarisstudio install; already installed.")
        else:
            logger.info("Determining which solarisstudio package to install.")
            pkg = None
            vers = '0.0' # Find the most recent version.
            for name in packages.keys():
                if _compare_versions(packages[name]['version'], vers) > 0:
                    vers = packages[name]['version']
                    pkg = 'pkg://solarisstudio/developer/%s' % name
            if pkg is None:
                raise AssertionError("Unable to find a solarisstudio package to install.")

            logger.info("Installing solarisstudio package '%s'." % (pkg))
            sh('pkg', 'install', '--accept', pkg)


        logger.info("Installing development packages.")
        try:
            sh('pkg', 'install',
            'autoconf',
            'automake',
            'bison',
            'flex',
            'git',
            'gnu-binutils',
            'gnu-coreutils',
            'gnu-sed',
            'libtool',
            'make',
            'onbld',
            'text/locale',
            )
        except CommandFailed as e:
            if e.code != 4:  # 4 is means installed (not an error)
                logger.error("pkg install failed: %s" % e)

    except urllib2.HTTPError as e:
        logger.error("Unable to download files from url '%s', %s'" % (creds, e))
    except ValueError as e:
        logger.error("%s" % e)
    finally:
        if tmpdir:
            logger.info("Cleaning up temp files.")
            if os.path.exists(os.path.join(tmpdir, key)):
                os.remove(os.path.join(tmpdir, key))
            if os.path.exists(os.path.join(tmpdir, cert)):
                os.remove(os.path.join(tmpdir, cert))
            if os.path.exists(tmpdir) and tmpdir != "/":
                os.rmdir(tmpdir)

def getdeps(**kwargs):
    """Install build dependencies for this platform."""
    system = platform.system()
    if system == 'Linux':
        dist = platform.dist()[0]
        if dist == 'debian' or dist == 'Ubuntu':
            _debian_getdeps()
        elif dist == 'centos':
            _centos_getdeps()
        elif dist == 'SuSE':
            _opensuse_getdeps()
        elif dist == 'fedora':
            _fedora_getdeps()
        else:
            raise AssertionError("Unsupported dist: %s" % (dist))
    elif system == 'SunOS':
        release = platform.release()
        if release == '5.11':
            _sol11_getdeps(**kwargs)
        else:
            raise NotImplementedError()
    else:
        raise AssertionError("Unsupported operating system: %s" % (system))

def _make_tarball(tarball=None):
    sysname = _detect_sysname()
    if sysname is None:
        raise AssertionError("Cannot find sysname.")
    if tarball is None:
        # Hack Alert:  Put the tarball into the afs-robotest distribution directory if present.
        tardir = os.path.expanduser('~/.afsrobotestrc/dist')
        if not os.path.isdir(tardir):
            tardir = '.'
        tarball = os.path.join(tardir, "openafs-%s.tar.gz" % (sysname))
    tar(tarball, sysname)
    logger.info("Created tar file %s", tarball)

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
    srcdir = kwargs.get('srcdir', '.')
    tarball = kwargs.get('tarball', None)

    if cf is not None:
        cf = shlex.split(cf)  # Note: shlex handles quoting properly.
    else:
        cf = DEFAULT_CF
        if sysname == "Linux":
            if not '--disable-checking' in cf:
                cf.append('--enable-checking')
            if modern_kmod_name:
                cf.append('--with-linux-kernel-packaging')
        if transarc_paths and not '--enable-transarc-paths' in cf:
            cf.append('--enable-transarc-paths')

    # Sadly, the top-level target depends on the mode we are
    # building.
    if target == 'all' and '--enable-transarc-paths' in cf:
        target = 'dest'

    if srcdir == '.':
        _sanity_check_dir()
    if clean:
        _clean(srcdir)
    _setenv()
    if not os.path.exists('%s/configure' % srcdir):
        sh('/bin/sh', '-c', 'cd %s && ./regen.sh' % srcdir)
    if not os.path.exists('config.status'):
        sh('%s/configure' % srcdir, *cf)
    _make(jobs, target)
    if target == 'dest':
        _make_tarball(tarball)

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
    jobs = kwargs.get('jobs', 1)
    source = kwargs.get('source', False)
    if clean:
        _clean('.')
    sh('./regen.sh', '-q')
    sh('./configure')
    sh('make', '-j', jobs, 'dist')
    srpm = _make_srpm(jobs)
    if not source:
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
