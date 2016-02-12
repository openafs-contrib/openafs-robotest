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

from afsutil.system import run, which
from afsutil.transarc import AFS_SRV_BIN_DIR, AFS_SRV_SBIN_DIR, AFS_WS_DIR

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


def asetkey(*args, **kwargs):
    global ASETKEY
    if ASETKEY is None:
        ASETKEY = which('asetkey', extra_paths=PATHS, raise_errors=True)
    return run(ASETKEY, args=args, **kwargs)

def kinit(*args, **kwargs):
    global KINIT
    extra_paths = ['/usr/bin', '/usr/sbin', '/usr/kerberos/bin', '/usr/heimdal/bin']
    if KINIT is None:
        KINIT = which('kinit', extra_paths=extra_paths, raise_errors=True)
    return run(KINIT, args=args, **kwargs)

def aklog(*args, **kwargs):
    global AKLOG
    if AKLOG is None:
        AKLOG = which('aklog', extra_paths=PATHS, raise_errors=True)
    return run(AKLOG, args=args, **kwargs)

def bos(*args, **kwargs):
    global BOS
    if BOS is None:
        BOS = which('bos', extra_paths=PATHS, raise_errors=True)
    if os.geteuid() == 0:
        args = list(args)
        args.append('-localauth')
    return run(BOS, args=args, **kwargs)

def vos(*args, **kwargs):
    global VOS
    if VOS is None:
        VOS = which('vos', extra_paths=PATHS, raise_errors=True)
    if os.geteuid() == 0:
        args = list(args)
        args.append('-localauth')
    return run(VOS, args=args, **kwargs)

def pts(*args, **kwargs):
    global PTS
    if PTS is None:
        PTS = which('pts', extra_paths=PATHS, raise_errors=True)
    if os.geteuid() == 0:
        args = list(args)
        args.append('-localauth')
    return run(PTS, args=args, **kwargs)

def fs(*args, **kwargs):
    global FS
    if FS is None:
        FS = which('fs', extra_paths=PATHS, raise_errors=True)
    return run(FS, args=args, **kwargs)

def udebug(*args, **kwargs):
    global UDEBUG
    if UDEBUG is None:
        UDEBUG = which('udebug', extra_paths=PATHS, raise_errors=True)
    return run(UDEBUG, args=args, **kwargs)

def rxdebug(*args, **kwargs):
    global RXDEBUG
    if RXDEBUG is None:
        RXDEBUG = which('rxdebug', extra_paths=PATHS+[os.path.join(AFS_WS_DIR,'etc')], raise_errors=True)
    return run(RXDEBUG, args=args, **kwargs)

def tokens(*args, **kwargs):
    global TOKENS
    if TOKENS is None:
        TOKENS = which('tokens', extra_paths=PATHS+[os.path.join(AFS_WS_DIR,'bin')], raise_errors=True)
    return run(TOKENS, args=args, **kwargs)


