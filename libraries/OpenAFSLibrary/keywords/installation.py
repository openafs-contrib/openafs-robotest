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
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn
from robot.libraries.BuiltIn import register_run_keyword
from OpenAFSLibrary.util import get_var,run_program,load_globals,DIST
from OpenAFSLibrary.util.rpm import Rpm
from OpenAFSLibrary.util.command import vos,fs
from OpenAFSLibrary.keywords.login import _LoginKeywords
from OpenAFSLibrary.keywords.keytab import _KeytabKeywords

def say(msg):
    """Display a progress message to the console."""
    stream = sys.__stdout__
    stream.write("%s\n" % (msg))
    stream.flush()

def setup_stage(method):
    """Setup keyword wrapper to manage the order of setup stages."""
    def decorator(self):
        name = method.func_name
        if should_run_stage(name):
            say("Setup.%s" % name)
            method(self)
            set_stage(name)
    decorator.__doc__ = method.__doc__
    return decorator

def teardown_stage(method):
    """Teardown keyword wrapper to manage the order of teardown stages."""
    def decorator(self):
        if get_var('DO_TEARDOWN') == False:
            # Do not change the stage so the setup is skipped the
            # next time the tests harness is run.
            logger.info("Skipping Teardown: DO_TEARDOWN is False")
        else:
            name = method.func_name
            if should_run_stage(name):
                say("Teardown.%s" % name)
                method(self)
                set_stage(name)
    decorator.__doc__ = method.__doc__
    return decorator

def should_run_stage(stage):
    """Returns true if this stage should be run."""
    sequence = ['', # initial condition
                'precheck_system',  'install_openafs', 'create_test_cell',
                'shutdown_openafs', 'remove_openafs',  'purge_files']
    last = get_stage()
    if last == sequence[-1]:
        last = sequence[0] # next cycle
    if not stage in sequence[1:]:
        raise AssertionError("Internal error: invalid stage name '%s'" % stage)
    if not last in sequence:
        filename = os.path.join(get_var('SITE'), ".stage")
        raise AssertionError("Invalid stage name '%s' in file '%s'" % (last, filename))
    if sequence.index(stage) <= sequence.index(last):
        logger.info("Skipping %s; already done" % (stage))
        return False
    if sequence.index(stage) != sequence.index(last) + 1:
        logger.info("Skipping %s; out of sequence! last stage was '%s'" % (stage, last))
        return False
    return True

def get_stage():
    """Get the last setup/teardown stage which was completed."""
    try:
        filename = os.path.join(get_var('SITE'), ".stage")
        f = open(filename, "r")
        stage = f.readline().strip()
        f.close()
        logger.debug("get stage: %s" % (stage))
        return stage
    except:
        return reset_stage()

def reset_stage():
    """Reset the last stage to the initial state."""
    return set_stage('')

def set_stage(stage):
    """Set the last setup/teardown stage completed."""
    try:
        filename = os.path.join(get_var('SITE'), ".stage")
        f = open(filename, "w")
        f.write("%s\n" % stage)
        f.close()
        logger.debug("set stage: %s" % (stage))
    except:
        raise AssertionError("Unable to save setup/teardown stage! %s" % (sys.exc_info()[1]))
    return stage

def import_dist_variables():
    if not get_var('AFS_DIST'):
        raise AssertionError("AFS_DIST is not set!")
    dist = os.path.abspath(os.path.join(DIST, "%s.py" % get_var('AFS_DIST')))
    if not os.path.isfile(dist):
        raise AssertionError("Unable to find dist file! %s" % dist)
    load_globals(dist)

def register_keywords():
    """Register the keywords in all of the resource files."""
    resources = os.path.abspath(os.path.join(os.path.dirname(__file__), "../resources"))
    logger.info("resources=%s" % resources)
    if not os.path.isdir(resources):
        raise AssertionError("Unable to find resources directory! resources=%s" % resources)
    for filename in glob.glob(os.path.join(resources, "*.robot")):
        logger.info("looking up keywords in file %s" % filename)
        try:
            BuiltIn().import_resource(filename)
            keywords = lookup_keywords(filename)
            for keyword in keywords:
                register_run_keyword(filename, keyword, 0)
        except:
            pass

def lookup_keywords(filename):
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

def run_keyword(name, *args):
    """Run the named keyword."""
    BuiltIn().run_keyword(name, *args)

def setup_service_key():
    """Helper method to setup the AFS service key.

    Create a dummy keytab file when running in akimpersonate mode.

    Call the correct keyword depending on which key file is being setup in
    the test cell. Supported types are the lecacy DES KeyFile, the interim
    rxkad-k5 non-DES enctype, and the modern non-DES KeyFileExt.
    """
    if get_var('AFS_AKIMPERSONATE'):
        keytab = get_var('KRB_AFS_KEYTAB')
        if keytab and not os.path.exists(keytab):
            cell = get_var('AFS_CELL')
            realm = get_var('KRB_REALM')
            enctype = get_var('KRB_AFS_ENCTYPE')
            _KeytabKeywords().create_service_keytab(keytab, cell, realm, enctype, akimpersonate=True)
    if get_var('AFS_KEY_FILE') == 'KeyFile':
        run_keyword("Create Key File")
    elif get_var('AFS_KEY_FILE') == 'rxkad.keytab':
        run_keyword("Install rxkad-k5 Keytab")
    elif get_var('AFS_KEY_FILE') == 'KeyFileExt':
        run_keyword("Create Extended Key File", get_var('KRB_AFS_ENCTYPE'))
    else:
        raise AssertionError("Unsupported AFS_KEY_FILE! %s" % (get_var('AFS_KEY_FILE')))

def remove_symlinks_created_by_bosserver():
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
    afs_conf_dir = get_var('AFS_CONF_DIR')    # e.g. /usr/afs/etc
    afs_data_dir = get_var('AFS_DATA_DIR')    # e.g. /usr/vice/etc
    if afs_conf_dir is None or afs_conf_dir == "":
        raise AssertionError("AFS_CONF_DIR is not set!")
    if afs_data_dir is None or afs_data_dir == "":
        raise AssertionError("AFS_DATA_DIR is not set!")
    if not os.path.exists(afs_data_dir):
        run_keyword("Sudo", "mkdir -p %s" % (afs_data_dir))
    if os.path.islink("%s/CellServDB" % (afs_data_dir)):
        run_keyword("Sudo", "rm", "-f", "%s/CellServDB" % (afs_data_dir))
    if os.path.islink("%s/ThisCell" % (afs_data_dir)):
        run_keyword("Sudo", "rm", "-f", "%s/ThisCell" % (afs_data_dir))
    run_keyword("Sudo", "cp", "%s/CellServDB" % (afs_conf_dir), "%s/CellServDB.local" % (afs_data_dir))
    run_keyword("Sudo", "cp", "%s/CellServDB" % (afs_conf_dir), "%s/CellServDB" % (afs_data_dir))
    run_keyword("Sudo", "cp", "%s/ThisCell" % (afs_conf_dir), "%s/ThisCell" % (afs_data_dir))



class _InstallationKeywords(object):
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

    @setup_stage
    def precheck_system(self):
        """Verify system prerequisites are met."""
        run_keyword("Non-interactive sudo is Required")
        if not get_var('AFS_DIST') in ('transarc', 'rhel6', 'suse'):
            raise AssertionError("Unsupported AFS_DIST: %s" % get_var('AFS_DIST'))
        run_keyword("Required Variables Should Not Be Empty")
        if get_var('AFS_DIST') == 'transarc':
            run_keyword("Transarc Variables Should Exist")
        run_keyword("Host Address Should Not Be Loopback")
        run_keyword("Network Interface Should Have The Host Address")
        run_keyword("OpenAFS Servers Should Not Be Running")
        run_keyword("AFS Filesystem Should Not Be Mounted")
        run_keyword("OpenAFS Kernel Module Should Not Be Loaded")
        run_keyword("OpenAFS Installation Directories Should Not Exist")
        if os.path.exists(get_var('AFS_CACHE_DIR')):
            run_keyword("Cache Partition Should Be Empty")
        for id in ['a']:
            run_keyword("Vice Partition Should Be Empty", id)
            run_keyword("Vice Partition Should Be Attachable", id)
        if get_var('AFS_CSDB_DIST'):
            run_keyword("CellServDB.dist Should Exist")
        if get_var('AFS_AKIMPERSONATE') == False:
            run_keyword("Kerberos Client Must Be Installed")
            run_keyword("Service Keytab Should Exist",
                get_var('KRB_AFS_KEYTAB'), get_var('AFS_CELL'), get_var('KRB_REALM'),
                get_var('KRB_AFS_ENCTYPE'), get_var('AFS_KEY_FILE'))
            run_keyword("Kerberos Keytab Should Exist", get_var('KRB_USER_KEYTAB'),
                "%s" % get_var('AFS_USER').replace('.','/'), get_var('KRB_REALM'))
            run_keyword("Kerberos Keytab Should Exist", get_var('KRB_ADMIN_KEYTAB'),
                "%s" % get_var('AFS_ADMIN').replace('.','/'), get_var('KRB_REALM'))
            run_keyword("Can Get a Kerberos Ticket", get_var('KRB_USER_KEYTAB'),
                "%s" % get_var('AFS_USER').replace('.','/'), get_var('KRB_REALM'))

    @setup_stage
    def install_openafs(self):
        """Install the OpenAFS client and server binaries."""
        if get_var('DO_INSTALL') == False:
            logger.info("Skipping install: DO_INSTALL is False")
            return
        uname = os.uname()[0]
        dist = get_var('AFS_DIST')
        if dist == "transarc":
            try:
                tarball = get_var('TRANSARC_TARBALL')
            except AssertionError:
                tarball = False
            if tarball:
                run_keyword("Untar Binaries")
            run_keyword("Install Server Binaries")
            run_keyword("Install Client Binaries")
            run_keyword("Install Workstation Binaries")
            run_keyword("Install Shared Libraries")
            if uname == "Linux":
                run_keyword("Install Init Script on Linux")
            elif uname == "SunOS":
                run_keyword("Install Init Script on Solaris")
            else:
                raise AssertionError("Unsupported operating system: %s" % (uname))
        elif dist in ('rhel6', 'suse'):
            rpm = Rpm.current()
            run_keyword("Install RPM Files", *rpm.get_server_rpms())
            run_keyword("Install RPM Files", *rpm.get_client_rpms())
        else:
            raise AssertionError("Unsupported AFS_DIST: %s" % (dist))

    @setup_stage
    def create_test_cell(self):
        """Create the OpenAFS test cell."""
        hostname = socket.gethostname()
        if get_var('KRB_REALM').lower() != get_var('AFS_CELL').lower():
            run_keyword("Set Kerberos Realm Name", get_var('KRB_REALM'))
        run_keyword("Set Machine Interface")
        setup_service_key()
        if get_var('AFS_DIST') == "transarc":
            run_keyword("Start the bosserver")
        else:
            run_keyword("Start Service", "openafs-server")
        run_keyword("Set the Cell Name", get_var('AFS_CELL'))
        remove_symlinks_created_by_bosserver()
        run_keyword("Create Database Service", "ptserver", 7002)
        run_keyword("Create Database Service", "vlserver", 7003)
        if get_var('AFS_DAFS'):
            run_keyword("Create Demand Attach File Service")
        else:
            run_keyword("Create File Service")
        run_keyword("Create an Admin Account", get_var('AFS_ADMIN'))
        run_keyword("Create the root.afs Volume")
        if get_var('AFS_CSDB_DIST'):
            run_keyword("Append CellServDB.dist")
        run_keyword("Create AFS Mount Point")
        run_keyword("Set Cache Manager Configuration")
        if get_var('AFS_DIST') == "transarc":
            uname = os.uname()[0]
            if uname == 'Linux':
                run_keyword("Start the Cache Manager on Linux")
            elif uname == 'SunOS':
                run_keyword("Start the Cache Manager on Solaris")
            else:
                raise AssertionError("Unsupported operating system: %s" % (uname))
        else:
            run_keyword("Start Service", "openafs-client")
        run_keyword("Cell Should Be", get_var('AFS_CELL'))
        _LoginKeywords().login(get_var('AFS_ADMIN'))
        vos("create", hostname, "a", "root.cell")
        run_keyword("Mount Cell Root Volume")
        for v in ("root.afs", "root.cell"):
            vos("addsite", hostname, "a", v)
            vos("release", v)

        # Create a replicated test volume.
        path = "/afs/.%s/test" % get_var('AFS_CELL')
        volume = "test"
        part = "a"
        parent = "root.cell"
        vos("create", hostname, part, volume)
        fs('mkmount', '-dir', path, '-vol', volume)
        run_keyword("Add Access Rights",  path, "system:anyuser", "rl")

        vos("addsite", hostname, part, volume)
        vos("release", volume)
        vos("release", parent)

        fs("checkvolumes")  # just in case
        fs("flushall")      # a desperate hack
        _LoginKeywords().logout()

    @teardown_stage
    def shutdown_openafs(self):
        """Shutdown the OpenAFS client and servers."""
        if get_var('AFS_DIST') == "transarc":
            uname = os.uname()[0]
            if uname == 'Linux':
                run_keyword("Stop the Cache Manager on Linux")
            elif uname == 'SunOS':
                run_keyword("Stop the Cache Manager on Solaris")
            else:
                raise AssertionError("Unsupported operating system: %s" % (uname))
            run_keyword("Stop the bosserver")
        else:
            run_keyword("Stop Service", "openafs-client")
            run_keyword("Stop Service", "openafs-server")

    @teardown_stage
    def remove_openafs(self):
        """Remove the OpenAFS server and client binaries."""
        if get_var('DO_REMOVE') == False:
            logger.info("Skipping remove: DO_REMOVE is False")
            return
        if get_var('AFS_DIST') == "transarc":
            run_keyword("Remove Server Binaries")
            run_keyword("Remove Client Binaries")
            run_keyword("Remove Workstation Binaries")
            run_keyword("Remove Shared Libraries Binaries")
        else:
            run_keyword("Remove OpenAFS RPM Packages")

    @teardown_stage
    def purge_files(self):
        """Remove remnant data and configuration files."""
        run_keyword("Purge Server Configuration")
        run_keyword("Purge Cache Manager Configuration")
        # TODO: Probably the only sane way to do this is to call
        #       a helper script which runs as root.
        # run_keyword("Purge Cache")
        valid = r'/vicep([a-z]|[a-h][a-z]|i[a-v])$'
        for vicep in glob.glob("/vicep*"):
            if re.match(valid, vicep) and os.path.isdir(vicep):
                run_keyword("Purge Directory", "%s/AFSIDat" % vicep)
                run_keyword("Purge Directory", "%s/Lock" % vicep)
                for vheader in glob.glob("%s/V*.vol" % vicep):
                    run_keyword("Sudo", "rm -f %s" % vheader)

import_dist_variables()
register_keywords()
