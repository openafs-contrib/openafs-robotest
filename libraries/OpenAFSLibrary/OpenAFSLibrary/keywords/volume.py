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
import struct
import socket
import re
import tempfile
import unittest

from robot.api import logger
from OpenAFSLibrary.command import vos, fs, NoSuchEntryError

def examine_path(path):
    info = {}
    out = fs('examine', '-path', path)
    for line in out.splitlines():
        m = re.match(r'File (\S+) \(([\d\.]+)\) contained in volume (\d+)', line)
        if m:
            info['path'] = m.group(1)
            info['fid'] = m.group(2)
            info['vid'] = int(m.group(3))
        m = re.match(r'Volume status for vid = (\d+) named (\S+)', line)
        if m:
            info['name'] = m.group(2)
        m = re.match(r'Current disk quota is unlimited', line)
        if m:
            info['quota'] = 0
        m = re.match(r'Current disk quota is (\d+)', line)
        if m:
            info['quota'] = int(m.group(1))
        m = re.match(r'Current blocks used are (\d+)', line)
        if m:
            info['blocks'] = int(m.group(1))
        m = re.match(r'The partition has (\d+) blocks available out of (\d+)', line)
        if m:
            free = int(m.group(1))
            total = int(m.group(2))
            used = total - free
            info['part'] = {'free':free, 'used':used, 'total':total}
    return info

def get_volume_entry(name_or_id):
    info = {'locked':False}
    out = vos('listvldb', '-name', name_or_id, '-quiet', '-noresolve', '-noauth')
    for line in out.splitlines():
        m = re.search(r'^(\S+)', line)
        if m:
            info['name'] = m.group(1)
        m = re.search(r'RWrite: (\d+)', line)
        if m:
            info['rw'] = m.group(1)
        m = re.search(r'ROnly: (\d+)', line)
        if m:
            info['ro'] = m.group(1)
        m = re.search(r'Backup: (\d+)', line)
        if m:
            info['bk'] = m.group(1)
        m = re.match(r'\s+server (\S+) partition /vicep(\S+) RW Site', line)
        if m:
            info['server'] = m.group(1)
            info['part'] = m.group(2)
        m = re.match(r'\s+server (\S+) partition /vicep(\S+) RO Site', line)
        if m:
            server = m.group(1)
            part = m.group(2)
            if 'rosites' not in info:
                info['rosites'] = []
            info['rosites'].append((server, part))
        m = re.match(r'\s*Volume is currently LOCKED', line)
        if m:
            info['locked'] = True
        m = re.match(r'\s*Volume is locked for a (\S+) operation', line)
        if m:
            info['op'] = m.group(1)
    return info

def release_parent(path):
    ppath = os.path.dirname(path)
    info = examine_path(ppath)
    parent = get_volume_entry(info['vid'])
    if 'ro' in parent:
       vos('release', parent['name'], '-verbose')
       fs("checkvolumes")

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

class _VolumeKeywords(object):
    """Volume keywords."""

    def create_volume(self, name, server=None, part='a', path=None, quota='0', ro=False, acl=None):
        """Create and mount a volume.

        Create a volume and optionally mount the volume. Also optionally create
        a read-only clone of the volume and release the new new volume. Release the
        parent volume if it is replicated.
        """
        vid = None
        if not name:
            raise AssertionError("volume name is required!")
        if server is None or server == '': # use this host
            server = socket.gethostname()
        if path:
            path = os.path.abspath(path)
            if not path.startswith('/afs'):
                raise AssertionError("Path not in '/afs'.")
        out = vos('create', '-server', server, '-partition', part, '-name', name, '-m', quota, '-verbose')
        for line in out.splitlines():
            m = re.match(r'Volume (\d+) created on partition', line)
            if m:
                vid = m.group(1)
        if path:
            fs('mkmount', '-dir', path, '-vol', name)
            if acl:
               fs('setacl', '-dir', path, '-acl', *acl.split(','))
        if ro:
            vos('addsite', '-server', server, '-partition', part, '-id', name)
            vos('release', name, '-verbose')
        if path:
            release_parent(path)
        return vid

    def remove_volume(self, name, path=None, flush=False):
        """Remove a volume.

        Remove the volume and any clones. Optionally remove the given mount point.
        """
        removed_mtpt = False
        try:
            volume = get_volume_entry(name)
        except NoSuchEntryError:
            logger.info("No vldb entry found for volume '%s'" % name)
            volume = None
        if path:
            path = os.path.abspath(path)
            if not os.path.exists(path):
                raise AssertionError("Path not found: %s" % (path))
            if not path.startswith('/afs'):
                raise AssertionError("Path not in '/afs': %s" % (path))
            if flush:
                fs("flush", path)
            fs('rmmount', '-dir', path)
            removed_mtpt = True
        if volume:
            if 'rosites' in volume:
                for server,part in volume['rosites']:
                    vos('remove', '-server', server, '-part', part, '-id', "%s.readonly" % name)
            vos('remove', '-id', name)
        if removed_mtpt:
            release_parent(path)
        fs("checkvolumes")

    def mount_volume(self, path, vol, *options):
        """Mount an AFS volume."""
        fs('mkmount', '-dir', path, '-vol', vol, *options)

    def release_volume(self, name):
        vos('release', '-id', name, '-verbose')
        fs("checkvolumes")

    def volume_should_exist(self, name_or_id):
        """Verify the existence of a read-write volume.

        Fails if the volume entry is not found in the VLDB or the volume is
        not present on the fileserver indicated by the VLDB.
        """
        volume = get_volume_entry(name_or_id)
        out = vos('listvol', '-server', volume['server'], '-partition', volume['part'], '-fast', '-noauth', '-quiet')
        for line in out.splitlines():
            vid = line.strip()
            if vid:
               if volume['rw'] == vid:
                   return
        raise AssertionError("Volume id %s is not present on server '%s', partition '%s'" %
                             (volume['rw'], volume['server'], volume['part']))

    def volume_should_not_exist(self, name_or_id):
        try:
            volume = get_volume_entry(name_or_id)
        except:
            volume = None
        if volume:
            raise AssertionError("Volume entry found in vldb for %s" % (name_or_id))

    def volume_location_matches(self, name_or_id, server, part, vtype='rw'):
        address = socket.gethostbyname(server)
        if vtype not in ('rw', 'ro', 'bk'):
            raise AssertionError("Volume type must be one of 'rw', 'ro', or 'bk'.")
        volume = get_volume_entry(name_or_id)
        logger.info("volume: %s" % (volume))
        if vtype not in volume:
            raise AssertionError("Volume type '%s' not found in VLDB for volume '%s'" % (vtype, name_or_id))
        if vtype == 'ro':
            found = False
            for s,p in volume['rosites']:
                if s == address and p == part:
                    found = True
            if not found:
                raise AssertionError("Volume entry does not contain ro site! %s:%s" % (server, part))
        else:
            if volume['server'] != address or volume['part'] != part:
                raise AssertionError("Volume entry location does not match! expected %s:%s, found %s:%s" %
                                     (address, part, volume['server'], volume['part']))
        out = vos('listvol', '-server', volume['server'], '-partition', volume['part'], '-fast', '-noauth', '-quiet')
        for line in out.splitlines():
            vid = line.strip()
            if vid:
               if volume[vtype] == vid:
                   return
        raise AssertionError("Volume id %s is not present on server '%s', partition '%s'" %
                             (volume['rw'], volume['server'], volume['part']))

    def volume_should_be_locked(self, name):
        """Verify the volume is locked."""
        volume = get_volume_entry(name)
        if not volume['locked']:
            raise AssertionError("Volume '%s' is not locked." % (name))

    def volume_should_be_unlocked(self, name):
        """Verify the volume is unlocked."""
        volume = get_volume_entry(name)
        if volume['locked']:
            raise AssertionError("Volume '%s' is locked." % (name))

    def should_be_a_dump_file(self, filename):
        """Fails if filename is not an AFS dump file."""
        VolumeDump.check_header(filename)

    def create_empty_dump(self, filename):
        """Create the smallest possible valid dump file."""
        volid = 536870999 # random, but valid, volume id
        dump = VolumeDump(filename)
        dump.write(ord('v'), "L", volid)
        dump.write(ord('t'), "HLL", 2, 0, 0)
        dump.write(VolumeDump.D_VOLUMEHEADER, "")
        dump.close()

    def create_dump_with_bogus_acl(self, filename):
        """Create a minimal dump file with bogus ACL record.

        The bogus ACL would crash the volume server before gerrit 11702."""
        volid = 536870999 # random, but valid, volume id
        size, version, total, positive, negative = (0, 0, 0, 1000, 0) # positive is out of range.
        dump = VolumeDump(filename)
        dump.write(ord('v'), "L", volid)
        dump.write(ord('t'), "HLL", 2, 0, 0)
        dump.write(VolumeDump.D_VOLUMEHEADER, "")
        dump.write(VolumeDump.D_VNODE, "LL", 3, 999)
        dump.write(ord('A'), "LLLLL", size, version, total, positive, negative)
        dump.close()

#
# Unit Tests
#
class VolumeKeywordTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.v = _VolumeKeywords()

    def test_create(self):
        name = 'unittest.xyzzy'
        path = "/afs/.robotest/test/%s" % name
        self.v.create_volume(name, path=path, ro=True)
        self.v.remove_volume(name, path=path)

    def test_should_exist(self):
        self.v.volume_should_exist('root.cell')

    def test_should_not_exist(self):
        self.v.volume_should_not_exist('does.not.exist')

    def test_location(self):
        name_or_id = 'root.cell'
        server = socket.gethostname()
        part = 'a'
        self.v.volume_location_matches(name_or_id, server, part, vtype='rw')

    def test_unlocked(self):
        self.v.volume_should_be_unlocked('root.cell')

    def test_create_empty_dump(self):
        filename = tempfile.mktemp()
        self.v.create_empty_dump(filename)
        self.failUnless(os.path.exists(filename))
        self.v.should_be_a_dump_file(filename)
        os.remove(filename)

    def test_create_bogus_dump(self):
        filename = tempfile.mktemp()
        self.v.create_dump_with_bogus_acl(filename)
        self.failUnless(os.path.exists(filename))
        self.v.should_be_a_dump_file(filename)
        os.remove(filename)

# usage: PYTHONPATH=libraries python -m OpenAFSLibrary.keywords.volume
if __name__ == '__main__':
    unittest.main()

