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

import os
import unittest
import tempfile
import shutil

from afsutil.system import CommandFailed
from afsutil.system import directory_should_exist
from afsutil.system import directory_should_not_exist
from afsutil.system import is_loaded
from afsutil.system import is_running
from afsutil.system import network_interfaces
from afsutil.system import sh
from afsutil.system import symlink
from afsutil.system import touch
from afsutil.system import which

class SystemTest(unittest.TestCase):

    def test_sh(self):
        self.assertIsNotNone(sh("/bin/ls", "/bin"))
        self.assertIn("sh", sh("/bin/ls", "/bin"))

    def test_sh_fail(self):
        self.assertRaises(CommandFailed, sh, "false")

    def test_directory_should_exist(self):
        self.assertTrue(directory_should_exist("/tmp"))
        self.assertRaises(AssertionError, directory_should_exist, "/bogus")

    def test_directory_should_not_exist(self):
        self.assertTrue(directory_should_not_exist("/bogus"))
        self.assertRaises(AssertionError, directory_should_not_exist, "/tmp")

    def test_is_running(self):
        self.assertTrue(is_running("python"))

    def test_touch(self):
        tdir = tempfile.mkdtemp()
        src = os.path.join(tdir, "xyzzy")
        try:
            touch(src)
        finally:
            shutil.rmtree(tdir)

    def test_symlink(self):
        tdir = tempfile.mkdtemp()
        src = os.path.join(tdir, "xyzzy")
        dst = os.path.join(tdir, "plugh")
        try:
            touch(src)
            symlink(src, dst)
            self.assertTrue(os.path.exists(dst))
            self.assertTrue(os.path.islink(dst))
        finally:
            shutil.rmtree(tdir)

    def test_so_symlinks(self):
        from afsutil.system.sunos import _so_symlinks
        tdir = tempfile.mkdtemp()
        src = os.path.join(tdir, "xyzzy.so.1.0.0")
        try:
            touch(src)
            _so_symlinks(tdir)
            self.assertTrue(os.path.islink(os.path.join(tdir, "xyzzy.so.1.0")))
            self.assertTrue(os.path.islink(os.path.join(tdir, "xyzzy.so.1")))
            self.assertTrue(os.path.islink(os.path.join(tdir, "xyzzy.so")))
        finally:
            shutil.rmtree(tdir)

    def test_network_interfaces(self):
        self.assertTrue(len(network_interfaces()) > 0)
        for addr in network_interfaces():
            self.assertRegexpMatches(addr, r'^\d+\.\d+\.\d+\.\d+$')
            self.assertNotRegexpMatches(addr, r'^127\.\d+\.\d+\.\d+$')

    def test_is_loaded(self):
        mount = which('mount', extra_paths=['/usr/sbin'])
        output = "\n".join(sh(mount))
        if "AFS on /afs" in output:
            self.assertTrue(is_loaded('openafs'))
        else:
            self.assertFalse(is_loaded('openafs'))

if __name__ == "__main__":
     unittest.main()

