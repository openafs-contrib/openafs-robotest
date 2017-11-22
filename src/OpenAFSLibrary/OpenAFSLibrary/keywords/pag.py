# Copyright (c) 2014-2016, Sine Nomine Associates
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

import os
import subprocess
from robot.api import logger
from OpenAFSLibrary.variable import get_var, get_bool

PAG_MIN = 0x41000000
PAG_MAX = 0x41ffffff
PAG_ONEGROUP = True

def _get_pag_from_one_group(gids):
    pag = None
    for gid in gids:
        if PAG_MIN <= gid <= PAG_MAX:
            if pag is None:
                pag = gid
                logger.debug("pag=%d" % (pag))
            else:
                raise AssertionError("More than one PAG group found.")
    return pag

def _get_pag_from_two_groups(g0, g1):
    pag = None
    g0 -= 0x3f00
    g1 -= 0x3f00
    if g0 < 0xc000 and g1 < 0xc000:
        l = ((g0 & 0x3fff) << 14) | (g1 & 0x3fff)
        h = (g0 >> 14)
        h = (g1 >> 14) + h + h + h
        x = ((h << 28) | l)
        if PAG_MIN <= x <= PAG_MAX:
            pag = x
    return pag

def _pag_from_groups(gids):
    logger.debug("gids=%s" % (gids,))
    pag = None
    try:
        PAG_ONEGROUP = get_bool('PAG_ONEGROUP')
    except:
        PAG_ONEGROUP = True

    if PAG_ONEGROUP:
        pag = _get_pag_from_one_group(gids)
    elif len(gids) > 1:
        pag = _get_pag_from_two_groups(gids[0], gids[1])
    return pag

class _PagKeywords(object):

    def pag_from_groups(self, gids=None):
        """Return the PAG from the given group id list."""
        logger.debug("gids=%s" % (gids,))
        if gids is None:
            gids = os.getgroups()
        else:
            # Convert the given string to a list of ints.
            gids = [int(x.strip('[],')) for x in gids.split()]
        pag = _pag_from_groups(gids)
        if pag is None:
            pag = 'None'
        else:
            pag = '%d' % pag
        return pag

    def pag_should_exist(self):
        """Fails if a PAG is not set."""
        gids = os.getgroups()
        pag = _pag_from_groups(gids)
        if pag is None:
            raise AssertionError("PAG is not set")
        logger.debug("ok")

    def pag_should_not_exist(self):
        """Fails if a PAG is set."""
        gids = os.getgroups()
        pag = _pag_from_groups(gids)
        if pag is not None:
            raise AssertionError("PAG is set (%d)" % (pag))
        logger.debug("ok")

    def pag_should_be_valid(self, pag):
        """Fails if the given PAG number is out of range."""
        if pag is None:
            raise AssertionError("PAG is None.")
        pag = pag.rstrip()
        if pag == 'None' or pag == '':
            raise AssertionError("PAG is None.")
        pag = int(pag)
        logger.info("Checking PAG value %d" % (pag))
        if not PAG_MIN <= pag <= PAG_MAX:
            raise AssertionError("PAG is out of range: %d" % (pag))
        logger.debug("ok")

    def pag_shell(self, script):
        """Run a command in the pagsh and returns the output."""
        PAGSH = get_var('PAGSH')
        logger.info("running %s" % (PAGSH,))
        pagsh = subprocess.Popen(PAGSH, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, error) = pagsh.communicate(input=script)
        code = pagsh.wait()
        if code == 0:
            logger.debug("stdin=%s" % (script))
            logger.debug("code=%d" % (code,))
            logger.debug("stdout=%s" % (output,))
            logger.debug("stderr=%s" % (error,))
        else:
            logger.info("stdin=%s" % (script))
            logger.info("code=%d" % (code,))
            logger.info("stdout=%s" % (output,))
            logger.info("stderr=%s" % (error,))
            raise AssertionError("Failed to run pagsh!")
        return output

