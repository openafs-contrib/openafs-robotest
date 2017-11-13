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
#

import types
import subprocess
from robot.api import logger
from OpenAFSLibrary.variable import get_var

class CommandFailed(Exception):
    def __init__(self, name, args, err):
        self.name = name
        self.err = err
        self.args = list(args)

    def __str__(self):
        msg = "%s %s failed! %s" % (self.name, self.args, self.err.strip())
        return repr(msg)

class NoSuchEntryError(CommandFailed):
    def __init__(self, args):
        CommandFailed.__init__(self, "vos", args, "no such volume in the vldb")

def run_program(args):
    if isinstance(args, types.StringTypes):
        cmd_line = args
        shell = True
    else:
        args = [str(a) for a in args]
        cmd_line = " ".join(args)
        shell = False
    logger.info("running: %s" % cmd_line)
    proc = subprocess.Popen(args, shell=shell, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = proc.communicate()
    if proc.returncode:
        logger.info("output: " + output)
        logger.info("error:  " + error)
    return (proc.returncode, output, error)

def rxdebug(*args):
    rc,out,err = run_program([get_var('RXDEBUG')] + list(args))
    if rc != 0:
        raise CommandFailed('rxdebug', args, err)
    return out

def bos(*args):
    rc,out,err = run_program([get_var('BOS')] + list(args))
    if rc != 0:
        raise CommandFailed('bos', args, err)
    return out

def vos(*args):
    rc,out,err = run_program([get_var('VOS')] + list(args))
    if rc != 0:
        for line in err.splitlines():
            if "VLDB: no such entry" in line:
                raise NoSuchEntryError(args)
            if "does not exist" in line:
                raise NoSuchEntryError(args)
        raise CommandFailed('vos', args, err)
    return out

def fs(*args):
    rc,out,err = run_program([get_var('FS')] + list(args))
    if rc != 0:
        raise CommandFailed('fs', args, err)
    return out


