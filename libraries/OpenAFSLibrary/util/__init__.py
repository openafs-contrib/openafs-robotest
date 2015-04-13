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

import sys
import os
import re
import imp
import types
import subprocess
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn

# Assume the root is relative to this module. In the future, an environment
# variable may be needed.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources", "dist"))

rf = BuiltIn()

# Helpers

def _emulate_get_variable_value(name):
    """Lookup setting variables when running outside of RF.

    This allows the setup tools to call library keywords.
    """
    if name == 'SITE':
        value = os.path.join(ROOT, 'site')
        return value
    # Local settings.
    settings_py = os.path.join(ROOT, 'settings.py')
    if not os.path.isfile(settings_py):
        raise AssertionError("Cannot find settings.py file! path=%s" % settings_py)
    settings = imp.load_source('settings', settings_py)
    value = getattr(settings, name, None)
    if value is not None:
        return value
    # Default settings for the current distribution type.
    dist_py = os.path.join(DIST, "%s.py" % getattr(settings, 'AFS_DIST'))
    if dist_py is None or not os.path.isfile(dist_py):
        raise AssertionError("Cannot find dist.py file! path=%s" % dist_py)
    dist = imp.load_source('settings.dist', dist_py)
    value = getattr(dist, name, None)
    return value  # may be None


def load_globals(path):
    """Load defaults into the global variable namespace."""
    module = imp.load_source('globals', path)
    for name in dir(module):
        if name.startswith("_"):
            continue
        try:
            value = getattr(module, name, None)
            if value and not get_var(name):
                rf.set_global_variable("${%s}" % name, value)
        except AttributeError:
            pass # allow to load outside of RF

def get_var(name):
    """Return the named variable value or None if it does not exist."""
    try:
        return rf.get_variable_value("${%s}" % name)
    except AttributeError:
        # Look in the settings files directly when running outside of the RF.
        return _emulate_get_variable_value(name)

def run_program(args):
    if isinstance(args, types.StringTypes):
        logger.info("running: string=%s" % args)
        shell = True
    else:
        logger.info("running: args=%s" % " ".join(args))
        shell = False
    proc = subprocess.Popen(args, shell=shell, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = proc.communicate()
    if proc.returncode:
        logger.info("output: " + output)
        logger.info("error:  " + error)
    return (proc.returncode, output, error)

def sudo(cmd, *args):
    rc,out,err = run_program(['sudo', '-n', '/usr/sbin/afs-robotest-sudo', cmd] + list(args))
    if rc == os.EX_NOPERM:
        raise AssertionError("Command not permitted: %s\n" % (cmd));
    if rc != 0:
        raise AssertionError("Command failed: %s: exit code %d" % (cmd, rc))

def rxdebug(*args):
    rc,out,err = run_program([get_var('RXDEBUG')] + list(args))
    if rc != 0:
        raise AssertionError("rxdebug failed! %s" % (err))
    return out

def bos(*args):
    rc,out,err = run_program([get_var('BOS')] + list(args))
    if rc != 0:
        raise AssertionError("bos failed! %s" % (err))
    return out

def vos(*args):
    rc,out,err = run_program([get_var('VOS')] + list(args))
    if rc != 0:
        raise AssertionError("vos failed! %s" % (err))
    return out

def fs(*args):
    rc,out,err = run_program([get_var('FS')] + list(args))
    if rc != 0:
        raise AssertionError("fs failed! %s" % (err))
    return out


