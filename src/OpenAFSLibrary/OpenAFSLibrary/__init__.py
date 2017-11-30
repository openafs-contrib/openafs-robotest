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

"""Robotframe keyword library for OpenAFS tests"""

from OpenAFSLibrary.__version__ import VERSION as __version__

from OpenAFSLibrary.keywords import _CommandKeywords
from OpenAFSLibrary.keywords import _LoginKeywords
from OpenAFSLibrary.keywords import _PathKeywords
from OpenAFSLibrary.keywords import _ACLKeywords
from OpenAFSLibrary.keywords import _VolumeKeywords
from OpenAFSLibrary.keywords import _RxKeywords
from OpenAFSLibrary.keywords import _PagKeywords
from OpenAFSLibrary.keywords import _CacheKeywords
from OpenAFSLibrary.keywords import _DumpKeywords

class OpenAFSLibrary(
    _CommandKeywords,
    _LoginKeywords,
    _PathKeywords,
    _ACLKeywords,
    _VolumeKeywords,
    _RxKeywords,
    _PagKeywords,
    _CacheKeywords,
    _DumpKeywords,
    ):
    """Robot Framework test library for OpenAFS (preliminary).

    `OpenAFSLibrary` provides keywords for basic OpenAFS testing. It
    includes keywords to install OpenAFS client and servers and
    setup a cell for testing.

    = Settings =

    == Test cell name ==

    The following settings specify the test cell and user names:
    | AFS_CELL          | Test cell name |
    | AFS_ADMIN         | Test cell admin username |
    | AFS_USER          | Test cell username |

    === Command paths ===

    | AKLOG   |   `/usr/afsws/bin/aklog` |
    | ASETKEY |   `/usr/afs/bin/asetkey` |
    | BOS     |   `/usr/afs/bin/bos` |
    | FS      |   `/usr/afs/bin/fs` |
    | PAGSH   |   `/usr/afsws/bin/pagsh` |
    | PTS     |   `/usr/afs/bin/pts` |
    | RXDEBUG |   `/usr/afsws/etc/rxdebug` |
    | TOKENS  |   `/usr/afsws/bin/tokens` |
    | UDEBUG  |   `/usr/afs/bin/udebug` |
    | UNLOG   |   `/usr/afsws/bin/unlog` |
    | VOS     |   `/usr/afs/bin/vos` |
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = __version__


