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

"""Build OpenAFS from sources (developer tool)"""

import logging
import os
import re
import shlex
import platform
import glob

from afsutil.system import sh, CommandFailed, tar, mkdirp

logger = logging.getLogger(__name__)

def cfopts():
    """Return the default configure options for this system."""
    options = [
        '--enable-debug',
        '--enable-debug-kernel',
        '--disable-optimize',
        '--disable-optimize-kernel',
        '--without-dot',
        '--enable-transarc-paths',
    ]
    sysname = os.uname()[0]
    if sysname == "Linux":
        options.append('--with-linux-kernel-packaging')
        options.append('--enable-checking')
    return " ".join(options)

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
        output = sh('git', '--git-dir', gitdir, 'config', '--bool', '--get', 'afsutil.clean')
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
            sh('git', '--git-dir', gitdir, '--work-tree', srcdir, 'clean', '-f', '-d', '-x', '-q', output=False)
    else:
        if os.path.isfile('./Makefile'): # Maybe out of tree, not in srcdir.
            sh('make', 'clean', output=False)

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

def _make_tarball(tarball=None):
    sysname = _detect_sysname()
    if sysname is None:
        raise AssertionError("Cannot find sysname.")
    if tarball is None:
        tardir = 'packages'
        if not os.path.isdir(tardir):
            mkdirp(tardir)
        tarball = os.path.join(tardir, "openafs-%s.tar.gz" % (sysname))
    tar(tarball, sysname)
    logger.info("Created tar file %s", tarball)

def _cfadd(cf, option):
    if option in cf:
        cf.remove(option)

def _cfrm(cf, option):
    if option not in cf:
        cf.append(option)

def build(**kwargs):
    """Build the OpenAFS binaries.

    Build the transarc-path compatible bins by default, which are
    deprecated, but old habits die hard.
    """
    cf = kwargs.get('cf', cfopts())
    target = kwargs.get('target', 'all')
    clean = kwargs.get('clean', True)
    no_transarc_paths = kwargs.get('no_transarc_paths', False)
    no_modern_kmod_name = kwargs.get('no_modern_kmod_name', False)
    jobs = kwargs.get('jobs', 1)
    srcdir = kwargs.get('srcdir', '.')
    tarball = kwargs.get('tarball', None)

    cf = shlex.split(cf)  # Note: shlex handles quoting properly.
    if no_transarc_paths:
        _cfrm(cf, '--enable-transarc-paths')
    if no_modern_kmod_name:
        _cfrm(cf, '--with-linux-kernel-packaging')

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
        sh('/bin/sh', '-c', 'cd %s && ./regen.sh' % srcdir, output=False)
    if not os.path.exists('config.status'):
        sh('%s/configure' % srcdir, *cf, output=False)
    _make(jobs, target)
    if target == 'dest':
        _make_tarball(tarball)

def _make(jobs, target):
    uname = os.uname()[0]
    if uname == "Linux":
        sh('make', '-j', jobs, target, output=False)
    elif uname == "SunOS":
        sh('make', target, output=False)
    else:
        raise AssertionError("Unsupported operating system: %s" % (uname))
