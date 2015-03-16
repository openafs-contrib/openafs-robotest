# Copyright (c) 2014-2015, Sine Nomine Associates
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

import sys
import os
import re
import glob
import socket
import shlex
import subprocess
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn
from robot.libraries.BuiltIn import register_run_keyword

from libraries.dump import VolumeDump
from libraries.acl import AccessControlList
from libraries.system import System
from libraries.rpm import Rpm

class _Util:
    """Generic helper keywords."""

    def __init__(self):
        self.system = System.current()

    def run_program(self, cmd_line):
        rc = _run_program(cmd_line)
        if rc:
            raise AssertionError("Program failed: '%s', exit code='%d'" % (cmd_line, rc))

    def sudo(self, cmd, *args):
        # Run a command as root.
        self.system.sudo(cmd, *args)

    def get_host_by_name(self, hostname):
        """Return the ipv4 address of the hostname."""
        return socket.gethostbyname(hostname)

    def get_device(self, path):
        """Return the device id of the given path as '(major,minor)'."""
        device = os.stat(path).st_dev
        return "(%d,%d)" % (os.major(device), os.minor(device))

    def get_modules(self):
        """Return a list of loaded kernel module names."""
        return self.system.get_modules()

    def unload_module(self, name):
        """Unload the kernel module."""
        return self.system.unload_module(name)

    def get_interfaces(self):
        """Find the non-loopback IPv4 addresses of the network interfaces."""
        return self.system.get_interfaces()

    def _get_crash_count(self):
        count = 0
        last = ""
        filename = "%s/BosLog" % _get_var('AFS_LOGS_DIR')
        log = open(filename, "r")
        for line in log.readlines():
            if 'core dumped' in line:
                last = line
                count += 1
        log.close()
        return (count, last)

    def init_crash_check(self):
        (count, last) = self._get_crash_count()
        BuiltIn().set_suite_variable('${CRASH_COUNT}', count)
        BuiltIn().set_suite_variable('${CRASH_LAST}', last)

    def crash_check(self):
        before = _get_var('CRASH_COUNT')
        (after, last) = self._get_crash_count()
        if after != before:
            raise AssertionError("Server crash detected! %s" % last)

    def directory_entry_should_exist(self, path):
        """Fails if directory entry does not exist in the given path."""
        base = os.path.basename(path)
        dir = os.path.dirname(path)
        if not base in os.listdir(dir):
            raise AssertionError("Directory entry '%s' does not exist in '%s'" % (base, dir))

class _Login:

    def _principal(self, user, realm):
        # Convert OpenAFS k4 style names to k5 style principals.
        return "%s@%s" %  (user.replace('.', '/'), realm)

    def login(self, user=None):
        if user is None:
            user = _get_var('AFS_ADMIN')
        if _get_var('AFS_AKIMPERSONATE'):
            self.akimpersonate(user)
        else:
            self.login_with_keytab(user)

    def logout(self):
        if not _get_var('AFS_AKIMPERSONATE'):
            site = _get_var('SITE')
            kdestroy = _get_var('KDESTROY')
            krb5cc = os.path.join(site, "krb5cc")
            cmd = "KRB5CCNAME=%s %s" % (krb5cc, kdestroy)
            rc = _run_program(cmd)
            if rc:
                raise AssertionError("kdestroy failed: '%s'; exit code = %d" % (cmd, rc))
        unlog = _get_var('UNLOG')
        rc = _run_program(unlog)
        if rc:
            raise AssertionError("unlog failed: '%s'; exit code = %d" % (unlog, rc))

    def akimpersonate(self, user):
        if not user:
            raise AsseritionError("User name is required")
        aklog = _get_var('AKLOG')
        cell = _get_var('AFS_CELL')
        realm = _get_var('KRB_REALM')
        keytab = _get_var('KRB_AFS_KEYTAB')
        principal = self._principal(user, realm)
        cmd = "%s -d -c %s -k %s -keytab %s -principal %s" % (aklog, cell, realm, keytab, principal)
        rc = _run_program(cmd)
        if rc:
            raise AssertionError("aklog failed: '%s'; exit code = %d" % (cmd, rc))

    def login_with_keytab(self, user):
        if not user:
            raise AsseritionError("User name is required")
        site = _get_var('SITE')
        kinit = _get_var('KINIT')
        aklog = _get_var('AKLOG')
        cell = _get_var('AFS_CELL')
        realm = _get_var('KRB_REALM')
        principal = self._principal(user, realm)
        if user == _get_var('AFS_USER'):
            keytab = _get_var('KRB_USER_KEYTAB')
        elif user == _get_var('AFS_ADMIN'):
            keytab = _get_var('KRB_ADMIN_KEYTAB')
        else:
            raise AssertionError("No keytab found for user '%s'." % user)
        if not keytab:
            raise AssertionError("Keytab not set for user '%s'." % user)
        logger.info("keytab: " + keytab)
        if not os.path.exists(keytab):
            raise AsseritionError("Keytab file '%s' is missing." % keytab)
        if not os.path.isdir(site):
            raise AsseritionError("SITE directory '%s' is missing." % site)
        krb5cc = os.path.join(site, "krb5cc")
        cmd = "KRB5CCNAME=%s %s -5 -k -t %s %s" % (krb5cc, kinit, keytab, principal)
        rc = _run_program(cmd)
        if rc:
            raise AssertionError("kinit failed: '%s'; exit code = %d" % (cmd, rc))
        cmd = "KRB5CCNAME=%s %s -d -c %s -k %s" % (krb5cc, aklog, cell, realm)
        rc = _run_program(cmd)
        if rc:
            raise AssertionError("kinit failed: '%s'; exit code = %d" % (cmd, rc))

class _Dump:
    """Volume dump keywords."""

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

class _ACL:
    """ACL testing keywords."""

    def access_control_list_matches(self, path, *acls):
        """Fails if a directory ACL does not match the given ACL."""
        logger.debug("access_control_list_matches: path=%s, acls=[%s]" % (path, ",".join(acls)))
        a1 = AccessControlList.from_path(path)
        a2 = AccessControlList.from_args(*acls)
        logger.debug("a1=%s" % a1)
        logger.debug("a2=%s" % a2)
        if a1 != a2:
            raise AssertionError("ACLs do not match: path=%s args=%s" % (a1, a2))

    def access_control_list_contains(self, path, name, rights):
        logger.debug("access_control_list_contains: path=%s, name=%s, rights=%s" % (path, name, rights))
        a = AccessControlList.from_path(path)
        if not a.contains(name, rights):
            raise AssertionError("ACL entry rights do not match for name '%s'")

    def access_control_should_exist(self, path, name):
        """Fails if the access control does not exist for the the given user or group name."""
        logger.debug("access_control_should_exist: path=%s, name=%s, rights=%s" % (path, name, rights))
        a = AccessControlList.from_path(path)
        if name not in a.acls:
            raise AssertionError("ACL entry does not exist for name '%s'" % (name))

    def access_control_should_not_exist(self, path, name):
        """Fails if the access control exists for the the given user or group name."""
        logger.debug("access_control_should_not_exist: path=%s, name=%s" % (path, name))
        a = AccessControlList.from_path(path)
        if name in a.acls:
            raise AssertionError("ACL entry exists for name '%s'" % (name))

class _Setup:
    """Test system setup and teardown top-level keywords.

    This library provides keywords to install the OpenAFS server and
    client on a single system, create a small test cell, and then
    tear it down for the next test cycle.

    The DO_TEARDOWN setting my be set to False to skip the teardown
    keywords.  The setup keywords will be skipped on the next test
    cycle.  This maybe helpful during test development to avoid lengthy
    setup and teardowns when the software and setup under test is not
    changed.

    Implementation of many of the setup and teardown steps are provided
    in external robot resource files.  This library determines which
    keywords are called based on the settings and saved state.
    """

    def _setup_stage(method):
        """Setup keyword wrapper to manage the order of setup stages."""
        def decorator(self):
            name = method.func_name
            if self._should_run_stage(name):
                _say("Setup.%s" % name)
                method(self)
                self._set_stage(name)
        return decorator

    def _teardown_stage(method):
        """Teardown keyword wrapper to manage the order of teardown stages."""
        def decorator(self):
            if _get_var('DO_TEARDOWN') == False:
                # Do not change the stage so the setup is skipped the
                # next time the tests harness is run.
                logger.info("Skipping Teardown: DO_TEARDOWN is False")
            else:
                name = method.func_name
                if self._should_run_stage(name):
                    _say("Teardown.%s" % name)
                    method(self)
                    self._set_stage(name)
        return decorator

    @_setup_stage
    def precheck_system(self):
        """Verify system prerequisites are met."""
        _run_keyword("Non-interactive sudo is Required")
        if not _get_var('AFS_DIST') in ('transarc', 'rhel6', 'suse'):
            raise AssertionError("Unsupported AFS_DIST: %s" % _get_var('AFS_DIST'))
        _run_keyword("Required Variables Should Not Be Empty")
        if _get_var('AFS_DIST') == 'transarc':
            _run_keyword("Transarc Variables Should Exist")
        _run_keyword("Host Address Should Not Be Loopback")
        _run_keyword("Network Interface Should Have The Host Address")
        _run_keyword("OpenAFS Servers Should Not Be Running")
        _run_keyword("AFS Filesystem Should Not Be Mounted")
        _run_keyword("OpenAFS Kernel Module Should Not Be Loaded")
        _run_keyword("OpenAFS Installation Directories Should Not Exist")
        if os.path.exists(_get_var('AFS_CACHE_DIR')):
            _run_keyword("Cache Partition Should Be Empty")
        for id in ['a']:
            _run_keyword("Vice Partition Should Be Empty", id)
            _run_keyword("Vice Partition Should Be Attachable", id)
        if _get_var('AFS_CSDB_DIST'):
            _run_keyword("CellServDB.dist Should Exist")
        if _get_var('AFS_AKIMPERSONATE') == False:
            _run_keyword("Kerberos Client Must Be Installed")
            _run_keyword("Service Keytab Should Exist",
                _get_var('KRB_AFS_KEYTAB'), _get_var('AFS_CELL'), _get_var('KRB_REALM'),
                _get_var('KRB_AFS_ENCTYPE'), _get_var('AFS_KEY_FILE'))
            _run_keyword("Kerberos Keytab Should Exist", _get_var('KRB_USER_KEYTAB'),
                "%s" % _get_var('AFS_USER').replace('.','/'), _get_var('KRB_REALM'))
            _run_keyword("Kerberos Keytab Should Exist", _get_var('KRB_ADMIN_KEYTAB'),
                "%s" % _get_var('AFS_ADMIN').replace('.','/'), _get_var('KRB_REALM'))
            _run_keyword("Can Get a Kerberos Ticket", _get_var('KRB_USER_KEYTAB'),
                "%s" % _get_var('AFS_USER').replace('.','/'), _get_var('KRB_REALM'))

    @_setup_stage
    def install_openafs(self):
        """Install the OpenAFS client and server binaries."""
        if _get_var('DO_INSTALL') == False:
            logger.info("Skipping install: DO_INSTALL is False")
            return
        uname = os.uname()[0]
        dist = _get_var('AFS_DIST')
        if dist == "transarc":
            if _get_var('TRANSARC_TARBALL'):
                _run_keyword("Untar Binaries")
            _run_keyword("Install Server Binaries")
            _run_keyword("Install Client Binaries")
            _run_keyword("Install Workstation Binaries")
            _run_keyword("Install Shared Libraries")
            if uname == "Linux":
                _run_keyword("Install Init Script on Linux")
            elif uname == "SunOS":
                _run_keyword("Install Init Script on Solaris")
            else:
                raise AssertionError("Unsupported operating system: %s" % (uname))
        elif dist in ('rhel6', 'suse'):
            rpm = Rpm.current()
            _run_keyword("Install RPM Files", *rpm.get_server_rpms())
            _run_keyword("Install RPM Files", *rpm.get_client_rpms())
        else:
            raise AssertionError("Unsupported AFS_DIST: %s" % (dist))

    @_setup_stage
    def create_test_cell(self):
        """Create the OpenAFS test cell."""
        hostname = socket.gethostname()
        if _get_var('KRB_REALM').lower() != _get_var('AFS_CELL').lower():
            _run_keyword("Set Kerberos Realm Name", _get_var('KRB_REALM'))
        _run_keyword("Set Machine Interface")
        self._setup_service_key()
        if _get_var('AFS_DIST') == "transarc":
            _run_keyword("Start the bosserver")
        else:
            _run_keyword("Start Service", "openafs-server")
        _run_keyword("Set the Cell Name", _get_var('AFS_CELL'))
        self._remove_symlinks_created_by_bosserver()
        _run_keyword("Create Database Service", "ptserver", 7002)
        _run_keyword("Create Database Service", "vlserver", 7003)
        if _get_var('AFS_DAFS'):
            _run_keyword("Create Demand Attach File Service")
        else:
            _run_keyword("Create File Service")
        _run_keyword("Create an Admin Account", _get_var('AFS_ADMIN'))
        _run_keyword("Create the root.afs Volume")
        if _get_var('AFS_CSDB_DIST'):
            _run_keyword("Append CellServDB.dist")
        _run_keyword("Create AFS Mount Point")
        _run_keyword("Set Cache Manager Configuration")
        if _get_var('AFS_DIST') == "transarc":
            uname = os.uname()[0]
            if uname == 'Linux':
                _run_keyword("Start the Cache Manager on Linux")
            elif uname == 'SunOS':
                _run_keyword("Start the Cache Manager on Solaris")
            else:
                raise AssertionError("Unsupported operating system: %s" % (uname))
        else:
            _run_keyword("Start Service", "openafs-client")
        _run_keyword("Cell Should Be", _get_var('AFS_CELL'))
        _Login().login(_get_var('AFS_ADMIN'))
        _run_keyword("Create Volume",  hostname, "a", "root.cell")
        _run_keyword("Mount Cell Root Volume")
        _run_keyword("Create and Mount Volume", hostname, "a", "test", "/afs/%s/test" % _get_var('AFS_CELL'))
        _run_keyword("Replicate Volume", hostname, "a", "root.afs")
        _run_keyword("Replicate Volume", hostname, "a", "root.cell")
        _Login().logout()

    @_teardown_stage
    def shutdown_openafs(self):
        """Shutdown the OpenAFS client and servers."""
        if _get_var('AFS_DIST') == "transarc":
            uname = os.uname()[0]
            if uname == 'Linux':
                _run_keyword("Stop the Cache Manager on Linux")
            elif uname == 'SunOS':
                _run_keyword("Stop the Cache Manager on Solaris")
            else:
                raise AssertionError("Unsupported operating system: %s" % (uname))
            _run_keyword("Stop the bosserver")
        else:
            _run_keyword("Stop Service", "openafs-client")
            _run_keyword("Stop Service", "openafs-server")

    @_teardown_stage
    def remove_openafs(self):
        """Remove the OpenAFS server and client binaries."""
        if _get_var('DO_REMOVE') == False:
            logger.info("Skipping remove: DO_REMOVE is False")
            return
        if _get_var('AFS_DIST') == "transarc":
            _run_keyword("Remove Server Binaries")
            _run_keyword("Remove Client Binaries")
            _run_keyword("Remove Workstation Binaries")
            _run_keyword("Remove Shared Libraries Binaries")
        else:
            _run_keyword("Remove OpenAFS RPM Packages")

    @_teardown_stage
    def purge_files(self):
        """Remove remnant data and configuration files."""
        _run_keyword("Purge Server Configuration")
        _run_keyword("Purge Cache Manager Configuration")
        # TODO: Probably the only sane way to do this is to call
        #       a helper script which runs as root.
        # _run_keyword("Purge Cache")
        valid = r'/vicep([a-z]|[a-h][a-z]|i[a-v])$'
        for vicep in glob.glob("/vicep*"):
            if re.match(valid, vicep) and os.path.isdir(vicep):
                _run_keyword("Purge Directory", "%s/AFSIDat" % vicep)
                _run_keyword("Purge Directory", "%s/Lock" % vicep)
                for vheader in glob.glob("%s/V*.vol" % vicep):
                    _run_keyword("Sudo", "rm -f %s" % vheader)

    def _setup_service_key(self):
        """Helper method to setup the AFS service key.

        Create a dummy keytab file when running in akimpersonate mode.

        Call the correct keyword depending on which key file is being setup in
        the test cell. Supported types are the lecacy DES KeyFile, the interim
        rxkad-k5 non-DES enctype, and the modern non-DES KeyFileExt.
        """
        if _get_var('AFS_AKIMPERSONATE') and not os.path.exists(_get_var('AFS_KEY_FILE')):
            _run_keyword("Create Akimpersonate Keytab")
        if _get_var('AFS_KEY_FILE') == 'KeyFile':
            _run_keyword("Create Key File")
        elif _get_var('AFS_KEY_FILE') == 'rxkad.keytab':
            _run_keyword("Install rxkad-k5 Keytab")
        elif _get_var('AFS_KEY_FILE') == 'KeyFileExt':
            _run_keyword("Create Extended Key File", _get_var('KRB_AFS_ENCTYPE'))
        else:
            raise AssertionError("Unsupported AFS_KEY_FILE! %s" % (_get_var('AFS_KEY_FILE')))

    def _remove_symlinks_created_by_bosserver(self):
        """Remove the symlinks to the CellServDB and ThisCell files
        created by the bosserver and replace them with regular files.

        This is a workaround step which is needed to support RPM packages.
        The init scripts provided by the RPMs can inadvertently overwrite
        the server's CellServDB when the client side CellServDB is a symlink.

        It is not sufficient to just remove the symlinks. The client side
        configuration is needed by vos and pts, which are used to setup the
        cell before the client is started.

        So, remove the symlinked CSDB and ThisCell, and replace with copies
        from the server configuration directory.
        """
        afs_conf_dir = _get_var('AFS_CONF_DIR')    # e.g. /usr/afs/etc
        afs_data_dir = _get_var('AFS_DATA_DIR')    # e.g. /usr/vice/etc
        if afs_conf_dir is None or afs_conf_dir == "":
            raise AssertionError("AFS_CONF_DIR is not set!")
        if afs_data_dir is None or afs_data_dir == "":
            raise AssertionError("AFS_DATA_DIR is not set!")
        if not os.path.exists(afs_data_dir):
            _run_keyword("Sudo", "mkdir -p %s" % (afs_data_dir))
        if os.path.islink("%s/CellServDB" % (afs_data_dir)):
            _run_keyword("Sudo", "rm", "-f", "%s/CellServDB" % (afs_data_dir))
        if os.path.islink("%s/ThisCell" % (afs_data_dir)):
            _run_keyword("Sudo", "rm", "-f", "%s/ThisCell" % (afs_data_dir))
        _run_keyword("Sudo", "cp", "%s/CellServDB" % (afs_conf_dir), "%s/CellServDB.local" % (afs_data_dir))
        _run_keyword("Sudo", "cp", "%s/CellServDB" % (afs_conf_dir), "%s/CellServDB" % (afs_data_dir))
        _run_keyword("Sudo", "cp", "%s/ThisCell" % (afs_conf_dir), "%s/ThisCell" % (afs_data_dir))


    def _should_run_stage(self, stage):
        """Returns true if this stage should be run."""
        sequence = ['', # initial condition
                    'precheck_system',  'install_openafs', 'create_test_cell',
                    'shutdown_openafs', 'remove_openafs',  'purge_files']
        last = self._get_stage()
        if last == sequence[-1]:
            last = sequence[0] # next cycle
        if not stage in sequence[1:]:
            raise AssertionError("Internal error: invalid stage name '%s'" % stage)
        if not last in sequence:
            filename = os.path.join(_get_var('SITE'), ".stage")
            raise AssertionError("Invalid stage name '%s' in file '%s'" % (last, filename))
        if sequence.index(stage) <= sequence.index(last):
            logger.info("Skipping %s; already done" % (stage))
            return False
        if sequence.index(stage) != sequence.index(last) + 1:
            logger.info("Skipping %s; out of sequence! last stage was '%s'" % (stage, last))
            return False
        return True

    def _get_stage(self):
        """Get the last setup/teardown stage which was completed."""
        try:
            filename = os.path.join(_get_var('SITE'), ".stage")
            f = open(filename, "r")
            stage = f.readline().strip()
            f.close()
            logger.debug("get stage: %s" % (stage))
            return stage
        except:
            return self._reset_stage()

    def _reset_stage(self):
        """Reset the last stage to the initial state."""
        return self._set_stage('')

    def _set_stage(self, stage):
        """Set the last setup/teardown stage completed."""
        try:
            filename = os.path.join(_get_var('SITE'), ".stage")
            f = open(filename, "w")
            f.write("%s\n" % stage)
            f.close()
            logger.debug("set stage: %s" % (stage))
        except:
            raise AssertionError("Unable to save setup/teardown stage! %s" % (sys.exc_info()[0]))
        return stage


class OpenAFS(_Util, _Login, _Dump, _ACL, _Setup):
    """OpenAFS test library for basic tests.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'


# Helpers

def _run_program(cmd):
    logger.info("running: %s" % cmd)
    proc = subprocess.Popen(cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = proc.communicate()
    if proc.returncode:
        logger.info("output: " + output)
        logger.info("error:  " + error)
    return proc.returncode

def _say(msg):
    """Display a progress message to the console."""
    stream = sys.__stdout__
    stream.write("%s\n" % (msg))
    stream.flush()

def _run_keyword(name, *args):
    """Run the named keyword."""
    BuiltIn().run_keyword(name, *args)

def _get_var(name):
    """Return the named variable value or None if it does not exist."""
    return BuiltIn().get_variable_value("${%s}" % name)

def _lookup_keywords(filename):
    """Lookup the keyword names in the given resource file."""
    keywords = []
    start_of_table = r'\*+\s+'
    start_of_kw_table = r'\*+\s+Keyword'
    in_kw_table = False
    f = open(filename, "r")
    for line in f.readlines():
        line = line.rstrip()
        if len(line) == 0 or line.startswith("#"):
            continue  # skip comments and blanks
        if re.match(start_of_kw_table, line):
            in_kw_table = True   # table started
            continue
        if re.match(start_of_table, line) and not re.match(start_of_kw_table, line):
            in_kw_table = False  # table ended
            continue
        if line.startswith(' '):
            continue  # skip content rows
        if in_kw_table:
            keywords.append(line)
    f.close()
    return keywords

def _register_keywords():
    """Register the keywords in all of the resource files."""
    for filename in glob.glob('./resources/*.robot'):
        keywords = _lookup_keywords(filename)
        for keyword in keywords:
            register_run_keyword(filename, keyword, 0)

_register_keywords()

