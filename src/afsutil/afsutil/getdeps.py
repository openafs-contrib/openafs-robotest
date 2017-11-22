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

"""Install build dependencies (developer tool)"""

import logging
import os
import platform
import urllib2
import tempfile

from afsutil.system import sh, CommandFailed

logger = logging.getLogger(__name__)

def _debian_getdeps():
    sh('apt-get', '-y', 'build-dep', 'openafs', output=False)
    sh('apt-get', '-y', 'install', 'linux-headers-%s' % platform.release(), output=False)
    sh('apt-get', '-y', 'install', 'libtool', output=False)

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
       'redhat-rpm-config',
       output=False)

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
       output=False)
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
       'redhat-rpm-config',
       output=False)

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
           '-g', 'https://pkg.oracle.com/solarisstudio/release', 'solarisstudio',
           output=False)

        logger.info("Getting available solarisstudio packages.")
        output = sh('pkg', 'list', '-H', '-a', '-v', '--no-refresh', 'pkg://solarisstudio/*', quiet=True)
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
            sh('pkg', 'install', '--accept', pkg, output=False)


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
            output=False)
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
