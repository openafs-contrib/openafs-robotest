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

import os
import glob
import imp
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn

_rf = BuiltIn()
DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "resources", "dist"))

def load_globals(path):
    """Load defaults into the global variable namespace."""
    module = imp.load_source('globals', path)
    for name in dir(module):
        if name.startswith("_"):
            continue
        try:
            value = getattr(module, name, None)
            if value and not _rf.get_variable_value("${%s}" % name):
                _rf.set_global_variable("${%s}" % name, value)
        except AttributeError:
            pass # allow to load outside of RF

def import_dist_variables():
    dist = os.path.abspath(os.path.join(DIST, "%s.py" % get_var('AFS_DIST')))
    if not os.path.isfile(dist):
        raise AssertionError("Unable to find dist file! %s" % dist)
    load_globals(dist)

def get_var(name):
    """Return the variable value."""
    if not name:
        raise AssertionError("get_var argument is missing!")
    try:
        value = _rf.get_variable_value("${%s}" % name)
    except AttributeError:
        value = None
    if value is None:
        raise AssertionError("%s is not set!" % name)
    if value == "":
        raise AssertionError("%s is empty!" % name)
    return value
