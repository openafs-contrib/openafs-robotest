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
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn
from robot.libraries.BuiltIn import register_run_keyword

from libraries.dump import VolumeDump

class _Linux:
    def get_modules(self):
        """Return loaded kernel module names."""
        modules = []
        f = open("/proc/modules", "r")
        for line in f.readlines():
            module = line.split()[0]
            modules.append(module)
        f.close()
        return modules

    def unload_module(self, name):
        """Unload the kernel module."""
        _run_keyword("Sudo", "rmmod", name)

class _Solaris:
    def _get_kernel_modules(self):
        """Return loaded kernel module names and ids."""
        modules = {}
        pipe = os.popen("/usr/sbin/modinfo -w")
        for line in pipe.readlines():
            if line.lstrip().startswith("Id"):
                continue # skip header line
            # Fields are: Id Loadaddr Size Info Rev Module Name (Desc)
            m = re.match(r'\s*(\d+)\s+\S+\s+\S+\s+\S+\s+\d+\s+(\S+)', line)
            if m:
                id = m.group(1)
                name = m.group(2)
                modules[name] = id  # remove duplicate entries
            else:
                raise AssertionError("Unexpected modinfo output: %s" % (line))
        pipe.close()
        return modules

    def get_modules(self):
        """Return loaded kernel module names."""
        return self._get_kernel_modules().keys()

    def unload_module(self, name):
        """Unload the kernel module."""
        modules = self._get_kernel_modules()
        if name in modules:
            _run_keyword("Sudo", "modunload", "-i", modules[name])


class _Util:
    """Generic helper keywords."""

    def __init__(self):
        uname = os.uname()[0]
        if uname == "Linux":
            self._os = _Linux()
        elif uname == "SunOS":
            self._os = _Solaris()
        else:
            raise AssertionError("Unsupported operating system: %s" % (uname))

    def get_host_by_name(self, hostname):
        """Return the ipv4 address of the hostname."""
        return socket.gethostbyname(hostname)

    def get_device(self, path):
        """Return the device id of the given path as '(major,minor)'."""
        device = os.stat(path).st_dev
        return "(%d,%d)" % (os.major(device), os.minor(device))

    def get_modules(self):
        """Return a list of loaded kernel module names."""
        return self._os.get_modules()

    def unload_module(self, name):
        """Unloade the kernel module."""
        return self._os.unload_module(name)

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

class _Dump:
    """OpenAFS volume dump keywords."""

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
    _stage_filename = 'site/.stage' # Where the last completed stage name is saved.

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
        if not _get_var('AFS_DIST') in ('transarc', 'rhel6', 'suse'):
            raise AssertionError("Unsupported AFS_DIST: %s" % _get_var('AFS_DIST'))
        _run_keyword("Required Variables Should Not Be Empty")
        if _get_var('AFS_DIST') == 'transarc':
            _run_keyword("Transarc Variables Should Exist")
        _run_keyword("Host Address Should Not Be Loopback")
        _run_keyword("OpenAFS Servers Should Not Be Running")
        _run_keyword("AFS Filesystem Should Not Be Mounted")
        _run_keyword("OpenAFS Kernel Module Should Not Be Loaded")
        _run_keyword("OpenAFS Installation Directories Should Not Exist")
	_run_keyword("Cache Partition Should Be Empty")
        for id in ['a']:
            _run_keyword("Vice Partition Should Be Empty", id)
            _run_keyword("Vice Partition Should Be Attachable", id)
        if _get_var('AFS_CSDB_DIST'):
            _run_keyword("CellServDB.dist Should Exist")
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
            if uname == "Linux":
                _run_keyword("Install Init Script on Linux")
            elif uname == "SunOS":
                _run_keyword("Install Init Script on Solaris")
            else:
                raise AssertionError("Unsupported operating system: %s" % (uname))
        elif dist in ('rhel6', 'suse'):
            _run_keyword("Install OpenAFS Server RPM Files")
            _run_keyword("Install OpenAFS Client RPM Files")
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
        _run_keyword("Set the Cell Configuration")
        _run_keyword("Create Database Service", "ptserver", 7002)
        _run_keyword("Create Database Service", "vlserver", 7003)
        if _get_var('AFS_DAFS'):
            _run_keyword("Create Demand Attach File Service")
        else:
            _run_keyword("Create File Service")
        _run_keyword("Create an Admin Account", _get_var('AFS_ADMIN'))
        _run_keyword("Create the root.afs Volume")
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
        _run_keyword("Login",  _get_var('AFS_ADMIN'))
        _run_keyword("Create Volume",  hostname, "a", "root.cell")
        _run_keyword("Mount Cell Root Volume")
        _run_keyword("Replicate Volume", hostname, "a", "root.afs")
        _run_keyword("Replicate Volume", hostname, "a", "root.cell")

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
        else:
            _run_keyword("Remove OpenAFS RPM Packages")

    @_teardown_stage
    def purge_files(self):
        """Remove remnant data and configuration files."""
        _run_keyword("Purge Server Configuration")
        _run_keyword("Purge Cache Manager Configuration")
        valid = r'/vicep([a-z]|[a-h][a-z]|i[a-v])$'
        for vicep in glob.glob("/vicep*"):
            if re.match(valid, vicep) and os.path.isdir(vicep):
                _run_keyword("Purge Volumes On Partition", vicep)

    def _setup_service_key(self):
        """Helper method to setup the AFS service key.

        Call the correct keyword depending on which key file is being setup in
        the test cell. Supported types are the lecacy DES KeyFile, the interim
        rxkad-k5 non-DES enctype, and the modern non-DES KeyFileExt.
        """
        if _get_var('AFS_KEY_FILE') == 'KeyFile':
            _run_keyword("Create Key File")
        elif _get_var('AFS_KEY_FILE') == 'rxkad.keytab':
            _run_keyword("Install rxkad-k5 Keytab")
        elif _get_var('AFS_KEY_FILE') == 'KeyFileExt':
            _run_keyword("Create Extended Key File", _get_var('KRB_AFS_ENCTYPE'))
        else:
            raise AssertionError("Unsupported AFS_KEY_FILE! %s" % (_get_var('AFS_KEY_FILE')))

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
            raise AssertionError("Invalid stage name '%s' in file '%s'" % (last, self._stage_filename))
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
            f = open(self._stage_filename, "r")
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
            f = open(self._stage_filename, "w")
            f.write("%s\n" % stage)
            f.close()
            logger.debug("set stage: %s" % (stage))
        except:
            raise AssertionError("Unable to save setup/teardown stage! %s" % (sys.exc_info()[0]))
        return stage


class OpenAFS(_Util, _Dump, _Setup):
    """OpenAFS test library for basic tests.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'


# Helpers

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
