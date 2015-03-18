# Copyright (c) 2015 Sine Nomine Associates
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
import math
from robot.api import logger

def create_files(path, count, size=0):
    """Create count number fixed size files in the given path.

    Fails if the files are already present.
    """
    if count <= 0:
        return
    fmt = "%%0%dd" % (int(math.log10(float(count))) + 1) # fixed width filenames
    if size > 0:
        block = '\0' * 8192
        blocks = size // len(block)
        partial = size % len(block)
        if partial > 0:
            pblock = '\0' * partial
    for i in xrange(0, count):
        num = os.path.join(path, fmt % (i))
        fd = os.open(num, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0777)
        if size > 0:
            for j in xrange(0, blocks):
                if os.write(fd, block) != len(block):
                    raise IOError("Failed to write block %d to file '%s'" % (j,num))
            if partial:
                if os.write(fd, pblock) != len(pblock):
                    raise IOError("Failed to write to file '%s'" % num)
        os.close(fd)

