# Copyright (c) 2014-2018 Sine Nomine Associates
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
import sys
import random
from robot.api import logger
import errno


PY2 = (sys.version_info[0] == 2)
if PY2:
    range = xrange


def _convert_errno_parm(code_should_be):
    """ Convert the code_should_be value to an integer
    If code_should_be isn't an integer, then try to use
    the code_should_be value as a errno "name" and extract
    the errno value from the errno module.
    """
    try:
        code = int(code_should_be)
    except ValueError:
        try:
            code = getattr(errno, code_should_be)
        except AttributeError:
            raise AssertionError("code_should_be '%s' is not a valid errno name" % code_should_be)
    return code

class _PathKeywords(object):

    def create_files(self, path, count=1, size=0, depth=0, width=0, fill='zero'):
        """
        Create a directory tree of test files.

        path
          destination path
        count
          number of files to create in each directory
        size
          size of each file
        depth
          sub-directory depth
        width
          number of sub-directories in each directory
        fill
          test files data pattern

        Valid fill values:

        * zero - fill with zero bits
        * one  - fill with one bits
        * random - fill with pseudo random bits
        * fixed  - fill with repetitions of fixed bits
        """
        BLOCKSIZE = 8192
        count = int(count)
        size = int(size)
        depth = int(depth)
        width = int(width)

        if fill == 'zero':
            block = bytearray(BLOCKSIZE)
        elif fill == 'one':
            block = bytearray(BLOCKSIZE)
        elif fill == 'random':
            random.seed(0) # Always make the same psuedo random sequence.
            block = bytearray(random.getrandbits(8) for _ in range(BLOCKSIZE))
        elif fill == 'fixed':
            hexstring = 'deadbeef'
            ncopies = BLOCKSIZE // len(hexstring)
            block = bytearray.fromhex(hexstring * ncopies)
        else:
            raise ValueError("Invalid fill type: %s" % fill)

        nblocks = size // BLOCKSIZE
        partial_size = size % BLOCKSIZE
        if partial_size:
            partial_block = block[0:partial_size]

        def make_files(p, count):
            for i in range(0, count):
                name = os.path.join(p, '%d' % (i))
                with open(name, 'wb') as f:
                    for _ in range(0, nblocks):
                        f.write(block)
                    if partial_size:
                        f.write(partial_block)

        def make_tree(p, d):
            if d > depth:
                return
            if not os.path.isdir(p):
                os.mkdir(p)
            if count:
                make_files(p, count)
            for i in range(0, width):
                make_tree('%s/d%d' % (p, i), d + 1)

        make_tree(path, 0)


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
        if code != _convert_errno_parm(code_should_be):
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
        if code != _convert_errno_parm(code_should_be):
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
        if code != _convert_errno_parm(code_should_be):
            raise AssertionError("unlink returned an unexpected code: %d" % code)

    def link_count_should_be(self, path, count):
        """Fails if the path has an unexpected inode link count."""
        count = int(count)
        if not path:
            raise AssertionError("Empty argument!")
        if os.stat(path).st_nlink != count:
            raise AssertionError("%s does not have %d links" % (path,count))

    def inode_should_be_equal(self, a, b):
        """Fails if paths have different inodes."""
        if not a or not b:
            raise AssertionError("Empty argument!")
        if os.stat(a).st_ino != os.stat(b).st_ino:
            raise AssertionError("%s and %s do not have the same inode number." % (a,b))

    def get_inode(self, path):
        """Returns the inode number of a path."""
        if not path:
            raise AssertionError("Empty argument!")
        return os.stat(path).st_ino

