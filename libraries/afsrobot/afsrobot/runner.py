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
import base64
import sys
import socket
import logging
import subprocess
import afsutil.system
import afsrobot.config
from afsrobot.config import islocal

# Install robotframework with `sudo pip install robotframework`
import robot.run

logger = logging.getLogger(__name__)

class SimpleMessage(object):
    def __init__(self, msg):
        self.msg = msg

    def __enter__(self):
        sys.stdout.write(self.msg)
        sys.stdout.write("\n")

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            sys.stdout.write("ok: %s\n" % (self.msg))
        else:
            sys.stdout.write("fail: %s\n" % (self.msg))
        return False

class ProgressMessage(object):
    """Display a progress message followed by ok or fail."""
    def __init__(self, msg):
        self.msg = msg

    def __enter__(self):
        sys.stdout.write(self.msg.ljust(60, '.'))
        sys.stdout.flush()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            sys.stdout.write(" ok\n")
        else:
            sys.stdout.write(" fail\n")
        return False

class Runner(object):

    def __init__(self, config=None):
        if config is None:
            config = afsrobot.config.Config()
            config.load_defaults()
        self.config = config
        self.hostname = socket.gethostname()
        self.verbose = False

    def _aklog_workaround_check(self):
        # Sadly, akimpersonate is broken on the master branch at this time. To
        # workaround this users must setup an aklog 1.6.10+ in some directory
        # and then set a option to specify the location. Since this is easy to
        # get wrong, do a sanity check up front, at least until aklog is fixed.
        if self.config.optbool('kerberos', 'akimpersonate'):
            aklog = self.config.optstr('variables', 'aklog')
            if aklog is None:
                sys.stderr.write("Warning: The akimpersonate feature is enabled but the aklog option\n")
                sys.stderr.write("         is not set. See the README.md for more information about\n")
                sys.stderr.write("         testing without Kerberos.\n")

    def _run(self, hostname, args, sudo=False):
        """Run commands locally or remotely, with or without sudo."""
        if sudo:
            args.insert(0, 'sudo')
            args.insert(1, '-n')
        if not islocal(hostname):
            command = subprocess.list2cmdline(args)
            args = [
                'ssh', '-q', '-t', '-o', 'PasswordAuthentication no'
            ]
            keyfile = self.config.optstr('ssh', 'keyfile')
            if keyfile:
                 args.append('-i')
                 args.append(keyfile)
            args.append(hostname)
            args.append(command)
        afsutil.system.sh(*args, quiet=False, output=False, prefix=hostname)

    def _afsutil(self, hostname, command, args, sudo=True):
        args.insert(0, 'afsutil')
        args.insert(1, command)
        if logger.getEffectiveLevel() == logging.DEBUG:
            args.append('--verbose')
        self._run(hostname, args, sudo=sudo)

    def setup(self, **kwargs):
        """Setup OpenAFS client and servers and create a test cell."""
        logger.info("setup starting")

        verbose = kwargs.get('verbose', False)
        progress = SimpleMessage if verbose else ProgressMessage
        self._aklog_workaround_check()

        # Be sure to use the same secret value on each host.
        if self.config.optbool('kerberos', 'akimpersonate'):
            secret = self.config.optstr('kerberos', 'secret')
            if secret is None:
                random = base64.b64encode(os.urandom(32))
                self.config.set_value('kerberos', 'secret', random)

        # Installation.
        for hostname in self.config.opthostnames():
            section = "host:%s" % (hostname)
            installer = self.config.optstr(section, 'installer', default='none')
            if installer == 'none':
                logger.info("Skipping install on hostname %s; installer is 'none'." % (hostname))
            elif installer == 'transarc' or installer == 'rpm':
                with progress("Installing on %s" % (hostname)):
                    if self.config.optbool('kerberos', 'akimpersonate'):
                        self._afsutil(hostname, 'fakekey', self.config.optfakekey())
                    self._afsutil(hostname, 'install', self.config.optinstall(hostname))
                with progress("Setting key on %s" % (hostname)):
                    self._afsutil(hostname, 'setkey', self.config.optsetkey(hostname))
                if self.config.optbool(section, "isfileserver") or \
                   self.config.optbool(section, "isdbserver"):
                    with progress("Starting servers on %s" % (hostname)):
                        self._afsutil(hostname, 'start', ['server'])
                if self.config.optbool(section, "isclient") and \
                   self.config.optdynroot():
                    with progress("Starting client on %s" % (hostname)):
                        self._afsutil(hostname, 'start', ['client'])
            else:
                raise ValueError("Invalid installer option for hostname %s!; installer='%s'." % (hostname, installer))
        # Setup new cell.
        with progress("Setting up new cell"):
            self._afsutil(self.hostname, 'newcell', self.config.optnewcell())
        # Now that the root volumes are ready, start any non-dynroot clients.
        for hostname in self.config.opthostnames():
            section = "host:%s" % (hostname)
            if self.config.optbool(section, "isclient") and \
               not self.config.optdynroot():
                with progress("Starting non-dynroot client on %s" % (hostname)):
                    self._afsutil(hostname, 'start', ['client'])
        logger.info("setup done")

    def login(self, **kwargs):
        """Obtain a token for manual usage.

        The test harness will obtain and remove tokens as needed for the RF
        tests, but this sub-command is a useful short cut to get a token for
        the configured admin user.
        """
        verbose = kwargs.get('verbose', False)
        progress = SimpleMessage if verbose else ProgressMessage
        user = kwargs.get('user')
        if user is None:
            user = self.config.optstr('cell', 'admin', 'admin')
        args = self.config.optlogin(user=user)
        with progress("Obtaining token for %s" % (user)):
            self._afsutil(self.hostname, 'login', args, sudo=False)

    def test(self, **kwargs):
        """Run the Robotframework test suites."""
        self._aklog_workaround_check()
        config = self.config

        # Setup the python paths for our libs and resources.
        sys.path.append(os.path.join(config.get('paths', 'libraries'), 'OpenAFSLibrary'))
        sys.path.append(config.get('paths', 'resources'))

        # Create output dir if needed.
        output = config.optstr('paths', 'output', required=True)
        if not os.path.isdir(output):
            os.makedirs(output)

        # Verify we have a afs service keytab.
        if config.optbool('kerberos', 'akimpersonate'):
            keytab = config.optkeytab('fake')
        else:
            keytab = config.optkeytab('afs')
        if not os.path.isfile(keytab):
            raise ValueError("Cannot find keytab file '%s'!\n" % keytab)

        # Additional variables.
        variable = [
            'RESOURCES:%s' % config.get('paths', 'resources'),
            'AFS_CELL:%s' % config.get('cell', 'name'),
            'AFS_ADMIN:%s' % config.get('cell', 'admin'),
            'AFS_AKIMPERSONATE:%s' % config.getboolean('kerberos', 'akimpersonate'),
            'KRB_REALM:%s' % config.get('kerberos', 'realm'),
            'KRB_AFS_KEYTAB:%s' % keytab,
        ]
        if config.has_section('variables'):
            for o,v in config.items('variables'):
                variable.append("%s:%s" % (o.upper(), v))

        # Determine tests to exclude.
        exclude = config.get('run', 'exclude_tags').split(',')

        # Setup the rf options.
        tests = config.get('paths', 'tests') # path to our tests
        options = {
            'report': 'index.html',
            'outputdir': output,
            'loglevel': config.get('run', 'log_level'),
            'variable': variable,
            'exclude': exclude,
            'runemptysuite': True,
            'exitonfailure': False,
        }

        # Additional options.
        if kwargs.has_key('suite') and kwargs['suite']:
            options['suite'] = kwargs['suite']

        if kwargs.has_key('include') and kwargs['include']:
            options['include'] = kwargs['include']

        # Run the RF tests.
        code = robot.run(tests, **options)
        if code != 0:
            sys.stderr.write("Tests failed.\n")
        return code

    def teardown(self, **kwargs):
        """Uninstall and purge files."""
        logger.info("teardown starting")

        verbose = kwargs.get('verbose', False)
        progress = SimpleMessage if verbose else ProgressMessage
        for hostname in self.config.opthostnames():
            section = "host:%s" % (hostname)
            installer = self.config.optstr(section, 'installer', default='none')
            if installer == 'none':
                logger.info("Skipping remove on hostname %s; installer is 'none'." % (hostname))
            elif installer == 'transarc' or installer == 'rpm':
                with progress("Removing clients and servers on %s" % (hostname)):
                    self._afsutil(hostname, 'stop', self.config.optcomponents(hostname))
                    self._afsutil(hostname, 'remove', ['--purge'])
                    if self.config.optbool('kerberos', 'akimpersonate'):
                        keytab = self.config.optkeytab('fake')
                        if keytab:
                            try:
                                self._run(hostname, ['rm', '-f', keytab])
                            except afsutil.system.CommandFailed as e:
                                logger.warning("Unable to remove keytab; code=%d" % (e.code))
            else:
                logger.info("Invalid installer option for hostname %s!; installer='%s'." % (hostname, installer))
        logger.info("teardown done")


# Test driver.
if __name__ == '__main__':
    logging.basicConfig()
    if len(sys.argv) < 2:
        sys.stderr.write("usage: python runner.py [command]\n")
        sys.exit(1)
    cf = os.path.join(os.getenv('HOME'), '.afsrobotestrc', 'afs-robotest.conf')
    c = afsrobot.config.Config()
    c.load_from_file(cf)
    r = Runner(config=c)
    fn = getattr(r, sys.argv[1])
    fn()
