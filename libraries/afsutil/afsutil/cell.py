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

"""Setup a new AFS cell.

This module requires the server binaries must be installed, the Kerberos
service key is set, and the bosserver running.
"""

import time
import logging
import os
import re
import sys

from afsutil.cli import bos, vos, pts, fs, udebug, rxdebug
from afsutil.system import CommandFailed, afs_mountpoint
from afsutil.transarc import AFS_SRV_LIBEXEC_DIR

logger = logging.getLogger(__name__)

class Host(object):
    """Helper to configure an OpenAFS server using the bos command."""

    def __init__(self, hostname=None, **kwargs):
        """Initialize the afs host object."""
        self._cellname = None   # retrieved with bos
        self._cellhosts = set() # retrieved with bos
        if hostname is None:
            hostname = os.uname()[1]
        self._hostname = hostname

    def cellinfo(self):
        """Retrieve the cell info."""
        output = bos('listhosts', '-server', self._hostname)
        self._cellhosts = set()
        for line in output.splitlines():
            match = re.match(r'Cell name is (\S+)', line)
            if match:
                self._cellname = match.group(1)
            match = re.match(r'\s+Host \S+ is (\S+)', line)
            if match:
                self._cellhosts.add(match.group(1))
        return (self._cellname, self._cellhosts)

    def services(self):
        """Retrieve service names and current status."""
        output = bos('status', '-server', self._hostname, '-long')
        services = {}
        bnode = None
        bstatus = None
        for line in output.splitlines():
            match = re.match(r'Instance ([^,]+),', line)
            if match:
                bnode = match.group(1)
                match = re.search(r'currently (\S+)', line)
                if match:
                    bstatus = match.group(1)
                else:
                    bstatus = 'unknown'
                services[bnode] = {'status':bstatus}
                bnode = None
                bstatus = None
        return services

    def getcellname(self):
        """Get the configured cell name for this host (ThisCell)."""
        self.cellinfo()
        return self._cellname

    def getcellhosts(self):
        """Get the configured cell hosts for this host (CellServDB)."""
        self.cellinfo()
        return self._cellhosts

    def setcellname(self, name):
        """Set the configured cell name for this host (ThisCell)."""
        bos('setcellname', '-server', self._hostname, '-name', name)
        if self.getcellname() != name:
            raise AssertionError("Failed to update cell name!")

    def setcellhosts(self, hosts):
        """Set the configured cell hosts for this host (CellServDB).

        hosts : a sequence of hostname strings or Host objects
        """
        hostnames = set()
        for h in hosts:
            if isinstance(h, Host):
                hostnames.add(h._hostname)
            else:
                hostnames.add(h)
        logging.info("Setting cell hosts to %s", ",".join(hostnames))
        self.cellinfo()
        newhosts = hostnames - self._cellhosts
        oldhosts = self._cellhosts - hostnames
        for newhost in newhosts:
            bos('addhost', '-server', self._hostname, '-host', newhost)
        for oldhost in oldhosts:
            bos('removehost', '-server', self._hostname, '-host', oldhost)
        if self.getcellhosts() != hostnames:
            raise AssertionError("Failed to update cell hosts!")

    def listusers(self):
        output = bos('listusers', '-server', self._hostname)
        return output.replace('SUsers are:', '').split()

    def adduser(self, name):
        users = self.listusers()
        if name not in users:
            bos('adduser', '-server', self._hostname, '-user', name)

    def create_database(self, name, *options):
        """Start the database server."""
        if name in self.services():
            logger.info("Skipping create database for %s; already exists.", name)
            return
        cmd = os.path.join(AFS_SRV_LIBEXEC_DIR, name) # use canonical path
        if options:
            cmd = '"%s %s"' % (cmd, " ".join(options)) # enclose in quotes too
        bos('create', '-server', self._hostname, '-instance', name, '-type', 'simple', '-cmd', cmd)

    def is_sync_site(self, name):
        services = {'ptserver':'7002', 'vlserver':'7003'}
        port = services[name]
        try:
            output = udebug('-server', self._hostname, '-port', port, retry=10)
        except CommandFailed:
            pass
        else:
            logger.debug("udebug for %s: %s", self._hostname, output)
            if re.search(r'clock may be bad', output):
                logger.info("Clock may be bad on host %s.", self._hostname)
            if re.search(r'I am not sync site', output):
                return False
            if re.search(r'I am sync site', output):
                logger.info("I am sync site: %s", self._hostname)
                match = re.search(r'Recovery state (\S+)', output)
                if match:
                    recovery_state = match.group(1)
                    logger.info("Recovery state: %s", recovery_state)
                    if recovery_state == '1f' or recovery_state == 'f':
                        logger.info("Host %s is %s sync site.", self._hostname, name)
                        return True
        return False

    def create_fileserver(self, dafs=True):
        if dafs:
            if 'dafs' in self.services():
                logger.info("Skipping create dafs on %s; already exists.", self._hostname)
                return
            bos('create', '-server', self._hostname,
                      '-instance', 'dafs', '-type', 'dafs',
                      '-cmd',
                       os.path.join(AFS_SRV_LIBEXEC_DIR, 'dafileserver'),
                       os.path.join(AFS_SRV_LIBEXEC_DIR, 'davolserver'),
                       os.path.join(AFS_SRV_LIBEXEC_DIR, 'salvageserver'),
                       os.path.join(AFS_SRV_LIBEXEC_DIR, 'dasalvager'))
        else:
            if 'fs' in self.services():
                logger.info("Skipping create fs on %s; already exists.", self._hostname)
                return
            bos('create', '-server', self._hostname,
                      '-instance', 'fs', '-type', 'fs',
                      '-cmd',
                       os.path.join(AFS_SRV_LIBEXEC_DIR, 'fileserver'),
                       os.path.join(AFS_SRV_LIBEXEC_DIR, 'volserver'),
                       os.path.join(AFS_SRV_LIBEXEC_DIR, 'salvager'))
        # Unfortunataly, bos start does not have a -wait option. So try
        # to use rxdebug to check for readiness.
        time.sleep(10) # give the fileserver a chance to startup.
        rxdebug('-server', self._hostname, '-port', '7000', retry=10)

    def _check_volume(self, name):
        try:
            vos('listvldb', '-name', name, '-quiet', '-noresolve', '-nosort')
        except CommandFailed:
            return False
        else:
            return True

    def create_volume(self, partition, name):
        """Create volume if it does not exist."""
        if self._check_volume(name):
            logger.info("Skipping create volume '%s'; already exists.", name)
        else:
            vos('create', '-server', self._hostname, '-partition', partition, '-name', name, retry=10)


class Cell(object):
    def __init__(self, cell='localcell', db=None, fs=None, admin='admin', **kwargs):
        hostname = os.uname()[1]
        if db is None:
            db = [hostname]
        if fs is None:
            fs = [hostname]
        self.cell = cell
        self.admin = admin.replace('/', '.') # afs uses k4-style seps
        self.dbhosts = [Host(n) for n in set(db)]
        self.fshosts = [Host(n) for n in set(fs)]
        self.servers = [Host(n) for n in set(db + fs)]

    def _wait_for_quorum(self, name, wait=30):
        for attempt in xrange(0, wait):
            if attempt > 0:
                time.sleep(5)
            count = 0
            for host in self.dbhosts:
                if host.is_sync_site(name):
                    count += 1
            if count == 1:
                logger.info("Database quorum reached for %s.", name)
                return
        raise AssertionError("Failed to reach database quorum for %s." % (name))

    def _create_admin(self):
        try:
            pts('createuser', '-name', self.admin)
        except CommandFailed as e:
            if not "Entry for name already exists" in e.err:
                raise
        try:
            pts('adduser', '-user', self.admin, '-group', 'system:administrators')
        except CommandFailed as e:
            if not "Entry for id already exists" in e.err:
                raise

    def _wscell(self):
        output = fs('wscell')  # Raises exception if client is not running.
        match = re.match("This workstation belongs to cell '(\S+)'", output)
        if match:
            cell = match.group(1)
        else:
            raise AssertionError("Unable to get local cell name!")
        logger.info("Cell is %s", self.cell)
        return cell

    def _mount(self, root, mtpt, volume):
        path = os.path.join(root, mtpt)
        if not os.path.exists(path):
            fs('mkmount', '-dir', path, '-vol', volume)
        path = os.path.join(root, ".%s" % (mtpt))
        if not os.path.exists(path):
            fs('mkmount', '-dir', path, '-vol', volume, '-rw')

    def _create_replica(self, name):
        output = vos('listvldb', '-name', name, '-quiet')
        if re.findall(r'^\s+server \S+ partition \S+ RO Site', output, re.M):
            logger.info("Skipping replication of %s; already have a read only site", name)
            return
        server,partition = re.findall(r'^\s+server (\S+) partition (\S+) RW Site', output, re.M)[0]
        vos('addsite', '-server', server, '-partition', partition, '-id', name)
        vos('release', '-id', name)

    def newcell(self):
        """Setup a new cell.

        Server bins must be installed and bosserver running. Client is not running yet."""
        logger.info("Setting up server ThisCell and CellServDB files.")
        for h in self.servers:
            h.setcellname(self.cell)
            h.setcellhosts(self.dbhosts)
        logger.info("Starting the database services.")
        for db in ('ptserver', 'vlserver'):
            for host in self.dbhosts:
                host.create_database(db)
            self._wait_for_quorum(db)
        logger.info("Creating the admin user (username: %s).", self.admin)
        self._create_admin()
        logger.info("Adding user %s to the server superuser list.", self.admin)
        for h in self.servers:
            h.adduser(self.admin)
        logger.info("Starting fileservers.")
        for h in self.fshosts:
            h.create_fileserver()
        logger.info("Creating root.afs and root.cell volumes.")
        # Note: root.afs must be exist before non-dynroot clients are started.
        for name in ('root.afs', 'root.cell'):
            self.fshosts[0].create_volume('a', name)

    def mount_root_volumes(self):
        """Mount and replicate the cell root volumes.

        Should be called after running newcell(), and then starting
        the client. Requires an admin token."""

        afs = afs_mountpoint()
        if afs is None:
            raise AssertionError("Unable to mount volumes; afs is not mounted!")
        dynmount = os.path.join(afs, '.:mount')
        cell = self._wscell()
        if cell != self.cell:
            raise AssertionError("Client side ThisCell file does not match the cell name!")

        logger.info("Mounting top level volumes.")
        # Mount the cell's root.cell volume with the root directory of root.afs
        # which is needed for clients not running in dynroot mode. Use the
        # special path by volume name feature to access the root.afs root
        # directory if this cache manager is running in dynroot mode.
        if os.path.exists(dynmount):
            root_afs = os.path.join(dynmount, '%s:root.afs' % (cell))
        else:
            root_afs = afs
        self._mount(root_afs, cell, 'root.cell')

        # Mount the root.afs under a special hidden directory to make a
        # read-write path available for any changes in the future.
        root_cell = os.path.join(afs, cell)
        root_cell_rw = os.path.join(afs, ".%s" % cell)
        root_afs_rw = os.path.join(root_cell_rw, '.root.afs')
        if not os.path.exists(root_afs_rw):
            fs('mkmount', '-dir', root_afs_rw, '-vol', 'root.afs')

        # Grant world readable access to the top level root directories.  Use
        # the read-write paths in case the volumes have already been released
        # (i.e. this function was already called.)
        for path in (root_afs_rw, root_cell_rw):
            fs('setacl', '-dir', path, '-acl', 'system:anyuser', 'read')

        # Add the read-only clones and release the volumes.
        logger.info("Releasing top level volumes.")
        for volume in ('root.afs', 'root.cell'):
            self._create_replica(volume)
        fs('checkvolumes')

    def create_top_volumes(self, volumes):
        """Create, mount, and replica one or more top-level volumes."""

        afs = afs_mountpoint()
        if afs is None:
            raise AssertionError("Unable to mount volumes; afs is not mounted!")
        cell = self._wscell()
        if cell != self.cell:
            raise AssertionError("Client side ThisCell file does not match the cell name!")

        root_cell_rw = os.path.join(afs, ".%s" % (self.cell))
        # Place top level volumes on the same fileserver as the root volumes.
        for name in volumes:
            self.fshosts[0].create_volume('a', name)
            self._mount(root_cell_rw, name, name)
            fs('setacl', '-dir', os.path.join(root_cell_rw, name), '-acl', 'system:anyuser', 'read')
            self._create_replica(name)
        vos('release', '-id', 'root.cell')
        fs('checkvolumes')

