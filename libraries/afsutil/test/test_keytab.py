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

import unittest
import tempfile
import subprocess
import os

import afsutil.cmd
import afsutil.system
from afsutil.keytab import Keytab, _split_principal
from afsutil.keytab import _check_for_extended_keyfile_support

have_klist = afsutil.system.which("klist")
asetkey_new= os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "asetkey-new")
asetkey_old= os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "asetkey-old")

class _KeytabTest(unittest.TestCase):
    """Requires kinit and a pregenerated keytab."""

    def __init__(self, *args, **kwargs):
        # Test with keytab previously created with kadmin.
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.testfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "example.keytab")
        assert os.path.exists(self.testfile)

    def test_split_principal(self):
        self.assertRaises(ValueError, _split_principal, "missing_realm")
        c,r = _split_principal("myname@MYREALM")
        self.assertEqual(c, ["myname"])
        self.assertEqual(r, "MYREALM")
        c,r = _split_principal("afs/mycell@MYREALM")
        self.assertEqual(c, ["afs", "mycell"])
        self.assertEqual(r, "MYREALM")

    def test_read_keytab(self):
        k = Keytab.load(self.testfile)
        self.assertIsNotNone(k)
        self.assertEquals(len(k.entries), 16)
        self.assertEquals(k.entries[0]['realm'], "LOCALREALM")
        self.assertEquals(k.entries[0]['principal'], "afs/robotest@LOCALREALM")
        self.assertEquals(k.entries[0]['kvno'], 10)
        self.assertEquals(k.entries[0]['eno'], 18)
        self.assertEquals(k.entries[0]['enctype'], 'aes256-cts-hmac-sha1-96')

    @unittest.skipUnless(have_klist, "missing klist")
    def test_create_empty_file(self):
        fd,filename = tempfile.mkstemp()
        try:
            k = Keytab()
            k.write(filename)
            self.assertEqual(k.entries, [])
            out = subprocess.check_output(["klist", "-e", "-k", "-t", filename]).splitlines()
            self.assertEquals(len(out), 3)
            self.assertTrue(out[0].startswith("Keytab name"))
            self.assertTrue(out[1].startswith("KVNO Timestamp"))
            self.assertTrue(out[2].startswith("----"))
        finally:
            os.close(fd)
            os.remove(filename)

    @unittest.skipUnless(have_klist, "missing klist")
    def test_create_fake_aes_key(self):
        fd,filename = tempfile.mkstemp()
        try:
            k = Keytab()
            k.add_fake_key("afs/localcell@LOCALCELL")
            k.write(filename)
            out = subprocess.check_output(["klist", "-e", "-k", "-t", filename]).splitlines()
            self.assertEquals(len(out), 4)
            self.assertTrue(out[0].startswith("Keytab name"))
            self.assertTrue(out[1].startswith("KVNO Timestamp"))
            self.assertTrue(out[2].startswith("----"))
            self.assertTrue("afs/localcell@LOCALCELL" in out[3])
            self.assertTrue("aes256-cts-hmac-sha1-96" in out[3])
        finally:
            os.close(fd)
            os.remove(filename)

    @unittest.skipUnless(have_klist, "missing klist")
    def test_create_fake_des_key(self):
        fd,filename = tempfile.mkstemp()
        try:
            k = Keytab()
            k.add_fake_key("afs/localcell@LOCALCELL", enctype='des-cbc-crc')
            k.write(filename)
            out = subprocess.check_output(["klist", "-e", "-k", "-t", filename]).splitlines()
            self.assertEquals(len(out), 4)
            self.assertTrue(out[0].startswith("Keytab name"))
            self.assertTrue(out[1].startswith("KVNO Timestamp"))
            self.assertTrue(out[2].startswith("----"))
            self.assertTrue("afs/localcell@LOCALCELL" in out[3])
            self.assertTrue("des-cbc-crc" in out[3])
        finally:
            os.close(fd)
            os.remove(filename)


    def test_get_kvno(self):
        k = Keytab()
        k.read(self.testfile)
        self.assertEquals(k.get_kvno("afs/robotest@LOCALREALM"), 10)
        self.assertEquals(k.get_kvno("robotest@LOCALREALM"), 19)
        self.assertEquals(k.get_kvno("bogus@BOGUS"), None)

    def test_get_entries(self):
        k = Keytab()
        k.read(self.testfile)
        entries = k.get_entries("afs/robotest@LOCALREALM")
        self.assertIsNotNone(entries)
        self.assertEquals(len(entries), 4)
        self.assertEquals(entries[0]['kvno'], 10)

    def test_get_entries_for_kvno(self):
        k = Keytab()
        k.read(self.testfile)
        entries = k.get_entries("robotest@LOCALREALM", 18) # not the max kvno
        self.assertIsNotNone(entries)
        self.assertEquals(len(entries), 4)

    def test_is_des(self):
        k = Keytab()
        k.read(self.testfile)
        self.assertTrue(k.is_des("afs/plugh@LOCALREALM"))
        self.assertFalse(k.is_des("afs/xyzzy@LOCALREALM"))
        # The following has a mix of des and non-des.
        self.assertRaises(AssertionError, Keytab.is_des, k, "afs/robotest@LOCALREALM")
        # No keys for the following.
        self.assertRaises(AssertionError, Keytab.is_des, k, "afs/bogus@LOCALREALM")

    def test_service_principals_0(self):
        k = Keytab()
        self.assertEquals(len(k.service_principals()), 0)

    def test_service_principals_1(self):
        k = Keytab()
        k.add_fake_key("afs/foobar@FOOBAR")
        self.assertEquals(len(k.service_principals()), 1)

    def test_service_principals_n(self):
        k = Keytab.load(self.testfile)
        self.assertItemsEqual(k.service_principals(),
            ['afs/xyzzy@LOCALREALM', 'afs/robotest@LOCALREALM', 'afs/plugh@LOCALREALM'])

    @unittest.skipIf(not os.path.exists(asetkey_old), "missing test old asetkey")
    def test_check_for_no_extended_keyfile_support(self):
        origprog = afsutil.cmd.ASETKEY
        afsutil.cmd.ASETKEY = asetkey_old
        self.assertFalse(_check_for_extended_keyfile_support())
        afsutil.cmd.ASETKEY = origprog

    @unittest.skipIf(not os.path.exists(asetkey_new), "missing test new asetkey")
    def test_check_for_extended_keyfile_support(self):
        origprog = afsutil.cmd.ASETKEY
        afsutil.cmd.ASETKEY = asetkey_new
        self.assertTrue(_check_for_extended_keyfile_support())
        afsutil.cmd.ASETKEY = origprog

    @unittest.skipIf(not os.path.exists(asetkey_new), "missing test new asetkey")
    def test_guess_key_format(self):
        origprog = afsutil.cmd.ASETKEY
        afsutil.cmd.ASETKEY = asetkey_new
        k = Keytab()
        principal = "afs/xyzzy@LOCALREALM"
        k.add_fake_key(principal)
        self.assertEquals(k._guess_key_format(principal), 'extended')
        afsutil.cmd.ASETKEY = origprog

if __name__ == "__main__":
     unittest.main()

