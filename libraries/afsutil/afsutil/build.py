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

"""Helper to build OpenAFS for development and testing."""

import logging
import os
import sys
from afsutil.system import sh, CommandFailed

logger = logging.getLogger(__name__)
DEFAULT_CF = [
    'enable-debug',
    'enable-debug-kernel',
    'disable-optimize',
    'disable-optimize-kernel',
    'without-dot',
]

def _cf(cf, transarc):
    if cf is None:
        cf = DEFAULT_CF
        if os.uname()[0] == "Linux":
            cf.append('enable-checking')
    if transarc:
        cf.append('enable-transarc-paths')
    cf = ['--' + x.lstrip('-') for x in cf]
    return cf

def _clean():
    if os.path.isdir('.git'):
        sh('git', 'clean', '-f', '-d', '-x', '-q')
    else:
        if os.path.isfile('./Makefile'):
            sh('make', 'clean')

def _make_package_rhel_srpm():
    # The script which builds the srpm prints the name of the srpm file
    # generated, so grab it from the output.  The srpm target runs the
    # rhel script to build the source rpm.
    output = sh('make', 'srpm', output=True)
    for line in output:
        if line.startswith('SRPM is '):
            return line.split()[2]
    raise CommandFailed('make', ['srpm'], 1, '', 'Failed to get the srpm filename.')

def _make_package_rhel(srpm):
    # This probably should be moved to a Makefile target.
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

def build(cf=None, target='all', clean=True, transarc=True, **kwargs):
    cf = _cf(cf, transarc)
    if target == 'all' and '--enable-transarc-paths' in cf:
        target = 'dest'
    if clean:
        _clean()
    sh('./regen.sh')
    sh('./configure', *cf)
    if target == 'pkg-rhel':
        sh('make', 'dist')
        srpm = _make_package_rhel_srpm()
        _make_package_rhel(srpm)
    else:
       sh('make', target)

