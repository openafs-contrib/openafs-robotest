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

"""Build OpenAFS rpm packages."""

import logging
import os

from afsutil.system import sh, CommandFailed
import afsutil.build

logger = logging.getLogger(__name__)

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

def package(**kwargs):
    """Build the OpenAFS rpm packages."""
    # The rpm spec file contains the configure options for the actual build.
    # We run configure here just to bootstrap the process.
    clean = kwargs.get('clean', True)
    jobs = kwargs.get('jobs', 1)
    source = kwargs.get('source', False)
    if clean:
        afsutil.build._clean('.')
    sh('./regen.sh', '-q')
    sh('./configure')
    sh('make', '-j', jobs, 'dist')
    srpm = _make_srpm(jobs)
    if not source:
        _make_rpm(srpm)
