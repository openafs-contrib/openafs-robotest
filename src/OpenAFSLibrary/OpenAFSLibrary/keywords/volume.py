# Copyright (c) 2014-2017 Sine Nomine Associates
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
import socket
import re

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

def get_parts(server):
    """Get the server partitions."""
    parts = []
    for line in vos('listpart', server).splitlines():
        line = line.strip()
        if line.startswith("The partitions"):
            continue
        if line.startswith("Total"):
            continue
        for part in line.split():
            parts.append(part.replace("/vicep", ""))
    return parts

def release_parent(path):
    ppath = os.path.dirname(path)
    info = examine_path(ppath)
    parent = get_volume_entry(info['vid'])
    if 'ro' in parent:
       vos('release', parent['name'], '-verbose')
       fs("checkvolumes")

def _zap_volume(name_or_id, server, part):
    try:
        vos('zap', '-id', name_or_id, '-server', server, '-part', part);
    except NoSuchEntryError:
        logger.info("No such volume to zap")

class _VolumeKeywords(object):
    """Volume keywords."""

    def create_volume(self, name, server=None, part='a', path=None, quota='0', ro=False, acl=None, orphan=False):
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
                break
        if vid is None:
            raise AssertionError("Created volume id not found!")
        if path:
            fs('mkmount', '-dir', path, '-vol', name)
            if acl:
               fs('setacl', '-dir', path, '-acl', *acl.split(','))
        if ro:
            vos('addsite', '-server', server, '-partition', part, '-id', name)
            vos('release', name, '-verbose')
        if path:
            release_parent(path)
        if orphan:
            # Intentionally remove the vldb entry for testing!
            vos('delent', '-id', vid)
        return vid

    def remove_volume(self, name_or_id, path=None, flush=False, server=None, part=None, zap=False):
        """Remove a volume.

        Remove the volume and any clones. Optionally remove the given mount point.
        """
        if name_or_id == '0':
            logger.info("Skipping remove for volume id 0")
            return
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
            release_parent(path)
        try:
            volume = get_volume_entry(name_or_id)
        except NoSuchEntryError:
            logger.info("No vldb entry found for volume '%s'" % name_or_id)
        if volume:
            if 'rosites' in volume:
                for server,part in volume['rosites']:
                    vos('remove', '-server', server, '-part', part, '-id', "%s.readonly" % name_or_id)
            vos('remove', '-id', name_or_id)
            fs("checkvolumes")
        elif zap:
            if not server:
                server = socket.gethostname()
            if part:
                try:
                    vos('zap', '-id', name_or_id, '-server', server, '-part', part);
                except NoSuchEntryError:
                    logger.info("No volume {name_or_id} to zap on server {server} part {part}".format(**locals()))
            else:
                for part in get_parts(server):
                    try:
                        vos('zap', '-id', name_or_id, '-server', server, '-part', part);
                    except NoSuchEntryError:
                        logger.info("No volume {name_or_id} to zap on server {server} part {part}".format(**locals()))

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

    def get_volume_id(self, name):
        volume = get_volume_entry(name)
        return volume['rw']
