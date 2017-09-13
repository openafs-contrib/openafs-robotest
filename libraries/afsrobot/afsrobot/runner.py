# Copyright (c) 2015-2017 Sine Nomine Associates
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

class NoMessage(object):
    def __init__(self, msg):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

class SimpleMessage(object):
    def __init__(self, msg):
        self.msg = msg

    def __enter__(self):
        sys.stdout.write("# {0}\n".format(self.msg))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            sys.stdout.write("# ok: %s\n" % (self.msg))
        else:
            sys.stdout.write("# fail: %s\n" % (self.msg))
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

class Host(object):
    def __init__(self, hostname, config):
        section = "host:{0}".format(hostname)
        self.name = hostname
        self.install = config.optstr(section, 'installer', default='none') != 'none'
        self.is_server = config.optbool(section, "isfileserver") or \
                         config.optbool(section, "isdbserver")
        self.is_client = config.optbool(section, "isclient")
    def __repr__(self):
        return "Host<name={0}, install={1}, is_server={2}, is_client={3}>".format(
                self.name, self.install, self.is_server, self.is_client)

class Runner(object):

    def __init__(self, config=None):
        if config is None:
            config = afsrobot.config.Config()
            config.load_defaults()
        self.config = config
        self.hostname = socket.gethostname()
        self.quiet = False
        self.verbose = False
        self.dryrun = False
        self.showcmds = False

    def _set_options(self, **kwargs):
        self.quiet = kwargs.get('quiet', False)
        self.verbose = kwargs.get('verbose', False)
        self.dryrun = kwargs.get('dryrun', False)
        self.showcmds = kwargs.get('showcmds', False)

    def progress_factory(self):
        if self.quiet:
            progress = NoMessage
        elif self.verbose or self.showcmds:
            progress = SimpleMessage
        else:
            progress = ProgressMessage
        return progress

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
        if self.showcmds:
            sys.stdout.write("{0}\n".format(subprocess.list2cmdline(args)))
        if not self.dryrun:
            afsutil.system.sh(*args, quiet=False, output=False, prefix=hostname)

    def _afsutil(self, hostname, command, subcmd=None, args=None, sudo=True):
        if args is None:
           args = []
        args.insert(0, 'afsutil')
        args.insert(1, command)
        if subcmd:
            args.insert(2, subcmd)
        if logger.getEffectiveLevel() == logging.DEBUG:
            args.append('--verbose')
        self._run(hostname, args, sudo=sudo)

    def setup(self, **kwargs):
        """Setup OpenAFS client and servers and create a test cell."""
        self._aklog_workaround_check()
        logger.info("setup starting")
        self._set_options(**kwargs)
        c = self.config # alias
        progress = self.progress_factory()

        # Be sure to use the same secret value on each host.
        if c.optbool('kerberos', 'akimpersonate'):
            secret = c.optstr('kerberos', 'secret')
            if secret is None:
                random = base64.b64encode(os.urandom(32))
                c.set_value('kerberos', 'secret', random)

        # Gather list of hosts for this setup.
        allhosts = [Host(n,c) for n in self.config.opthostnames()]
        hosts = {
            'all': allhosts,
            'install': [h for h in allhosts if h.install],
            'servers': [h for h in allhosts if h.is_server],
            'clients': [h for h in allhosts if h.is_client],
        }

        if not hosts['all']:
            logger.error("No hosts configured!")
            return

        if hosts['install']:
            with progress("Installing OpenAFS"):
                for host in hosts['install']:
                    self._afsutil(host.name, 'install', args=c.optinstall(host.name))

        if c.optbool('kerberos', 'akimpersonate'):
            with progress("Creating test key"):
                for host in hosts['all']:
                    self._afsutil(host.name, 'keytab', subcmd='create', args=c.optfakekey())

        if hosts['servers']:
            with progress("Setting service key"):
                for host in hosts['servers']:
                    self._afsutil(host.name, 'keytab', subcmd='setkey', args=c.optsetkey(host.name))

        if hosts['servers']:
            with progress("Starting servers"):
                for host in hosts['servers']:
                    self._afsutil(host.name, 'start', subcmd='server')
            with progress("Creating new cell"):
                host = hosts['servers'][0]
                self._afsutil(host.name, 'newcell', args=c.optnewcell())

        if hosts['clients']:
            with progress("Starting clients"):
                for host in hosts['clients']:
                    self._afsutil(host.name, 'start', subcmd='client')
            with progress("Mounting root volumes"):
                host = hosts['clients'][0]
                self._afsutil(host.name, 'mtroot', args=c.optmtroot())

        logger.info("setup done")

    def login(self, **kwargs):
        """Obtain a token for manual usage.

        The test harness will obtain and remove tokens as needed for the RF
        tests, but this sub-command is a useful short cut to get a token for
        the configured admin user.
        """
        self._set_options(**kwargs)
        progress = self.progress_factory()

        user = kwargs.get('user')
        if user is None:
            user = self.config.optstr('cell', 'admin', 'admin')
        args = self.config.optlogin(user=user)
        with progress("Obtaining token for %s" % (user)):
            self._afsutil(self.hostname, 'login', args=args, sudo=False)

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
        gfind = self.config.optstr('variables', 'gfind')
        if not gfind:
            sys.stderr.write("Excluding 'requires-gfind'; variables.gfind is not set in config.\n")
            exclude.append('requires-gfind')

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
        for key in kwargs.keys():
            if not kwargs[key] is None:
                options[key] = kwargs[key]

        # Run the RF tests.
        code = robot.run(tests, **options)
        if code != 0:
            sys.stderr.write("Tests failed.\n")
        return code

    def teardown(self, **kwargs):
        """Uninstall and purge files."""
        logger.info("teardown starting")

        c = self.config # alias
        self._set_options(**kwargs)
        progress = self.progress_factory()

        # Gather list of hosts.
        allhosts = [Host(n,c) for n in self.config.opthostnames()]
        hosts = {
            'all': allhosts,
            'install': [h for h in allhosts if h.install],
            'servers': [h for h in allhosts if h.is_server],
            'clients': [h for h in allhosts if h.is_client],
        }

        if hosts['clients']:
            with progress("Stopping clients"):
                for host in hosts['clients']:
                    self._afsutil(host.name, 'stop', subcmd='client')

        if hosts['servers']:
            with progress("Stopping servers"):
                for host in hosts['servers']:
                    self._afsutil(host.name, 'stop', subcmd='server')

        if hosts['install']:
            with progress("Removing OpenAFS"):
                for host in hosts['install']:
                    self._afsutil(host.name, 'remove', args=['--purge'])

        if c.optbool('kerberos', 'akimpersonate'):
            with progress("Removing test key"):
                for hosts in hosts['all']:
                    self._afsutil(host.name, 'keytab', subcmd='destroy', args=c.optremovekey())

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
