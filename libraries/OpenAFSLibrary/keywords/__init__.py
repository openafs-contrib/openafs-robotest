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

from system import _SystemKeywords
from keytab import _KeytabKeywords
from login import _LoginKeywords
from path import _PathKeywords
from acl import _ACLKeywords
from volume import _VolumeKeywords
from rx import _RxKeywords

__all__ = [
    '_SystemKeywords',
    '_KeytabKeywords',
    '_LoginKeywords',
    '_PathKeywords',
    '_ACLKeywords',
    '_VolumeKeywords',
    '_RxKeywords'
]

def import_dist_variables():
    import os
    import glob
    from OpenAFSLibrary.util import get_var,run_program,load_globals,DIST
    if not get_var('AFS_DIST'):
        raise AssertionError("AFS_DIST is not set!")
    dist = os.path.abspath(os.path.join(DIST, "%s.py" % get_var('AFS_DIST')))
    if not os.path.isfile(dist):
        raise AssertionError("Unable to find dist file! %s" % dist)
    load_globals(dist)

import_dist_variables()

