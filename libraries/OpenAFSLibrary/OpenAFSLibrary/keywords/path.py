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
import math
from robot.api import logger

class _PathKeywords(object):

    def create_files(self, path, count, size=0):
        """Create count number fixed size files in the given path.

        Fails if the files are already present.
        """
        count = int(count)
        size = int(size)
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
                        raise IOError("Failed to write block %d to file '%s'." % (j,num))
                if partial:
                    if os.write(fd, pblock) != len(pblock):
                        raise IOError("Failed to write to file '%s'." % num)
            os.close(fd)

    def directory_entry_should_exist(self, path):
        """Fails if directory entry does not exist in the given path."""
        base = os.path.basename(path)
        dir = os.path.dirname(path)
        if not base in os.listdir(dir):
            raise AssertionError("Directory entry '%s' does not exist in '%s'." % (base, dir))

    def should_be_file(self, path):
        """Fails if path is not a file."""
        if not path:
            raise AssertionError("Empty argument!")
        if not os.path.isfile(path):
            raise AssertionError("%s is not a file." % path)

    def file_should_be_executable(self, path):
        """Fails if path is not an executable file for the current user."""
        if not path:
            raise AssertionError("Empty argument!")
        if not os.access(path, os.X_OK):
            raise AssertionError("%s is not executable." % path)

    def should_be_symlink(self, path):
        """Fails if path is not a symlink."""
        if not path:
            raise AssertionError("Empty argument!")
        if not os.path.islink(path):
            raise AssertionError("%s is not a symlink." % path)

    def should_not_be_symlink(self, path):
        """Fails if path is a symlink."""
        if not path:
            raise AssertionError("Empty argument!")
        if os.path.islink(path):
            raise AssertionError("%s is a symlink." % path)

    def should_be_dir(self, path):
        """Fails if path is not a directory."""
        if not path:
            raise AssertionError("Empty argument!")
        if not os.path.isdir(path):
            raise AssertionError("%s is not a directory." % path)

    def should_not_be_dir(self, path):
        """Fails if path is a directory."""
        if not path:
            raise AssertionError("Empty argument!")
        if os.path.isdir(path):
            raise AssertionError("%s is a directory." % path)

    def link(self, src, dst, code_should_be=0):
        """Create a hard link."""
        code = 0
        try:
            os.link(src, dst)
        except OSError as e:
            logger.info("os.link(): %s" % e)
            code = e.errno
        logger.info("os.link()=%d" % code)
        if code != int(code_should_be):
            raise AssertionError("link returned an unexpected code: %d" % code)

    def symlink(self, src, dst, code_should_be=0):
        """Create a symlink."""
        code = 0
        try:
            os.symlink(src, dst)
        except OSError as e:
            logger.info("os.symlink(): %s" % e)
            code = e.errno
        logger.info("os.symlink()=%d" % code)
        if code != int(code_should_be):
            raise AssertionError("symlink returned an unexpected code: %d" % code)

    def unlink(self, path, code_should_be=0):
        """Unlink the directory entry."""
        code = 0
        try:
            os.unlink(path)
        except OSError as e:
            logger.info("os.unlink(): %s" % e)
            code = e.errno
        logger.info("os.unlink()=%d" % code)
        if code != int(code_should_be):
            raise AssertionError("unlink returned an unexpected code: %d" % code)

    def link_count_should_be(self, path, count):
        """Fails if the inode link count is not `count`."""
        count = int(count)
        if not path:
            raise AssertionError("Empty argument!")
        if os.stat(path).st_nlink != count:
            raise AssertionError("%s does not have %d links" % (path,count))

    def inode_should_be_equal(self, a, b):
        """Fails if path `a` is a different inode than `b`."""
        if not a or not b:
            raise AssertionError("Empty argument!")
        if os.stat(a).st_ino != os.stat(b).st_ino:
            raise AssertionError("%s and %s do not have the same inode number." % (a,b))

    def get_inode(self, path):
        """Returns the inode number of a path."""
        if not path:
            raise AssertionError("Empty argument!")
        return os.stat(path).st_ino

