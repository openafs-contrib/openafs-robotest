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

"""Setup a new AFS cell.

This module requires the server binaries must be installed, the Kerberos
service key is set, and the bosserver running.
"""

import time
import logging
import os
import re
import socket

from afsutil.cli import bos, vos, pts, fs, udebug, rxdebug
from afsutil.system import CommandFailed, afs_mountpoint
from afsutil.transarc import AFS_SRV_LIBEXEC_DIR

logger = logging.getLogger(__name__)

DBNAMES = ('ptserver', 'vlserver')
PORT = {
    'fileserver': '7000',
    'ptserver':   '7002',
    'vlserver':   '7003',
    'volserver':  '7005',
    'bosserver':  '7007',
}

def _optfsbnode(options):
    """Helper to get the fs bnode type."""
    dafs = options.get('dafs', 'yes').strip() # dafs by default.
    if dafs == 'no' or dafs == 'false' or dafs == '0':
        bnode = 'fs'
    else:
        bnode = 'dafs'
    return bnode

def _optcmdstring(options, program):
    """Helper to get the server cmd line string for bos create."""
    # Use the canonical path, bosserver will convert to the actual path.
    cmd = os.path.join(AFS_SRV_LIBEXEC_DIR, program)
    opts = options.get(program, '').strip()
    return ' '.join(filter(None, [cmd, opts]))

class Host(object):
    """Helper to configure an OpenAFS server using the bos command."""

    def __init__(self, hostname='localhost', **kwargs):
        """Initialize the afs host object."""
        if hostname is None or hostname == 'localhost':
            hostname = socket.gethostname()
        self.hostname = hostname
        # The following are retrieved with bos as needed.
        self.cellname = None
        self.cellhosts = None
        self.users = None

    def rxping(self, service='bosserver', retry=10):
        try:
            rxdebug('-server', self.hostname, '-port', PORT[service], '-version', retry=retry)
        except CommandFailed:
            success = False
        else:
            success = True
        return success

    def cellinfo(self):
        """Retrieve the cell info."""
        if self.cellname is None or self.cellhosts is None:
            output = bos('listhosts', '-server', self.hostname)
            self.cellhosts = set()
            for line in output.splitlines():
                match = re.match(r'Cell name is (\S+)', line)
                if match:
                    self.cellname = match.group(1)
                match = re.match(r'\s+Host \S+ is (\S+)', line)
                if match:
                    self.cellhosts.add(match.group(1))
        return (self.cellname, tuple(self.cellhosts))

    def services(self):
        """Retrieve service names and current status."""
        output = bos('status', '-server', self.hostname, '-long')
        services = {}
        bnode = None
        bstatus = None
        for line in output.splitlines():
            match = re.match(r'Instance ([^,]+),', line)
            if match:
                bnode = match.group(1)
                match = re.search(r'currently (\w+)', line)
                if match:
                    bstatus = match.group(1)
                else:
                    bstatus = 'unknown'
                services[bnode] = {'status':bstatus}
                bnode = None
                bstatus = None
        return services

    def getservice(self, name):
        """Return the status information by name."""
        return self.services().get(name, None)

    def wait_for_status(self, name, target='running', attempts=30, delay=5):
        """Wait for service to reach running state."""
        status = 'unknown'
        logger.info("Waiting for service %s to reach %s on host %s.", name, target, self.hostname)
        for attempt in xrange(0, attempts+1):
            service = self.getservice(name)
            if service is None:
                time.sleep(delay)
                continue
            if service['status'] == target:
                logger.info("Service %s is running on host %s.", name, self.hostname)
                return
            time.sleep(delay)
        if status is None:
            status = 'unknown'
        raise AssertionError("Service %s failed to start on %s; status=%s" % (name, self.hostname, status))

    def getcellname(self):
        """Get the configured cell name for this host (ThisCell)."""
        self.cellinfo()
        return self.cellname

    def getcellhosts(self):
        """Get the configured cell hosts for this host (CellServDB)."""
        self.cellinfo()
        return tuple(self.cellhosts)

    def setcellname(self, name):
        """Set the configured cell name for this host (ThisCell)."""
        bos('setcellname', '-server', self.hostname, '-name', name)
        if self.getcellname() != name:
            raise AssertionError("Failed to update cell name!")

    def setcellhosts(self, hosts):
        """Set the configured cell hosts for this host (CellServDB).

        hosts : a sequence of hostname strings or Host objects
        """
        assert hosts is not None
        assert not isinstance(hosts, basestring) # expect a list or tuple

        hostnames = set()
        for h in hosts:
            if isinstance(h, Host):
                hostnames.add(h.hostname)
            elif isinstance(h, basestring):
                hostnames.add(h)
            else:
                raise AssertionError("Expected a Host object or string.")

        self.cellinfo()
        newhosts = hostnames - self.cellhosts
        oldhosts = self.cellhosts - hostnames
        if newhosts or oldhosts:
            logging.info("Setting cell hosts to %s", ",".join(hostnames))
            for newhost in newhosts:
                bos('addhost', '-server', self.hostname, '-host', newhost)
            for oldhost in oldhosts:
                bos('removehost', '-server', self.hostname, '-host', oldhost)
            self.cellname = None
            self.cellhosts = None
            self.cellinfo()
            if self.cellhosts != hostnames:
                raise AssertionError("Failed to update cell hosts!")

    def listusers(self):
        output = bos('listusers', '-server', self.hostname)
        return output.replace('SUsers are:', '').split()

    def adduser(self, name):
        users = self.listusers()
        if name not in users:
            logger.info("Adding %s to the superuser list on %s.", name, self.hostname)
            bos('adduser', '-server', self.hostname, '-user', name)

    def create_database(self, name, options):
        """Start the database server."""
        service = self.getservice(name)
        if service is not None:
            status = service['status']
            if status == 'running':
                logger.info("Skipping create database for %s; already running.", name)
                return
            if status == 'shutdown':
                logger.info("Retarting database for %s.", name)
                self.restart(name)
                return
            raise AssertionError("Unexpected status '%s' while trying to create db service %s on host %s." % \
                                (status, name, self.hostname))
        bos('create', '-server', self.hostname,
            '-instance', name, '-type', 'simple',
            '-cmd', _optcmdstring(options, name))

    def shutdown(self, name):
        bos('shutdown', '-server', self.hostname, '-instance', name, '-wait')

    def restart(self, name):
        bos('restart', '-server', self.hostname, '-instance', name)

    def is_recovered_sync_site(self, name):
        """Returns true if this is the db sync site and the recovery state is good."""
        port = PORT[name]
        try:
            output = udebug('-server', self.hostname, '-port', port, retry=10)
        except CommandFailed:
            return False
        logger.debug("udebug for %s: %s", self.hostname, output)
        if re.search(r'clock may be bad', output):
            logger.info("Clock may be bad on host %s.", self.hostname)
        if re.search(r'I am not sync site', output):
            return False
        if re.search(r'I am sync site', output):
             match = re.search(r'Recovery state (\S+)', output)
             if match:
                 recovery_state = match.group(1)
             else:
                 recovery_state = '??'
             if recovery_state == '1f' or recovery_state == 'f':
                 logger.info("Database quorum reached for %s; sync site is %s; recovery state is %s.",
                             name, self.hostname, recovery_state)
                 return True
             logger.debug("Host %s is sync site with recovery state %s", self.hostname, recovery_state)
        return False

    def create_fileserver(self, bnode, options):
        if bnode in self.services():
            logger.info("Skipping create %s on %s; already exists.", bnode, self.hostname)
            return
        if bnode == 'dafs':
            bos('create', '-server', self.hostname,
                '-instance', bnode, '-type', bnode,
                '-cmd', _optcmdstring(options, 'dafileserver'),
                '-cmd', _optcmdstring(options, 'davolserver'),
                '-cmd', _optcmdstring(options, 'salvageserver'),
                '-cmd', _optcmdstring(options, 'dasalvager'))
        elif bnode == 'fs':
            bos('create', '-server', self.hostname,
                '-instance', bnode, '-type', bnode,
                '-cmd', _optcmdstring(options, 'fileserver'),
                '-cmd', _optcmdstring(options, 'volserver'),
                '-cmd', _optcmdstring(options, 'salvager'))
        else:
            raise AssertionError("Invalid fs bnode!")

        ok = self.rxping(service='fileserver', retry=60)
        if not ok:
            raise AssertionError("Unable to contact file server at %s." % (self.hostname))
        ok = self.rxping(service='volserver', retry=60)
        if not ok:
            raise AssertionError("Unable to contact volume server at %s." % (self.hostname))

    def _check_volume(self, name):
        try:
            vos('listvldb', '-name', name, '-quiet', '-noresolve', '-nosort')
        except CommandFailed:
            return False
        else:
            return True

    def create_volume(self, name, partition="a"):
        """Create volume if it does not exist."""
        if self._check_volume(name):
            logger.info("Skipping create volume '%s'; already exists.", name)
        else:
            logger.info("Creating volume %s on host %s, partition %s.", name, self.hostname, partition)
            vos('create', '-server', self.hostname, '-partition', partition, '-name', name, retry=60, wait=10)


class Cell(object):

    def __init__(self, cell='localcell', db=None, fs=None, admins=None, options=None, **kwargs):
        """Initialize the cell object.

        The first list element of the db list will be the primary db server,
        and the first element of the fs list will be the primary fileserver.
        """
        # Some sanity checking.
        assert cell is not None and isinstance(cell, basestring)  # expect a string
        assert db is None or not isinstance(db, basestring) # expect a list or tuple
        assert fs is None or not isinstance(fs, basestring) # expect a list or tuple
        assert admins is None or not isinstance(admins, basestring) # expect a list or tuple
        assert options is None or not isinstance(options, basestring) # expect a list or tuple

        # Covert the option list of lists to a dict.
        def optlists2dict(options):
            names = {}
            for optlist in options:
                for o in optlist:
                    name,value = o.split('=', 1)
                    names[name] = value
            return names
        if options is None: options = [[]]
        self.options = optlists2dict(options)

        # Defaults.
        hostname = socket.gethostname()
        if admins is None: admins = ['admin']
        if db is None: db = [hostname]
        if fs is None: fs = [hostname]
        # In case 'localhost' is given as a hostname, convert to the real name.
        db = [hostname if x=='localhost' else x for x in db]
        fs = [hostname if x=='localhost' else x for x in fs]

        # Cell name.
        self.cell = cell

        # Super users for this cell. Convert k5 style names to k4 style for AFS.
        self.admins = [name.replace('/', '.') for name in admins]

        # Create the set of hosts objects for this cell. A given host may
        # be a db server, a file server, or both. Avoid creating duplicate
        # objects.  The first element in the given lists are the primary
        # servers for the cell setup.
        hosts = {}
        for name in set(db + fs):
            hosts[name] = Host(name)
        self.primary_db = hosts[db[0]]
        self.primary_fs = hosts[fs[0]]
        self.db = [hosts[name] for name in set(db)]
        self.fs = [hosts[name] for name in set(fs)]
        self.hosts = hosts.values()

    @classmethod
    def current(cls, **kwargs):
        """Create a cell object from the existing cell."""
        host = Host()
        cell = host.getcellname()
        db = host.getcellhosts()
        fs = ['localhost'] # get from vos listaddrs?
        admins = host.listusers()
        cell = cls(cell=cell, db=db, fs=fs, admins=admins, **kwargs)
        return cell

    def _wait_for_quorum(self, name, attempts=60, delay=10):
        for attempt in xrange(0, attempts+1):
            logger.info("Waiting for %s database quorum; attempt %d of %d.", name, (attempt+1), attempts)
            num_sync_sites = 0
            for host in self.db:
                if host.is_recovered_sync_site(name):
                    num_sync_sites += 1
            if num_sync_sites == 1:
                logger.debug("Database quorum reached for %s.", name)
                return
            time.sleep(delay)
        raise AssertionError("Failed to reach database quorum for %s." % (name))

    def _create_admin(self, admin):
        logger.info("Creating the admin user %s.", admin)
        try:
            pts('createuser', '-name', admin)
        except CommandFailed as e:
            if not "Entry for name already exists" in e.err:
                raise
        try:
            pts('adduser', '-user', admin, '-group', 'system:administrators')
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
        # Sometimes the db drops quorum the first time we write to it after the
        # first election. vos fails with a uquorum error and and the volume is
        # left locked. Use this closure to unlock the the volume before
        # retrying the vos command.
        def _unlocker(name):
            def _unlock():
                try:
                    vos('unlock', '-id', name)
                except:
                    pass
            return _unlock
        vos('addsite', '-server', server, '-partition', partition, '-id', name,
            retry=20, wait=80, cleanup=_unlocker(name))
        vos('release', '-id', name,
            retry=20, wait=80, cleanup=_unlocker(name))

    def ping_hosts(self):
        """Verify hosts are reachable and bosserver is running."""
        failed = []
        for host in self.hosts:
            ok = host.rxping(service='bosserver', retry=0)
            if not ok:
                failed.append(host.hostname)
        if failed:
            s = 's' if len(failed) > 1 else ''
            f = ', '.join(failed)
            raise AssertionError("Failed to reach bosserver on host%s %s" % (s, f))

    def _setup_first_db_server(self):
        """Setup the initial database server and db files."""
        logger.info("Setting up the first database server.")

        # Setup the cell info for a single database server so the empty db can
        # be created and quorum established.
        self.primary_db.setcellname(self.cell)
        self.primary_db.setcellhosts([self.primary_db])
        for dbname in DBNAMES:
            self.primary_db.create_database(dbname, self.options)
            self.primary_db.wait_for_status(dbname, target='running')

        # Wait for for the empty db to be created and quorum established on
        # this single db server for each database type. The database servers
        # create emtpy prdb and vldb databases as side-effect of these queries,
        # including the creation of the initial ubik database versions.
        pts('listentries', retry=10)
        vos('listvldb', retry=10)

        # Create the superusers and add them to this first server's userlist.
        for admin in self.admins:
            self._create_admin(admin)
            self.primary_db.adduser(admin)

    def _add_db_servers(self):
        """Setup the remaining database servers."""
        logger.info("Setting up additional database servers.")

        # Shutdown the primary server since we are changing the
        # cell hosts on it.
        for dbname in DBNAMES:
            self.primary_db.shutdown(dbname)
            self.primary_db.wait_for_status(dbname, target='shutdown')
        time.sleep(1)

        # Set the cell hosts on all the db servers, including the primary.
        # Be sure keep the order of the hosts consistent, since that is
        # the normal setup.
        for host in self.db:
            host.setcellname(self.cell)
            host.setcellhosts([self.primary_db])
            host.setcellhosts(self.db)

        # Restart the primary and create the other database hosts.
        # Use udebug to verify quorum is established.
        for dbname in DBNAMES:
            self.primary_db.restart(dbname)
            self.primary_db.wait_for_status(dbname, target='running')
            for host in self.db:
                if host != self.primary_db:
                    for admin in self.admins:
		        host.adduser(admin)
                    host.create_database(dbname, self.options)
                    host.wait_for_status(dbname, target='running')

        logger.info("Waiting for quorum.")
        time.sleep(15)
        for dbname in DBNAMES:
            self._wait_for_quorum(dbname)

    def _add_fs_servers(self):
        """Add remaining file servers."""
        for server in self.fs:
            if server != self.primary_fs:
                self.add_fileserver(server)

    def _setup_first_fs_server(self):
        """Startup the file server processes and create the root volumes if needed."""
        logger.info("Setting up the first file server.")
        if self.primary_fs != self.primary_db:
            self.primary_db.setcellname(self.cell)
            self.primary_db.setcellhosts([self.primary_db])
            for admin in self.admins:
                self.primary_fs.adduser(admin)

        bnode = _optfsbnode(self.options)
        self.primary_fs.create_fileserver(bnode, self.options)
        self.primary_fs.wait_for_status(bnode, target='running')

        # Note: root.afs must exist before non-dynroot clients are started.
        self.primary_fs.create_volume('root.afs')
        self.primary_fs.create_volume('root.cell')

    def newcell(self):
        """Setup a new cell."""
        logger.info("Setting up new cell.")
        self.ping_hosts()
        self._setup_first_db_server()
        self._setup_first_fs_server()
        if len(self.db) > 1:
            self._add_db_servers()
        if len(self.fs) > 1:
            self._add_fs_servers()

    def add_fileserver(self, host):
        """Add a fileserver to this cell.

        The remote host must have the binaries installed, the service key
        installed, the bosserver started.  This function will setup the
        cell name, the CellServDB configuration, add the superuser names,
        and then create the bosserver configuration to run the fileserver.
        """
        if isinstance(host, basestring):
            host = Host(host)
        logger.info("Adding fileserver %s", host.hostname)
        host.setcellname(self.cell)
        host.setcellhosts(self.db)
        for admin in self.admins:
            host.adduser(admin)
        bnode = _optfsbnode(self.options)
        host.create_fileserver(bnode, self.options)

    def mount_root_volumes(self, dynroot):
        """Mount, setup acls, and replicate the root.afs and root.cell volumes.

        dynroot: True if the cache manager was started with -dynroot or -dynroot-sparse.

        Note: It would be nice if dynroot mode could be could be detected, but the OpenAFS
              cache manager does not provide a way to do so at this time.

        Preconditions:
        1. The root.afs and root.cell volumes must exist.
        2. The cache manager must be running, with or without -dynroot.
        3. An token with admin privileges has been acquired.

        Post-conditions:
        1. The root.afs.readonly and root.cell.readonly volumes exist.
        2. The path /afs/<cellname> resolves to the root.cell.readonly root vnode.
        3. The path /afs/.<cellname> resolves to the root.cell root vnode.
        4. The path /afs/.<cellname>/.afs resolves to the root.afs root vnode.

        If the cache manager is currently running in dynroot mode, the special
        /afs/.<cellname>/.afs mount point is created first, in order to
        reach the root.afs vnode to add cell mount points.

        If the cache manager is not currently running in dynroot mode, the
        special /afs/.<cellname>/.afs mount point is created first anyway
        in case it is needed later when dynroot is turned on, on this client or
        others.

        Note: In the past, this function attempted to create the cellular mount
        point using the magic '.:mount' path when the cache manager was running
        in dynroot mode.  However we found this did not work on Solaris unless
        the -fakestat option was also given. This is arguably an OpenAFS bug.
        """
        # First, verify AFS is mounted and find the mount point to it, e.g., /afs
        afs = afs_mountpoint()
        if afs is None:
            raise AssertionError("Unable to mount volumes; afs is not mounted!")

        # Verify the cache manager's cell matches the name of the cell
        # being setup. This mismatch can happen if the cache manager's ThisCell
        # and/or CellServDB files were not created correctly before the cache
        # was started.
        cell = self._wscell()
        if cell != self.cell:
            raise AssertionError("Client side ThisCell file does not match the cell name!")

        def _mount(path, volume, *opts):
            if not os.path.exists(path):
                msg = ' as read-write' if '-rw' in opts else ''
                logger.info("Mounting '%s' on path '%s'%s.", volume, path, msg)
                fs('mkmount', '-dir', path, '-vol', volume, *opts)

        if not dynroot:
            _mount("%(afs)s/%(cell)s" % locals(), 'root.cell', '-cell', cell)
            _mount("%(afs)s/.%(cell)s" % locals(), 'root.cell', '-cell', cell, '-rw')
            _mount("%(afs)s/.%(cell)s/.afs" % locals(), 'root.afs', '-rw') # for dynroot clients
        else:
            _mount("%(afs)s/.%(cell)s/.afs" % locals(), 'root.afs', '-rw')
            _mount("%(afs)s/.%(cell)s/.afs/%(cell)s" % locals(), 'root.cell', '-cell', cell)
            _mount("%(afs)s/.%(cell)s/.afs/.%(cell)s" % locals(), 'root.cell', '-cell', cell, '-rw')

        # Grant global read and list rights to the root /afs and /afs/<cell> paths.
        if not dynroot:
            fs('setacl', '-dir', "%(afs)s" % locals(), '-acl', 'system:anyuser', 'read')
            fs('setacl', '-dir', "%(afs)s/.%(cell)s" % locals(), '-acl', 'system:anyuser', 'read')
        else:
            fs('setacl', '-dir', "%(afs)s/.%(cell)s/.afs" % locals(), '-acl', 'system:anyuser', 'read')
            fs('setacl', '-dir', "%(afs)s/.%(cell)s" % locals(), '-acl', 'system:anyuser', 'read')

        # Replicate our root volumes.
        self._create_replica('root.afs')
        self._create_replica('root.cell')
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
            self.primary_fs.create_volume(name)
            self._mount(root_cell_rw, name, name)
            fs('setacl', '-dir', os.path.join(root_cell_rw, name), '-acl', 'system:anyuser', 'read')
            self._create_replica(name)
        vos('release', '-id', 'root.cell')
        fs('checkvolumes')

