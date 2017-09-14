# Copyright (c) 2014-2016 Sine Nomine Associates
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

import sys
import os
import unittest
import StringIO
import tempfile
import socket

sys.path.insert(0, "..")
sys.path.insert(0, ".")
import afsrobot.config

class ConfigTest(unittest.TestCase):

    def test_init(self):
        c = afsrobot.config.Config()
        self.assertIsNotNone(c)

    def test_load_from_string(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s\n")
        self.assertEqual(c.optstr('x', 'a'), 's')

    def test_set_value__change_value(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s\n")
        self.assertEqual(c.optstr('x', 'a'), 's')
        c.set_value('x', 'a', 't')
        self.assertEqual(c.optstr('x', 'a'), 't')

    def test_set_value__add_value(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s\n")
        self.assertEqual(c.optstr('x', 'a'), 's')
        c.set_value('x', 'b', 'u')
        self.assertEqual(c.optstr('x', 'a'), 's')
        self.assertEqual(c.optstr('x', 'b'), 'u')

    def test_set_value__add_section_and_value(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s\n")
        self.assertEqual(c.optstr('x', 'a'), 's')
        c.set_value('y', 'b', 'u')
        self.assertEqual(c.optstr('x', 'a'), 's')
        self.assertEqual(c.optstr('y', 'b'), 'u')

    def test_unset_value__option_exists(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s\n")
        self.assertEqual(c.optstr('x', 'a'), 's')
        c.unset_value('x', 'a')
        out = StringIO.StringIO()
        c.print_values(out=out)
        self.assertEqual(out.getvalue().strip(), "")

    def test_unset_value__option_missing(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s\n")
        c.unset_value('x', 'b')
        out = StringIO.StringIO()
        c.print_values(out=out)
        self.assertEqual(out.getvalue().strip(), "[x]\na = s")

    def test_unset_value__section_missing(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s\n")
        with self.assertRaises(Exception):
            c.unset_value('y', 'b')

    def test_optstr__found(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s1\nb = s2")
        self.assertEqual(c.optstr('x', 'a'), 's1')
        self.assertEqual(c.optstr('x', 'b'), 's2')

    def test_optstr__missing_with_default(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s1\nb = s2")
        self.assertEquals(c.optstr('x', 'c', 'd'), 'd')
        self.assertEquals(c.optstr('y', 'c', 'd'), 'd')

    def test_optstr__missing_without_default(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s1\nb = s2")
        self.assertIsNone(c.optstr('x', 'c'))
        self.assertIsNone(c.optstr('y', 'c'))

    def test_optstr__required_and_missing(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s1\nb = s2")
        with self.assertRaises(ValueError):
            c.optstr('x', 'c', required=True)
        with self.assertRaises(ValueError):
            c.optstr('y', 'c', required=True)

    def test_optbool(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = yes\nb = no\nc = 1\nd = 0\ne = true\nf = false")
        self.assertTrue(c.optbool('x', 'a'))
        self.assertFalse(c.optbool('x', 'b'))
        self.assertTrue(c.optbool('x', 'c'))
        self.assertFalse(c.optbool('x', 'd'))
        self.assertTrue(c.optbool('x', 'e'))
        self.assertFalse(c.optbool('x', 'f'))

    def test_optbool__required_and_missing(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s1\nb = s2")
        with self.assertRaises(ValueError):
            c.optbool('x', 'c', required=True)
        with self.assertRaises(ValueError):
            c.optbool('y', 'c', required=True)

    def test_optkeytab(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[kerberos]\nafs_keytab = a\nuser_keytab = b\nfake_keytab = c")
        self.assertEquals(c.optkeytab('afs'), 'a')
        self.assertEquals(c.optkeytab('user'), 'b')
        self.assertEquals(c.optkeytab('fake'), 'c')

    def test_opthostnames__empty(self):
        c = afsrobot.config.Config()
        hostnames = c.opthostnames()
        self.assertTrue(isinstance(hostnames, list))
        self.assertTrue(len(hostnames) == 0)

    def test_opthostnames__not_empty(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[host:a]\na = b\n[host:b]\na = b\n[host:c]\na = b")
        hostnames = c.opthostnames()
        self.assertTrue(isinstance(hostnames, list))
        self.assertTrue(len(hostnames) == 3)

    def test_optfakekey(self):
        home = os.environ['HOME']
        expect = '--cell robotest --keytab %s/afsrobot/fake.keytab --realm ROBOTEST' % (home)
        c = afsrobot.config.Config()
        c.load_defaults()
        args = c.optfakekey()
        self.assertEqual(expect, " ".join(args))

    def test_optlogin(self):
        home = os.environ['HOME']
        expect = '--user robotest.admin --cell robotest --realm ROBOTEST ' \
                 '--akimpersonate --keytab %s/afsrobot/fake.keytab' % (home)
        c = afsrobot.config.Config()
        c.load_defaults()
        args = c.optlogin()
        self.assertEqual(expect, " ".join(args))

    def test_optcomponents(self):
        hostname = socket.gethostname()
        expect = 'server client'
        c = afsrobot.config.Config()
        c.load_defaults()
        args = c.optcomponents(hostname)
        self.assertEqual(expect, " ".join(args))

    def test_optinstall(self):
        hostname = socket.gethostname()
        expect = '--dist none --components server client --cell robotest --hosts %s ' \
                 '--realm ROBOTEST --force -o afsd=-dynroot -fakestat -afsdb -o bosserver=' \
                 % (hostname,)
        c = afsrobot.config.Config()
        c.load_defaults()
        args = c.optinstall(hostname)
        self.assertEqual(expect, " ".join(args))

    def test_optsetkey(self):
        hostname = socket.gethostname()
        home = os.environ['HOME']
        expect = '--cell robotest --realm ROBOTEST --keytab %s/afsrobot/fake.keytab' % (home)
        c = afsrobot.config.Config()
        c.load_defaults()
        args = c.optsetkey(hostname)
        self.assertEqual(expect, " ".join(args))

    def test_optsetkey_noakimp(self):
        hostname = socket.gethostname()
        home = os.environ['HOME']
        expect = '--cell robotest --realm ROBOTEST --keytab %s/afsrobot/afs.keytab' % (home)
        c = afsrobot.config.Config()
        c.load_defaults()
        c.set_value('kerberos', 'akimpersonate', 'no')
        args = c.optsetkey(hostname)
        self.assertEqual(expect, " ".join(args))

    def test_optnewcell(self):
        hostname = socket.gethostname()
        home = os.environ['HOME']
        expect = '--cell robotest --admin robotest.admin ' \
                 '--top test --akimpersonate --keytab %s/afsrobot/fake.keytab --realm ROBOTEST ' \
                 '--fs %s --db %s ' \
                 '-o dafs=yes ' \
                 '-o afsd=-dynroot -fakestat -afsdb ' \
                 '-o bosserver= ' \
                 '-o dafileserver=-d 1 -L ' \
                 '-o davolserver=-d 1' \
                 % (home, hostname, hostname)
        c = afsrobot.config.Config()
        c.load_defaults()
        args = c.optnewcell()
        self.assertEqual(expect, " ".join(args))

    def test_optnewcell_noakimp(self):
        hostname = socket.gethostname()
        home = os.environ['HOME']
        expect = '--cell robotest --admin robotest.admin ' \
                 '--top test --keytab %s/afsrobot/user.keytab --realm ROBOTEST ' \
                 '--fs %s --db %s ' \
                 '-o dafs=yes ' \
                 '-o afsd=-dynroot -fakestat -afsdb ' \
                 '-o bosserver= ' \
                 '-o dafileserver=-d 1 -L ' \
                 '-o davolserver=-d 1' \
                 % (home, hostname, hostname)
        c = afsrobot.config.Config()
        c.load_defaults()
        c.set_value('kerberos', 'akimpersonate', 'no')
        args = c.optnewcell()
        self.assertEqual(expect, " ".join(args))

    def test_print_values(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s\n")
        out = StringIO.StringIO()
        c.print_values(out=out)
        self.assertEqual(out.getvalue().strip(), "[x]\na = s")

    def test_print_values__expanded(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s\nb = %(a)s")
        out = StringIO.StringIO()
        c.print_values(out=out)
        self.assertEqual(out.getvalue().strip(), "[x]\na = s\nb = s")
        out = StringIO.StringIO()
        c.print_values(out=out, raw=False)
        self.assertEqual(out.getvalue().strip(), "[x]\na = s\nb = s")

    def test_print_values__raw(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s\nb = %(a)s")
        out = StringIO.StringIO()
        c.print_values(out=out, raw=True)
        self.assertEqual(out.getvalue().strip(), "[x]\na = s\nb = %(a)s")

    def test_print_values__by_section_expanded(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s\nb = %(a)s")
        out = StringIO.StringIO()
        c.print_values(out=out, section="x")
        self.assertEqual(out.getvalue().strip(), "[x]\na = s\nb = s")
        out = StringIO.StringIO()
        c.print_values(out=out, section="x", raw=False)
        self.assertEqual(out.getvalue().strip(), "[x]\na = s\nb = s")

    def test_print_values__by_section_raw(self):
        c = afsrobot.config.Config()
        c.load_from_string(string="[x]\na = s\nb = %(a)s")
        out = StringIO.StringIO()
        c.print_values(out=out, section="x", raw=True)
        self.assertEqual(out.getvalue().strip(), "[x]\na = s\nb = %(a)s")

    def test_load_from_file(self):
        fd,filename = tempfile.mkstemp()
        try:
            os.write(fd, "[x]\na = s\n")
            c = afsrobot.config.Config()
            c.load_from_file(filename)
            out = StringIO.StringIO()
            c.print_values(out=out)
            self.assertEqual(out.getvalue().strip(), "[x]\na = s")
        finally:
            os.close(fd)
            os.remove(filename)

    def test_load_from_file__with_missing_file(self):
        fd,filename = tempfile.mkstemp()
        try:
            c = afsrobot.config.Config()
            bogus = filename + "-bogus"
            self.assertFalse(os.path.exists(bogus))
            with self.assertRaises(AssertionError):
                c.load_from_file(bogus)
        finally:
            os.close(fd)
            os.remove(filename)

    def test_save_as(self):
        fd,filename = tempfile.mkstemp()
        try:
            c = afsrobot.config.Config()
            c.load_from_string(string="[x]\na = s\n")
            c.save_as(filename)
            with open(filename) as f:
                out = f.read()
            self.assertEqual(out, "[x]\na = s\n\n")
        finally:
            os.close(fd)
            os.remove(filename)

    def test_save(self):
        fd,filename = tempfile.mkstemp()
        try:
            c = afsrobot.config.Config()
            os.write(fd, "[x]\na = s\n")
            c.load_from_file(filename)
            out = StringIO.StringIO()
            c.print_values(out=out)
            self.assertEqual(out.getvalue().strip(), "[x]\na = s")
            c.set('x', 'a', 't')
            out = StringIO.StringIO()
            c.print_values(out=out)
            self.assertEqual(out.getvalue().strip(), "[x]\na = t")
            c.save()
            with open(filename) as f:
                out = f.read()
            self.assertEqual(out, "[x]\na = t\n\n")
        finally:
            os.close(fd)
            os.remove(filename)

    def test_save__with_sequence_error(self):
        # save() without a prior load_from_file() or save_as() should
        # throw an exception.
        c = afsrobot.config.Config()
        with self.assertRaises(AssertionError):
            c.save()

if __name__ == "__main__":
     unittest.main()

