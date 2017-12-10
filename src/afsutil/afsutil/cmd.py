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

"""Wrappers to invoke AFS command line tools."""

import os
import logging
import time

from afsutil.system import sh, which, CommandFailed
from afsutil.transarc import AFS_SRV_BIN_DIR, AFS_SRV_SBIN_DIR, AFS_WS_DIR

logger = logging.getLogger(__name__)

# Common hidding places.
PATHS = [
    '/usr/bin',
    '/usr/sbin',
    AFS_SRV_BIN_DIR,
    AFS_SRV_SBIN_DIR,
    os.path.join(AFS_WS_DIR, 'bin'),
    os.path.join(AFS_WS_DIR, 'etc'),
    '/usr/kerberos/bin',
    '/usr/heimdal/bin',
]

_cmdpath = {
}

def setpath(cmd, path):
    _cmdpath[cmd] = path

def _run(cmd, args=None, quiet=False, retry=0, wait=1, cleanup=None):
    """Execute a command and return the output as a string.

    cmd:     command to be executed
    args:    list of command line arguments
    quiet:   do not log command and output
    retry:   number of retry attempts, 0 for none
    wait:    delay between retry attempts
    cleanup: cleanup function to run before retry

    returns: command output as a string

    Raises a CommandFailed exception if the command exits with
    a non-zero exit code."""
    count = 0 # retry counter
    if args is None:
        args = []
    elif not isinstance(args, list):
        args = list(args)
    cmd = _cmdpath.get(cmd, cmd)
    args.insert(0, which(cmd, raise_errors=True, extra_paths=PATHS))
    while True:
        try:
            lines = sh(*args, quite=quiet)
            break
        except CommandFailed as cf:
            if count < retry:
                count += 1
                logger.info("Retrying %s command in %d seconds; retry %d of %d.",
                    cmd, wait, count, retry)
                time.sleep(wait)
                if cleanup:
                    cleanup()  # Try to cleanup the mess from the last failure.
            else:
                raise cf
    return "\n".join(lines)

def asetkey(*args, **kwargs):
    return _run('asetkey', args=args, **kwargs)

def kinit(*args, **kwargs):
    return _run('kinit', args=args, **kwargs)

def aklog(*args, **kwargs):
    return _run('aklog', args=args, **kwargs)

def bos(*args, **kwargs):
    if os.geteuid() == 0:
        args = list(args)
        args.append('-localauth')
    return _run('bos', args=args, **kwargs)

def vos(*args, **kwargs):
    if os.geteuid() == 0:
        args = list(args)
        args.append('-localauth')
    return _run('vos', args=args, **kwargs)

def pts(*args, **kwargs):
    if os.geteuid() == 0:
        args = list(args)
        args.append('-localauth')
    return _run('pts', args=args, **kwargs)

def fs(*args, **kwargs):
    return _run('fs', args=args, **kwargs)

def udebug(*args, **kwargs):
    return _run('udebug', args=args, **kwargs)

def rxdebug(*args, **kwargs):
    return _run('rxdebug', args=args, **kwargs)

def tokens(*args, **kwargs):
    return _run('tokens', args=args, **kwargs)
