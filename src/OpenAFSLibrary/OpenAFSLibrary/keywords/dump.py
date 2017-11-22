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

import struct

class VolumeDump(object):
    """Helper class to create and check volume dumps."""

    DUMPBEGINMAGIC = 0xB3A11322
    DUMPENDMAGIC = 0x3A214B6E
    DUMPVERSION = 1

    D_DUMPHEADER = 1
    D_VOLUMEHEADER = 2
    D_VNODE = 3
    D_DUMPEND = 4

    @staticmethod
    def check_header(filename):
        """Verify filename is a dump file."""
        file = open(filename, "r")
        size = struct.calcsize("!BLL")
        packed = file.read(size)
        file.close()
        if len(packed) != size:
            raise AssertionError("Not a dump file: file is too short.")
        (tag, magic, version) = struct.unpack("!BLL", packed)
        if tag != VolumeDump.D_DUMPHEADER:
            raise AssertionError("Not a dump file: wrong tag")
        if magic != VolumeDump.DUMPBEGINMAGIC:
            raise AssertionError("Not a dump file: wrong magic")
        if version != VolumeDump.DUMPVERSION:
            raise AssertionError("Not a dump file: wrong version")

    def __init__(self, filename):
        """Create a new volume dump file."""
        self.file = open(filename, "w")
        self.write(self.D_DUMPHEADER, "LL", self.DUMPBEGINMAGIC, self.DUMPVERSION)

    def write(self, tag, fmt, *args):
        """Write a tag and values to the dump file."""
        packed = struct.pack("!B"+fmt, tag, *args)
        self.file.write(packed)

    def close(self):
        """Write the end of dump tag and close the dump file."""
        self.write(self.D_DUMPEND, "L", self.DUMPENDMAGIC) # vos requires the end tag
        self.file.close()
        self.file = None

class _DumpKeywords(object):
    """Volume dump keywords."""
    volid = 536870999 # random, but valid, volume id

    def _create_empty_dump(self, filename):
        """Create the smallest possible valid dump file."""
        dump = VolumeDump(filename)
        dump.write(ord('v'), "L", self.volid)
        dump.write(ord('t'), "HLL", 2, 0, 0)
        dump.write(VolumeDump.D_VOLUMEHEADER, "")
        dump.close()

    def _create_dump_with_bogus_acl(self, filename):
        """Create a minimal dump file with bogus ACL record.

        The bogus ACL would crash the volume server before gerrit 11702."""
        size, version, total, positive, negative = (0, 0, 0, 1000, 0) # positive is out of range.
        dump = VolumeDump(filename)
        dump.write(ord('v'), "L", self.volid)
        dump.write(ord('t'), "HLL", 2, 0, 0)
        dump.write(VolumeDump.D_VOLUMEHEADER, "")
        dump.write(VolumeDump.D_VNODE, "LL", 3, 999)
        dump.write(ord('A'), "LLLLL", size, version, total, positive, negative)
        dump.close()

    def should_be_a_dump_file(self, filename):
        """Fails if filename is not an AFS dump file."""
        VolumeDump.check_header(filename)

    def create_dump(self, filename, size='small', contains=''):
        if contains == 'bogus-acl':
            self._create_dump_with_bogus_acl(filename)
        elif size == 'empty':
            self._create_empty_dump(filename)
        elif size == 'small':
            self._create_empty_dump(filename) # todo: create a dump file
        else:
            raise ValueError('unsupported size arg: %s' % (size))
