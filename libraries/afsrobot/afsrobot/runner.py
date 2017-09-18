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

"""Run setup, tests, and teardown."""

import os
import base64
import sys
import logging
import robot.run
from afsutil.system import sh
from afsrobot.config import islocal
from afsrobot.ssh import ssh

logger = logging.getLogger(__name__)

class NoMessage(object):
    """Do not display progress messages."""
    def __init__(self, msg):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

class SimpleMessage(object):
    """Display simple messages for non-progress modes."""
    def __init__(self, msg):
        self.msg = msg

    def __enter__(self):
        sys.stdout.write("# {0}\n".format(self.msg))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout.write("\n")
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

def _afsutil(cmd, subcmd, args):
    """Build afsutil command line args."""
    afsutil = ['afsutil']
    afsutil.append(cmd)
    if subcmd:
        afsutil.append(subcmd)
    if logger.getEffectiveLevel() == logging.DEBUG:
        afsutil.append('--verbose')
    return afsutil + args

def _sudo(args):
    """Build sudo command line args."""
    return ['sudo', '-n'] + args

class Node(object):
    """A node (host) to be configured; may be the local host or a remote host."""

    def __init__(self, name, config, **kwargs):
        """Initialize this node.

        name: hostname of this node
        config: parsed configuration
        """
        if name is None or name == '':
            name = 'localhost'
        section = "host:{0}".format(name)
        self.name = name
        self.config = config
        self.name = name
        self.dryrun = kwargs.get('dryrun', False)
        self.installer = config.optstr(section, 'installer', default='none') != 'none'
        self.is_server = config.optbool(section, "isfileserver") or config.optbool(section, "isdbserver")
        self.is_client = config.optbool(section, "isclient")

    def execute(self, args):
        """Run the command."""
        sh(*args, prefix=self.name, quiet=False, output=False, dryrun=self.dryrun)

    def version(self):
        """Run afsutil version."""
        self.execute((_afsutil('version', None, [])))

    def install(self):
        """Run afsutil install."""
        c = self.config
        section = "host:%s" % (self.name)
        args = []
        args.append('--components')
        if self.is_server:
            args.append('server')
        if self.is_client:
            args.append('client')
        dist = c.optstr(section, 'installer', default='transarc')
        args.append('--dist')
        args.append(dist)
        if dist == 'transarc':
            dest = c.optstr(section, 'dest')
            if dest:
                args.append('--dir')
                args.append(dest)
        elif dist == 'rpm':
            rpms = c.optstr(section, 'rpms')
            if rpms:
                args.append('--dir')
                args.append(rpms)
        cell = c.optstr('cell', 'name')
        if cell:
            args.append('--cell')
            args.append(cell)
        hosts = c.opthostnames(filter='isdbserver', lookupname=True)
        if hosts:
            args.append('--hosts')
            args += hosts
        realm = c.optstr('kerberos', 'realm')
        if realm:
            args.append('--realm')
            args.append(realm)
        csdb = c.optstr(section, 'csdb')
        if csdb:
            args.append('--csdb')
            args.append(csdb)
        args.append('--force')
        if c.has_section('options'):
            for k,v in c.items('options'):
                if k == 'afsd' or k == 'bosserver':
                    args.append('-o')
                    args.append("%s=%s" % (k,v))
        self.execute(_sudo(_afsutil('install', None, args)))

    def keytab_create(self):
        """Run afsutil keytab create."""
        c = self.config
        if not c.optbool('kerberos', 'akimpersonate'):
            raise AssertionError('Trying to get fakekey options without akimpersonate.')
        args = []
        cell = c.optstr('cell', 'name')
        if cell:
            args.append('--cell')
            args.append(cell)
        keytab = c.optkeytab('fake')
        if keytab:
            args.append('--keytab')
            args.append(keytab)
        realm = c.optstr('kerberos', 'realm')
        if realm:
            args.append('--realm')
            args.append(realm)
        enctype = c.optstr('kerberos', 'enctype')
        if enctype:
            args.append('--enctype')
            args.append(enctype)
        secret = c.optstr('kerberos', 'secret')
        if secret:
            args.append('--secret')
            args.append(secret)
        self.execute(_sudo(_afsutil('keytab', 'create', args)))

    def keytab_setkey(self):
        """Run afsutil keytab setkey."""
        c = self.config
        section = "host:%s" % (self.name)
        args = []
        cell = c.optstr('cell', 'name')
        if cell:
            args.append('--cell')
            args.append(cell)
        realm = c.optstr('kerberos', 'realm')
        if realm:
            args.append('--realm')
            args.append(realm)
        if c.optbool('kerberos', 'akimpersonate'):
            name = 'fake'
        else:
            name = 'afs'
        keytab = c.optkeytab(name)
        if keytab:
            args.append('--keytab')
            args.append(keytab)
        keyformat = c.optstr(section, 'keyformat')
        if keyformat:
            args.append('--format')
            args.append(keyformat)
        self.execute(_sudo(_afsutil('keytab', 'setkey', args)))

    def keytab_destroy(self):
        """Run afsutil keytab destroy."""
        c = self.config
        if not c.optbool('kerberos', 'akimpersonate'):
            raise AssertionError('Trying to get fakekey options without akimpersonate.')
        args = []
        keytab = c.optkeytab('fake')
        if keytab:
            args.append('--keytab')
            args.append(keytab)
        args.append('--force')
        self.execute(_sudo(_afsutil('keytab', 'destroy', args)))

    def start(self, comp):
        """Run afsutil start."""
        self.execute(_sudo(_afsutil('start', comp, [])))

    def stop(self, comp):
        """Run afsutil stop."""
        self.execute(_sudo(_afsutil('stop', comp, [])))

    def newcell(self):
        """Run afsutil newcell."""
        c = self.config
        args = []
        cell = c.optstr('cell', 'name', 'localcell')
        if cell:
            args.append('--cell')
            args.append(cell)
        admin = c.optstr('cell', 'admin', 'admin')
        if admin:
            args.append('--admin')
            args.append(admin)
        realm = c.optstr('kerberos', 'realm')
        if realm:
            args.append('--realm')
            args.append(realm)
        fs = c.opthostnames(filter='isfileserver', lookupname=True)
        if fs:
            args.append('--fs')
            args += fs
        db = c.opthostnames(filter='isdbserver', lookupname=True)
        if db:
            args.append('--db')
            args += db
        if c.has_section('options'):
            for k,v in c.items('options'):
                args.append('-o')
                args.append("%s=%s" % (k,v))
        self.execute(_sudo(_afsutil('newcell', None, args)))

    def mtroot(self):
        """Run afsutil mtroot."""
        c = self.config
        args = []
        cell = c.optstr('cell', 'name', 'localcell')
        if cell:
            args.append('--cell')
            args.append(cell)
        admin = c.optstr('cell', 'admin', 'admin')
        if admin:
            args.append('--admin')
            args.append(admin)
        top = 'test'
        if top:
            args.append('--top')
            args.append(top)
        realm = c.optstr('kerberos', 'realm')
        if realm:
            args.append('--realm')
            args.append(realm)
        akimpersonate = c.optbool('kerberos', 'akimpersonate')
        if akimpersonate:
            args.append('--akimpersonate')
            keytab = c.optkeytab('fake')
            if keytab:
                args.append('--keytab')
                args.append(keytab)
        else:
            keytab = c.optkeytab('user')
            if keytab:
                args.append('--keytab')
                args.append(keytab)
        fs = c.opthostnames(filter='isfileserver', lookupname=True)
        if fs:
            args.append('--fs')
            args += fs
        aklog = c.optstr('variables', 'aklog')
        if aklog:
            args.append('--aklog')
            args.append(aklog)
        if c.has_section('options'):
            for k,v in c.items('options'):
                args.append('-o')
                args.append("%s=%s" % (k,v))
        self.execute(_afsutil('mtroot', None, args))

    def login(self, user):
        """Run afsutil login."""
        c = self.config
        args = []
        if not user:
            user = c.optstr('cell', 'admin', 'admin')
        if user:
            args.append('--user')
            args.append(user)
        cell = c.optstr('cell', 'name')
        if cell:
            args.append('--cell')
            args.append(cell)
        realm = c.optstr('kerberos', 'realm')
        if realm:
            args.append('--realm')
            args.append(realm)
        aklog = c.optstr('variables', 'aklog')
        if aklog:
            args.append('--aklog')
            args.append(aklog)
        if c.optbool('kerberos', 'akimpersonate'):
            args.append('--akimpersonate')
            keytab = c.optkeytab('fake')
            if keytab:
                args.append('--keytab')
                args.append(keytab)
        else:
            keytab = c.optkeytab('user')
            if keytab:
                args.append('--keytab')
                args.append(keytab)
        self.execute(_afsutil('login', None, args))

    def remove(self):
        """Run afsutil remove."""
        args = ['--purge']
        self.execute(_sudo(_afsutil('remove', None, args)))

class RemoteNode(Node):
    """Remote node (host) to be setup."""

    def __init__(self, name, config, **kwargs):
        """Initialize the remote node.

        name: hostname of this remote node
        config: parsed configuration
        """
        Node.__init__(self, name, config, **kwargs)
        self.ident = config.optstr('ssh', 'keyfile')

    def execute(self, args):
        """Run the remote command."""
        ssh(self.name, args, ident=self.ident, dryrun=self.dryrun)


def _get_progress(**kwargs):
    quiet = kwargs.get('quiet', False)
    verbose = kwargs.get('verbose', False)
    dryrun = kwargs.get('dryrun', False)
    if quiet:
        progress = NoMessage
    elif verbose or dryrun:
        progress = SimpleMessage
    else:
        progress = ProgressMessage
    return progress

def _aklog_workaround_check(config):
    # Sadly, akimpersonate is broken on the master branch at this time. To
    # workaround this users must setup an aklog 1.6.10+ in some directory
    # and then set a option to specify the location. Since this is easy to
    # get wrong, do a sanity check up front, at least until aklog is fixed.
    aklog = config.optstr('variables', 'aklog')
    if aklog is None:
        sys.stderr.write("Warning: The akimpersonate feature is enabled but the aklog option\n")
        sys.stderr.write("         is not set. See the README.md for more information about\n")
        sys.stderr.write("         testing without Kerberos.\n")

def _get_nodes(config, **kwargs):
    """Get nodes for setup and teardown."""
    nodes = {
        'all': [],
        'install': [],
        'servers': [],
        'clients': [],
    }
    for name in config.opthostnames():
        if islocal(name):
            node = Node(name, config, **kwargs)
        else:
            node = RemoteNode(name, config, **kwargs)
        nodes['all'].append(node)
        if node.installer:
            nodes['install'].append(node)
        if node.is_server:
            nodes['servers'].append(node)
        if node.is_client:
            nodes['clients'].append(node)
    return nodes

def setup(config, **kwargs):
    """Setup OpenAFS client and servers and create a test cell."""
    logger.info("setup starting")

    akimpersonate = config.optbool('kerberos', 'akimpersonate')
    # Be sure to use the same secret value on every node.
    if akimpersonate:
        _aklog_workaround_check(config)
        secret = config.optstr('kerberos', 'secret')
        if secret is None:
            random = base64.b64encode(os.urandom(32))
            config.set_value('kerberos', 'secret', random)

    progress = _get_progress(**kwargs)
    nodes = _get_nodes(config, **kwargs)

    if not nodes['all']:
        logger.error("No nodes configured!")
        return

    if nodes['install']:
        with progress("Installing"):
            for node in nodes['install']:
                node.install()

    if akimpersonate:
        with progress("Creating service key"):
            for node in nodes['all']:
                node.keytab_create()

    if nodes['servers']:
        with progress("Setting service key"):
            for node in nodes['servers']:
                node.keytab_setkey()

    if nodes['servers']:
        with progress("Starting servers"):
            for node in nodes['servers']:
                node.start('server')
        with progress("Creating new cell"):
            node = nodes['servers'][0]
            node.newcell()

    if nodes['clients']:
        with progress("Starting clients"):
            for node in nodes['clients']:
                node.start('client')
        with progress("Mounting root volumes"):
            node = nodes['clients'][0]
            node.mtroot()

    logger.info("setup done")

def login(config, **kwargs):
    """Obtain a token.

    The test harness will obtain and remove tokens as needed for the RF
    tests. This sub-command is a useful short cut to get a token for
    the configured admin user.
    """
    user = kwargs.pop('user', config.optstr('cell', 'admin', 'admin'))
    node = Node('localhost', config, **kwargs)
    progress = _get_progress(**kwargs)
    with progress("Obtaining token for %s" % (user)):
        node.login(user)

def test(config, **kwargs):
    """Run the Robotframework test suites."""
    akimpersonate = config.optbool('kerberos', 'akimpersonate')
    if akimpersonate:
        _aklog_workaround_check(config)

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
        'AFS_AKIMPERSONATE:%s' % akimpersonate,
        'KRB_REALM:%s' % config.get('kerberos', 'realm'),
        'KRB_AFS_KEYTAB:%s' % keytab,
    ]
    if config.has_section('variables'):
        for o,v in config.items('variables'):
            variable.append("%s:%s" % (o.upper(), v))

    # Determine tests to exclude.
    exclude = config.get('run', 'exclude_tags').split(',')
    gfind = config.optstr('variables', 'gfind')
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

def teardown(config, **kwargs):
    """Uninstall and purge files."""
    logger.info("teardown starting")
    akimpersonate = config.optbool('kerberos', 'akimpersonate')
    progress = _get_progress(**kwargs)
    nodes = _get_nodes(config, **kwargs)

    if nodes['clients']:
        with progress("Stopping clients"):
            for node in nodes['clients']:
                node.stop('client')

    if nodes['servers']:
        with progress("Stopping servers"):
            for node in nodes['servers']:
                node.stop('server')

    if nodes['install']:
        with progress("Uninstalling"):
            for node in nodes['install']:
                node.remove()

    if akimpersonate:
        with progress("Removing service key"):
            for nodes in nodes['all']:
                node.keytab_destroy()

    logger.info("teardown done")

