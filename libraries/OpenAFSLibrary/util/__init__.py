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
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
DIST = os.path.join(ROOT, 'resources', 'dist')

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

def say(msg):
    """Display a progress message to the console."""
    stream = sys.__stdout__
    stream.write("%s\n" % (msg))
    stream.flush()

def run_keyword(name, *args):
    """Run the named keyword."""
    rf.run_keyword(name, *args)

def lookup_keywords(filename):
    """Lookup the keyword names in the given resource file."""
    keywords = []
    start_of_table = r'\*+\s+'
    start_of_kw_table = r'\*+\s+Keyword'
    in_kw_table = False
    f = open(filename, "r")
    for line in f.readlines():
        line = line.rstrip()
        if len(line) == 0 or line.startswith("#"):
            continue  # skip comments and blanks
        if re.match(start_of_kw_table, line):
            in_kw_table = True   # table started
            continue
        if re.match(start_of_table, line) and not re.match(start_of_kw_table, line):
            in_kw_table = False  # table ended
            continue
        if line.startswith(' '):
            continue  # skip content rows
        if in_kw_table:
            keywords.append(line)
    f.close()
    return keywords

