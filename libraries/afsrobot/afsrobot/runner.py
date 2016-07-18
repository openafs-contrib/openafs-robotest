# Copyright (c) 2015-2016 Sine Nomine Associates
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

import os
import sys

import afsrobot.config
import afsrobot.command

try:
    import robot.run
except ImportError:
    sys.stderr.write("Cannot import robotframework packages.\n")
    sys.stderr.write("Install robotframework with `sudo pip install robotframework`.\n")
    sys.exit(1)

def mkdirp(path):
    """Make a directory with parents.
    Do not raise an execption if the directory already exists."""
    if not os.path.isdir(path):
        os.makedirs(path)

def start(msg):
    sys.stdout.write(msg.ljust(61, '.'))
    sys.stdout.write(' ')
    sys.stdout.flush()

def fail(msg):
    sys.stdout.write("fail\n%s\n" % (msg))
    sys.stdout.flush()
    sys.exit(1)

def ok():
    sys.stdout.write("ok\n")
    sys.stdout.flush()

def run_setup(args, config):
    """Setup OpenAFS client and servers and create a test cell."""
    aklog_workaround_check(args, config)

    keyfile = config.optstr('ssh', 'keyfile', required=True)
    logfile = os.path.join(config.optstr('paths', 'log', '.'), "setup.log")
    mkdirp(os.path.dirname(logfile))
    if os.path.exists(logfile):
        os.remove(logfile)

    def log(msg):
        with open(logfile, 'a') as f:
            f.writelines(["localhost", " ", "INFO", " ", msg, "\n"])

    sys.stdout.write("Running setup.\n")
    sys.stdout.flush()
    log("==== SETUP ====")

    # Install
    for hostname in config.opthostnames():
        cmd = afsrobot.command.Command(hostname, keyfile, logfile=logfile)
        section = "host:%s" % (hostname)
        installer = config.optstr(section, 'installer', default='none')
        if installer == 'transarc' or installer == 'rpm':
            start("Installing on %s" % (hostname))
            if config.optbool('kerberos', 'akimpersonate'):
                if cmd.afsutil('fakekey', *config.optfakekey()) != 0:
                    fail("Failed to create fake service key; see %s\n" % (logfile))
            if cmd.afsutil('install', *config.optinstall(hostname)) != 0:
                fail("Failed to install; see %s\n" % (logfile))
            ok()
        elif installer == 'none':
            log("Skipping install on hostname %s; installer is 'none'." % (hostname))
        else:
            fail("Invalid installer option for hostname %s!; installer='%s'." % (hostname, installer))

    # Set key
    for hostname in config.opthostnames():
        cmd = afsrobot.command.Command(hostname, keyfile, logfile=logfile)
        section = "host:%s" % (hostname)
        installer = config.optstr(section, 'installer', default='none')
        if installer == 'none':
            log("Skipping setkey on hostname %s; installer is 'none'." % (hostname))
            continue
        if cmd.afsutil('setkey', *config.optsetkey(hostname)) != 0:
            fail("Failed to setkey; see %s\n" % (logfile))

    # Start clients and servers.
    for hostname in config.opthostnames():
        cmd = afsrobot.command.Command(hostname, keyfile, logfile=logfile)
        section = "host:%s" % (hostname)
        if config.optbool(section, "isfileserver") or config.optbool(section, "isdbserver"):
            start("Starting servers on %s" % (hostname))
            if cmd.afsutil('start', 'server') != 0:
                fail("Failed to start servers; see %s\n" % (logfile))
            ok()
        if config.optbool(section, "isclient") and config.optbool(section, 'afsdb_dynroot', default=True):
            start("Starting client on %s" % (hostname))
            if cmd.afsutil('start', 'client') != 0:
                fail("Failed to start client; see %s\n" % (logfile))
            ok()

    cmd = afsrobot.command.Command('localhost', keyfile, logfile=logfile, verbose=args.verbose)
    start("Setting up new cell")
    if cmd.afsutil('newcell', *config.optnewcell()) != 0:
        fail("Failed to setup cell; see %s\n" % (logfile))
    ok()

    # Now that the root volumes are ready, start any non-dynroot clients.
    for hostname in config.opthostnames():
        cmd = afsrobot.command.Command(hostname, keyfile, logfile=logfile)
        section = "host:%s" % (hostname)
        if config.optbool(section, "isclient") and not config.optbool(section, 'afsdb_dynroot', default=True):
            start("Starting non-dynroot client on %s" % (hostname))
            if cmd.afsutil('start', 'client') != 0:
                fail("Failed to start client; see %s\n" % (logfile))
            ok()
    return 0

def run_login(args, config):
    logfile = os.path.join(config.optstr('paths', 'log', '.'), "login.log")
    mkdirp(os.path.dirname(logfile))
    if os.path.exists(logfile):
        os.remove(logfile)
    keyfile = config.optstr('ssh', 'keyfile', required=True)
    cargs = config.optlogin(args.user)
    if '--user' in cargs:
        user = cargs[cargs.index('--user') + 1]
    else:
        user = 'admin'
    cmd = afsrobot.command.Command('localhost', keyfile, logfile=logfile)
    start("Obtaining token for %s" % (user))
    rc = cmd.sh('afsutil', 'login', *cargs)
    if rc != 0:
        fail("Failed to login; see %s." % (logfile))
    ok()

def run_teardown(args, config):
    keyfile = config.optstr('ssh', 'keyfile', required=True)
    logfile = os.path.join(config.optstr('paths', 'log', '.'), "teardown.log")
    mkdirp(os.path.dirname(logfile))
    if os.path.exists(logfile):
        os.remove(logfile)

    def log(msg):
        with open(logfile, 'a') as f:
            f.writelines(["localhost", " ", "INFO", " ", msg, "\n"])

    sys.stdout.write("Running teardown.\n")
    log("==== TEARDOWN ====")

    for hostname in config.opthostnames():
        section = "host:%s" % (hostname)
        cmd = afsrobot.command.Command(hostname, keyfile, logfile=logfile)
        installer = config.optstr(section, 'installer', default='none')
        if installer == 'transarc':
            start("Removing clients and servers on %s" % (hostname))
            if cmd.afsutil('stop', *config.optcomponents(hostname)) != 0:
                fail("Failed to stop; see %s\n" % (logfile))
            if cmd.afsutil('remove', '--purge') != 0:
                fail("Failed to remove; see %s\n" % (logfile))
            ok()
        elif installer == 'none':
            log("Skipping remove on hostname %s; installer is 'none'." % (hostname))
        else:
            log("Invalid installer option for hostname %s!; installer='%s'.\n" % (hostname, installer))

    return 0

def run_tests(args, config):
    """Run the Robotframework test suites."""

    aklog_workaround_check(args, config)

    # Setup the python paths for our libs and resources.
    sys.path.append(os.path.join(config.get('paths', 'libraries'), 'OpenAFSLibrary'))
    sys.path.append(config.get('paths', 'resources'))

    # Create output dir if needed.
    output = config.optstr('paths', 'output', required=True)
    mkdirp(output)

    # Verify we have a keytab.
    if not os.path.isfile(config.get('kerberos', 'keytab')):
        sys.stderr.write("Cannot find keytab file '%s'!\n" % (config.get('kerberos', 'keytab')))
        sys.exit(1)

    # Setup the rf options.
    tests = config.get('paths', 'tests') # path to our tests
    options = {
        'variable': [
            'RESOURCES:%s' % config.get('paths', 'resources'), # path to our resources
            'AFS_CELL:%s' % config.get('cell', 'name'),
            'AFS_ADMIN:%s' % config.get('cell', 'admin'),
            'AFS_AKIMPERSONATE:%s' % config.getboolean('kerberos', 'akimpersonate'),
            'KRB_REALM:%s' % config.get('kerberos', 'realm'),
            'KRB_AFS_KEYTAB:%s' % config.get('kerberos', 'keytab'),
        ],
        'report': 'index.html',
        'outputdir': output,
        'loglevel': config.get('run', 'log_level'),
        'exclude': config.get('run', 'exclude_tags').split(','),
        'runemptysuite': True,
        'exitonfailure': False,
    }

    # Additional variables.
    if config.has_section('variables'):
        for o,v in config.items('variables'):
            options['variable'].append("%s:%s" % (o.upper(), v))

    # Additional options.
    if args.suite:
        options['suite'] = args.suite

    if args.include:
        options['include'] = args.include

    # Run the RF tests.
    sys.stdout.write("Running tests.\n")
    code = robot.run(tests, **options)
    if code != 0:
        sys.stderr.write("Tests failed.\n")

    return code

def aklog_workaround_check(args, config):
    # Sadly, akimpersonate is broken on the master branch at this time. To
    # workaround this users must setup an aklog 1.6.10+ in some directory
    # and then set a option to specify the location. Since this is easy to
    # get wrong, do a sanity check up front, at least until aklog is fixed.
    import mmap
    import re
    required = (1, 6, 10)
    def _warn():
        sys.stderr.write("Warning: The akimpersonate feature is enabled but the path to a supported\n")
        sys.stderr.write("         aklog is missing.  See the README.md for more information about\n")
        sys.stderr.write("         testing without Kerberos.\n")
    def _fail(msg=None):
        sys.stderr.write("Failed aklog check!\n")
        if msg:
            sys.stderr.write("%s\n" % (msg))
        sys.stderr.write("Please set the aklog option in the [variables] section of the config.\n")
        sys.stderr.write("Require aklog version %d.%d.x " % (required[0:2]))
        sys.stderr.write("and at least version %d.%d.%d.\n" % required)
        sys.exit(1)
    def _find_version(filename):
        with open(filename, "rb") as f:
            mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
            i = mm.find("@(#)")
            if i == -1:
                raise RuntimeError("Unable to find version string.")
            j = mm.find("\0", i)
            if j == -1:
                raise RuntimeError("Unable to find end of version string.")
            version_string = mm[i:j]
            mm.close()
        m = re.match(r'^@\(#\)\s*OpenAFS (\d+)\.(\d+)\.(\d+)', version_string)
        if m is None:
            # We need a valid n.n.n version number (dirty is tolerated)
            raise RuntimeError("Unrecognized version string '%s'." % (version_string))
        return tuple([int(x) for x in m.groups()])
    if config.optbool('kerberos', 'akimpersonate'):
        aklog = config.optstr('variables', 'aklog')
        if aklog is None:
            _warn()
            return
        if not os.access(aklog, os.F_OK):
            _fail("File '%s' not found." % (aklog))
        if not os.access(aklog, os.X_OK):
            _fail("File '%s' not executable." % (aklog))
        try:
            version = _find_version(aklog)
        except RuntimeError as e:
            _fail("Failed to get version number in file %s.\n%s" % (aklog, e))
        if version[0:2] != required[0:2] or version[2] < required[2]:
            msg = "Bad aklog version in file %s; " % (aklog)
            msg += "found version %d.%d.%d in file." % (version)
            _fail(msg)

