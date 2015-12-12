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

from OpenAFSLibrary.util import get_var,run_program

class CommandFailed(Exception):
    def __init__(self, name, err):
        self.name = name
        self.err = err

    def __str__(self):
        msg = "%s failed! %s" % (self.name, self.err.strip())
        return repr(msg)

class NoSuchEntryError(CommandFailed):
    def __init__(self):
        CommandFailed.__init__(self, "vos", "no such volume in the vldb")

def rxdebug(*args):
    rc,out,err = run_program([get_var('RXDEBUG')] + list(args))
    if rc != 0:
        raise CommandFailed('rxdebug', err)
    return out

def bos(*args):
    rc,out,err = run_program([get_var('BOS')] + list(args))
    if rc != 0:
        raise CommandFailed('bos', err)
    return out

def vos(*args):
    rc,out,err = run_program([get_var('VOS')] + list(args))
    if rc != 0:
        lines = err.splitlines()
        if len(lines) > 0 and lines[0] == "VLDB: no such entry":
            raise NoSuchEntryError()
        else:
            raise CommandFailed('vos', err)
    return out

def fs(*args):
    rc,out,err = run_program([get_var('FS')] + list(args))
    if rc != 0:
        raise CommandFailed('fs', err)
    return out


