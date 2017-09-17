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
import subprocess
import time

from afsutil.system import which, CommandFailed
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
]

KINIT = None
ASETKEY = None
AKLOG = None
BOS = None
VOS = None
PTS = None
FS = None
UDEBUG = None
RXDEBUG = None
TOKENS = None

def _run(cmd, args=None, quiet=False, retry=0, wait=1, cleanup=None):
    """Run a command and return the output.

    Raises a CommandFailed exception if the command exits with an
    a non zero exit code."""
    if args is None:
        args = []
    else:
        args = list(args)
    cmd = which(cmd, raise_errors=True)
    args.insert(0, cmd)
    for attempt in xrange(0, (retry + 1)):
        if attempt > 0:
            c = os.path.basename(cmd)
            logger.info("Retrying %s command in %d seconds; retry %d of %d.", c, wait, attempt, retry)
            time.sleep(wait)
            if cleanup:
                cleanup()  # Try to cleanup the mess from the last failure.
        logger.debug("running: %s", subprocess.list2cmdline(args))
        proc = subprocess.Popen(
                   args,
                   executable=cmd,
                   shell=False,
                   bufsize=-1,
                   env=os.environ,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)
        output,error = proc.communicate()
        rc = proc.returncode
        logger.debug("result of %s; rc=%d", cmd, rc)
        if output:
            logger.debug("<stdout>")
            logger.debug(output)
            logger.debug("</stdout>")
        if error:
            logger.debug("<stderr>")
            logger.debug(error)
            logger.debug("</stderr>")
        if rc == 0:
            return output
    raise CommandFailed(args, rc, output, error);

def asetkey(*args, **kwargs):
    global ASETKEY
    if ASETKEY is None:
        ASETKEY = which('asetkey', extra_paths=PATHS, raise_errors=True)
    return _run(ASETKEY, args=args, **kwargs)

def kinit(*args, **kwargs):
    global KINIT
    extra_paths = ['/usr/bin', '/usr/sbin', '/usr/kerberos/bin', '/usr/heimdal/bin']
    if KINIT is None:
        KINIT = which('kinit', extra_paths=extra_paths, raise_errors=True)
    return _run(KINIT, args=args, **kwargs)

def aklog(*args, **kwargs):
    global AKLOG
    if AKLOG is None:
        AKLOG = which('aklog', extra_paths=PATHS, raise_errors=True)
    return _run(AKLOG, args=args, **kwargs)

def bos(*args, **kwargs):
    global BOS
    if BOS is None:
        BOS = which('bos', extra_paths=PATHS, raise_errors=True)
    if os.geteuid() == 0:
        args = list(args)
        args.append('-localauth')
    return _run(BOS, args=args, **kwargs)

def vos(*args, **kwargs):
    global VOS
    if VOS is None:
        VOS = which('vos', extra_paths=PATHS, raise_errors=True)
    if os.geteuid() == 0:
        args = list(args)
        args.append('-localauth')
    return _run(VOS, args=args, **kwargs)

def pts(*args, **kwargs):
    global PTS
    if PTS is None:
        PTS = which('pts', extra_paths=PATHS, raise_errors=True)
    if os.geteuid() == 0:
        args = list(args)
        args.append('-localauth')
    return _run(PTS, args=args, **kwargs)

def fs(*args, **kwargs):
    global FS
    if FS is None:
        FS = which('fs', extra_paths=PATHS, raise_errors=True)
    return _run(FS, args=args, **kwargs)

def udebug(*args, **kwargs):
    global UDEBUG
    if UDEBUG is None:
        UDEBUG = which('udebug', extra_paths=PATHS, raise_errors=True)
    return _run(UDEBUG, args=args, **kwargs)

def rxdebug(*args, **kwargs):
    global RXDEBUG
    if RXDEBUG is None:
        RXDEBUG = which('rxdebug', extra_paths=PATHS+[os.path.join(AFS_WS_DIR,'etc')], raise_errors=True)
    return _run(RXDEBUG, args=args, **kwargs)

def tokens(*args, **kwargs):
    global TOKENS
    if TOKENS is None:
        TOKENS = which('tokens', extra_paths=PATHS+[os.path.join(AFS_WS_DIR,'bin')], raise_errors=True)
    return _run(TOKENS, args=args, **kwargs)
