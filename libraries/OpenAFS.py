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

import settings

# Setup and teardown stages.
_STAGE_INITIAL = 0
_STAGE_PRECHECK_SYSTEM = 1
_STAGE_INSTALL_OPENAFS = 2
_STAGE_CREATE_TEST_CELL = 3
_STAGE_SHUTDOWN_OPENAFS = 4
_STAGE_REMOVE_OPENAFS = 5
_STAGE_PURGE_FILES = 6

def _say(msg):
    """Display a progress message to the console."""
    stream = sys.__stdout__
    stream.write("%s\n" % (msg))
    stream.flush()

def _run_keyword(name, *args):
    """Run the named keyword."""
    BuiltIn().run_keyword(name, *args)


class OpenAFS:
    """OpenAFS test library for basic tests.

    This library provides keywords to install the OpenAFS server and
    client on a single system, create a small test cell, and then
    tear it all down for the next test cycle.

    The DO_TEARDOWN setting my be set to False to skip the teardown
    keywords.  The setup keywords will be skipped on the next test
    cycle.  This maybe helpful during test development to avoid lengthy
    setup and teardowns when the software and setup under test is not
    changed.

    Implementation of many of the setup steps are provided in external
    robot resource files.  This library determines which keywords
    are called based on the configuration.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self):
        self._stage = _Stage()

    def file_should_be_executable(self, path):
        """Fails if the file does not have execute permissions for the current user."""
        if not path:
            raise AssertionError("path arg is empty")
        if not os.path.isfile(path):
            raise AssertionError("path arg is not a file: %s" % (path))
        if not os.access(path, os.X_OK):
            raise AssertionError("File is not executable: %s" % (path))

    def get_host_by_name(self, hostname):
       """Return the ipv4 address of the hostname."""
       return socket.gethostbyname(hostname)

    def get_device(self, path):
        """Return the device id of the given path as '(major,minor)'."""
        device = os.stat(path).st_dev
        return "(%d,%d)" % (os.major(device), os.minor(device))

    def precheck_system(self):
        """Verify system prerequisites are met."""
        self._stage.check(_STAGE_PRECHECK_SYSTEM, self._precheck_system)

    def install_openafs(self):
        """Install the OpenAFS client and server binaries."""
        self._stage.check(_STAGE_INSTALL_OPENAFS, self._install_openafs)

    def create_test_cell(self):
        """Create the OpenAFS test cell."""
        self._stage.check(_STAGE_CREATE_TEST_CELL, self._create_test_cell)

    def shutdown_openafs(self):
        """Shutdown the OpenAFS client and servers."""
        self._stage.check(_STAGE_SHUTDOWN_OPENAFS, self._shutdown_openafs)

    def remove_openafs(self):
        """Remove the OpenAFS server and client binaries."""
        self._stage.check(_STAGE_REMOVE_OPENAFS, self._remove_openafs)

    def purge_files(self):
        """Remove remnant data and configuration files."""
        self._stage.check(_STAGE_PURGE_FILES, self._purge_files)

    def _precheck_system(self):
        _run_keyword("Required Variables Should Not Be Empty")
        if settings.AFS_DIST == 'transarc':
            _run_keyword("Transarc Variables Should Exist")
        _run_keyword("Host Address Should Not Be Loopback")
        _run_keyword("OpenAFS Servers Should Not Be Running")
        _run_keyword("AFS Filesystem Should Not Be Mounted")
        _run_keyword("OpenAFS Kernel Module Should Not Be Loaded")
        _run_keyword("OpenAFS Installation Directories Should Not Exist")
        for id in ['a']:
            _run_keyword("Vice Partition Should Be Empty", id)
            _run_keyword("Vice Partition Should Be Attachable", id)
        if settings.AFS_CSDB_DIST:
            _run_keyword("CellServDB.dist Should Exist")
        _run_keyword("Kerberos Client Must Be Installed")
        _run_keyword("Service Keytab Should Exist",
            settings.KRB_AFS_KEYTAB, settings.AFS_CELL, settings.KRB_REALM,
            settings.KRB_AFS_ENCTYPE, settings.AFS_KEY_FILE)
        _run_keyword("Kerberos Keytab Should Exist", settings.KRB_USER_KEYTAB,
            "%s" % settings.AFS_USER.replace('.','/'), settings.KRB_REALM)
        _run_keyword("Kerberos Keytab Should Exist", settings.KRB_ADMIN_KEYTAB,
            "%s" % settings.AFS_ADMIN.replace('.','/'), settings.KRB_REALM)
        _run_keyword("Can Get a Kerberos Ticket", settings.KRB_USER_KEYTAB,
            "%s" % settings.AFS_USER.replace('.','/'), settings.KRB_REALM)


    def _install_openafs(self):
        if settings.DO_INSTALL == False:
            logger.info("Skipping install: DO_INSTALL is False")
            return
        if settings.AFS_DIST == "transarc":
            if settings.TRANSARC_TARBALL:
                _run_keyword("Untar Binaries")
            _run_keyword("Install Server Binaries")
            _run_keyword("Install Client Binaries")
            _run_keyword("Install Workstation Binaries")
        elif settings.AFS_DIST == "rhel6":
            _run_keyword("Install OpenAFS Common Packages")
            _run_keyword("Install OpenAFS Kerberos5 Packages")
            _run_keyword("Install OpenAFS Server Packages")
            _run_keyword("Install OpenAFS Client Packages")
        else:
            raise AssertionError("Unsupported AFS_DIST: %s" % settings.AFS_DIST)

    def _setup_service_key(self):
        if settings.AFS_KEY_FILE == 'KeyFile':
            _run_keyword("Create Key File")
        elif settings.AFS_KEY_FILE == 'rxkad.keytab':
            _run_keyword("Install rxkad-k5 Keytab")
        elif settings.AFS_KEY_FILE == 'KeyFileExt':
            _run_keyword("Create Extended Key File", settings.KRB_AFS_ENCTYPE)
        else:
            raise AssertionError("Unsupported AFS_KEY_FILE! %s" % (settings.AFS_KEY_FILE))

    def _create_test_cell(self):
        if settings.KRB_REALM.lower() != settings.AFS_CELL.lower():
            _run_keyword("Set Kerberos Realm Name", settings.KRB_REALM)
        self. _setup_service_key()
        _run_keyword("Start the bosserver")
        _run_keyword("Set the Cell Name", settings.AFS_CELL)
        _run_keyword("Set the Cell Configuration")
        _run_keyword("Create Database Service", "ptserver", 7002)
        _run_keyword("Create Database Service", "vlserver", 7003)
        if settings.AFS_DAFS:
            _run_keyword("Create Demand Attach File Service")
        else:
            _run_keyword("Create File Service")
        _run_keyword("Create an Admin Account", settings.AFS_ADMIN)
        _run_keyword("Create the root.afs Volume")
        _run_keyword("Set Cache Manager Configuration")
        _run_keyword("Start the Cache Manager")
        _run_keyword("Login",  settings.AFS_ADMIN)
        hostname = socket.gethostname()
        _run_keyword("Create Volume",  hostname, "a", "root.cell")
        _run_keyword("Mount Cell Root Volume")
        _run_keyword("Replicate Volume", hostname, "a", "root.afs")
        _run_keyword("Replicate Volume", hostname, "a", "root.cell")

    def _shutdown_openafs(self):
        _run_keyword("Stop the Cache Manager")
        _run_keyword("Stop the bosserver")

    def _remove_openafs(self):
        if settings.DO_REMOVE == False:
            logger.info("Skipping remove: DO_REMOVE is False")
            return
        if settings.AFS_DIST == "transarc":
            _run_keyword("Remove Server Binaries")
            _run_keyword("Remove Client Binaries")
            _run_keyword("Remove Workstation Binaries")
        elif settings.AFS_DIST == "rhel6":
            _run_keyword("Remove Packages")
        else:
            raise AssertionError("Unsupported AFS_DIST: %s" % settings.AFS_DIST)

    def _purge_files(self):
        _run_keyword("Remove Cache Manager Configuration")
        valid = r'/vicep([a-z]|[a-h][a-z]|i[a-v])$'
        for vicep in glob.glob("/vicep*"):
            if re.match(valid, vicep) and os.path.isdir(vicep):
                _run_keyword("Purge Volumes On Partition", vicep)


class _Stage:

    def check(self, stage, fn):
        phase = 'Setup' if stage < _STAGE_SHUTDOWN_OPENAFS else 'Teardown'
        name = " ".join([w.capitalize() for w in fn.func_name.lstrip("_").split("_")])

        if phase == 'Teardown' and settings.DO_TEARDOWN == False:
            logger.info("Skipping Teardown: DO_TEARDOWN is False")
            return
        current = self.get()
        if current >= stage:
            logger.info("Skipping %s; already done (%d)" % (name, current))
            return
        if current != (stage - 1):
            raise AssertionError("Out of Sequence! %s; stage is %d, expected %d." % (name, current, stage-1))
        _say("%s.%s" % (phase, name))
        fn()
        if stage == _STAGE_PURGE_FILES:
            stage = _STAGE_INITIAL  # back to the start
        self.set(stage)

    def get(self):
        try:
            f = open("site/.stage", "r")
            stage = int(f.readline().strip())
            f.close()
            logger.debug("get stage: %d" % (stage))
            return stage
        except:
            self.set(_STAGE_INITIAL)
            return _STAGE_INITIAL

    def set(self, stage):
        try:
            f = open("site/.stage", "w")
            f.write("%d\n" % stage)
            f.close()
            logger.debug("set stage: %d" % (stage))
        except:
            raise AssertionError("Unable to save setup stage! %s" % (sys.exc_info()[0]))

def _lookup_keywords(filename):
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
    for filename in glob.glob('./resources/*.robot'):
        keywords = _lookup_keywords(filename)
        for keyword in keywords:
            register_run_keyword(filename, keyword, 0)

_register_keywords()

