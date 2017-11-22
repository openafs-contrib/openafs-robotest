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

from robot.libraries.BuiltIn import BuiltIn,RobotNotRunningError

_rf = BuiltIn()

class VariableMissing(Exception):
    pass

class VariableEmpty(Exception):
    pass

def get_var(name):
    """Return the variable value as a string."""
    if not name:
        raise ValueError("get_var argument is missing!")
    try:
        value = _rf.get_variable_value("${%s}" % name)
    except AttributeError:
        value = None
    if value is None:
        raise VariableMissing(name)
    if value == "":
        raise VariableEmpty(name)
    return value

def get_bool(name):
    """Return the variable value as a bool."""
    value = get_var(name)
    return value.lower() in ("yes", "y", "true", "t", "1")

def _split_into_list(name):
    # Split the given scalar into a list. This can be useful since lists can be
    # created only from tests or resources, and we set variables at runtime via
    # the command line or with the robot.run() function, which only supports
    # scalars.
    try:
        value = get_var(name)
        values = [v.strip() for v in value.split(',')]
        _rf.set_global_variable('@{%s}' % name, *values)
    except VariableMissing:
        pass
    except VariableEmpty:
        pass
    except RobotNotRunningError:
        pass

_split_into_list('AFS_FILESERVERS')
