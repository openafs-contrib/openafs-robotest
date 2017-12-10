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
import socket
import robot.run
from afsutil.system import sh
from afsrobot.config import islocal
from afsrobot.ssh import ssh

logger = logging.getLogger(__name__)

PROGRAMS = (
    'bosserver',
    'ptserver',
    'vlserver',
    'fileserver',
    'volserver',
    'salvager',
    'dafileserver',
    'davolserver',
    'salvageserver',
    'dasalvager',
)

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
        if name is None or name == '' or name == 'localhost':
            name = socket.gethostname()
        self.name = name
        assert(self.name)
        self.config = config
        self.name = name
        self.dryrun = kwargs.get('dryrun', False)
        # Get the config section for this node.
        self.section = None
        for section in config.sections():
            if section.startswith('host.'):
                if config.optstr(section, 'name') == name:
                    self.section = section
                    break
        if self.section is None:
            raise ValueError("Missing config section for host %s" % name)
        self.afsutil = self.opt('afsutil', 'afsutil') # path to afsutil on this node
        self.installer = config.optstr(self.section, 'installer', default=None)
        self.is_database = name in config.optstr('cell', 'db').split(',')
        self.is_fileserver = name in config.optstr('cell', 'fs').split(',')
        self.is_client = name in config.optstr('cell', 'cm').split(',')

        # Get the paths to commands on this host given in the config file.
        self.paths = {}
        sections = ['paths']
        paths = config.optstr(self.section, 'paths', default=self.installer)
        if paths:
            sections.append('paths.'+paths)
        sections.append(self.section+'.paths')
        for section in sections:
            if section in config.sections():
                for cmd,path in config.items(section):
                    self.paths[cmd] = path # overload

    def __repr__(self):
        return "Node(<" \
            "id={id} ," \
            "name='{self.name}', " \
            "installer='{self.installer}', " \
            "is_database={self.is_database}, " \
            "is_fileserver={self.is_fileserver}, " \
            "is_client={self.is_client}>)" \
            .format(id=id(self),self=self)

    def opt(self, name, default=None):
        return self.config.optstr(self.section, name, default=default)

    def _afsutil(self, cmd, args):
        """Build afsutil command line args."""
        afsutil = [self.afsutil]
        afsutil.append(cmd)
        if logger.getEffectiveLevel() == logging.DEBUG:
            afsutil.append('--verbose')
        return afsutil + args

    def execute(self, args):
        """Run the command."""
        sh(*args, prefix=self.name, quiet=False, output=False, dryrun=self.dryrun)

    def version(self):
        """Run afsutil version."""
        self.execute((self._afsutil('version', [])))

    def install(self):
        """Run afsutil install."""
        c = self.config
        args = []
        args.append('--components')
        if self.is_database or self.is_fileserver:
            args.append('server')
        if self.is_client:
            args.append('client')
        dist = self.opt('installer', default='transarc')
        args.append('--dist')
        args.append(dist)
        if dist == 'transarc':
            dest = self.opt('dest')
            if dest:
                args.append('--dir')
                args.append(dest)
        elif dist == 'rpm':
            rpms = self.opt('rpms')
            if rpms:
                args.append('--dir')
                args.append(rpms)
        cell = c.optstr('cell', 'name')
        if cell:
            args.append('--cell')
            args.append(cell)
        hosts = c.optstr('cell', 'db').split(',')
        if hosts:
            args.append('--hosts')
            args += hosts
        realm = c.optstr('kerberos', 'realm')
        if realm:
            args.append('--realm')
            args.append(realm)
        csdb = self.opt('csdb')
        if csdb:
            args.append('--csdb')
            args.append(csdb)
        args.append('--force')
        for program in ('afsd', 'bosserver'):
            options = self.opt(program)
            if options is None:
                options = c.optstr('cell', program)
            if options is not None:
                args.append('-o')
                args.append("%s=%s" % (program, options))
        pre = self.opt('pre_install')
        if pre:
            args.append('--pre')
            args.append(pre)
        post = self.opt('post_install')
        if post:
            args.append('--post')
            args.append(post)
        self.execute(_sudo(self._afsutil('install', args)))

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
        keytab = c.optstr('kerberos', 'fake')
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
        self.execute(_sudo(self._afsutil('ktcreate', args)))

    def keytab_setkey(self):
        """Run afsutil keytab setkey."""
        c = self.config
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
        keytab = c.optstr('kerberos', name)
        if keytab:
            args.append('--keytab')
            args.append(keytab)
        keyformat = self.opt('keyformat')
        if keyformat:
            args.append('--format')
            args.append(keyformat)
        self.execute(_sudo(self._afsutil('ktsetkey', args)))

    def keytab_destroy(self):
        """Run afsutil keytab destroy."""
        c = self.config
        if not c.optbool('kerberos', 'akimpersonate'):
            raise AssertionError('Trying to get fakekey options without akimpersonate.')
        args = []
        keytab = c.optstr('kerberos', 'fake')
        if keytab:
            args.append('--keytab')
            args.append(keytab)
        args.append('--force')
        self.execute(_sudo(self._afsutil('ktdestroy', args)))

    def start(self, comp):
        """Run afsutil start."""
        self.execute(_sudo(self._afsutil('start', [comp])))

    def stop(self, comp):
        """Run afsutil stop."""
        self.execute(_sudo(self._afsutil('stop', [comp])))

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
        fs = c.optstr('cell', 'fs').split(',')
        if fs:
            args.append('--fs')
            args += fs
        db = c.optstr('cell', 'db').split(',')
        if db:
            args.append('--db')
            args += db
        for program in PROGRAMS:
            options = c.optstr('cell', program)
            if options is not None:
                args.append('-o')
                args.append("%s=%s" % (program, options))
        for hostname in set(fs + db):
            section = c.get_host_section(hostname)
            for program in PROGRAMS:
                options = c.optstr(section, program)
                if options is not None:
                    args.append('-o')
                    args.append("%s.%s=%s" % (hostname, program, options))
        self.execute(_sudo(self._afsutil('newcell', args)))

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
            keytab = c.optstr('kerberos', 'fake')
            if keytab:
                args.append('--keytab')
                args.append(keytab)
        else:
            keytab = c.optstr('kerberos', 'user')
            if keytab:
                args.append('--keytab')
                args.append(keytab)
        fs = c.optstr('cell', 'fs').split(',')
        if fs:
            args.append('--fs')
            args += fs
        aklog = c.optstr('test', 'aklog')
        if aklog:
            args.append('--aklog')
            args.append(aklog)
        options = self.opt('afsd')
        if options is None:
            options = c.optstr('cell', 'afsd')
        if options is not None:
            args.append('-o')
            args.append("afsd=%s" % (options))
        self.execute(self._afsutil('mtroot', args))

    def login(self, user):
        """Run afsutil login."""
        c = self.config
        args = []
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
        aklog = c.optstr('test', 'aklog')
        if aklog:
            args.append('--aklog')
            args.append(aklog)
        if c.optbool('kerberos', 'akimpersonate'):
            args.append('--akimpersonate')
            keytab = c.optstr('kerberos', 'fake')
            if keytab:
                args.append('--keytab')
                args.append(keytab)
        else:
            keytab = c.optstr('kerberos', 'user')
            if keytab:
                args.append('--keytab')
                args.append(keytab)
        self.execute(self._afsutil('ktlogin', args))

    def remove(self):
        """Run afsutil remove."""
        args = ['--purge']
        pre = self.opt('pre_remove')
        if pre:
            args.append('--pre')
            args.append(pre)
        post = self.opt('post_remove')
        if post:
            args.append('--post')
            args.append(post)
        self.execute(_sudo(self._afsutil('remove', args)))

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
    aklog = config.optstr('test', 'aklog')
    if aklog is None:
        logger.warning("The akimpersonate feature is enabled but the aklog option")
        logger.warning("is not set. See the README.md for more information about")
        logger.warning("testing without Kerberos.")

def _get_nodes(config, **kwargs):
    """Get nodes for setup and teardown."""
    nodes = {
        'all': [],
        'install': [],
        'servers': [],
        'clients': [],
        'server': None,
        'client': None,
    }
    names = dict()
    db = config.optstr('cell', 'db').split(',')
    fs = config.optstr('cell', 'fs').split(',')
    cm = config.optstr('cell', 'cm').split(',')
    for name in config.opthostnames():
        if name in names:
            continue  # avoid dupes
        if islocal(name):
            node = Node(name, config, **kwargs)
        else:
            node = RemoteNode(name, config, **kwargs)
        names[name] = node
        nodes['all'].append(node)
        if node.installer:
            nodes['install'].append(node)
        if name in db or name in fs:
            nodes['servers'].append(node)
        if name in cm:
            nodes['clients'].append(node)

    # Find the nodes for the client-side and server-side setup.
    for flavor in ('server', 'client'):
        name = None
        if nodes[flavor+'s']:
            name = nodes[flavor+'s'][0].name # First one of this type.
        name = config.optstr('setup', flavor, default=name)
        if name:
            nodes[flavor] = names[name]

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
        with progress("Starting servers"):
            for node in nodes['servers']:
                node.start('server')

    node = nodes['server']
    if node:
        with progress("Creating new cell"):
            node.newcell()

    if nodes['clients']:
        with progress("Starting clients"):
            for node in nodes['clients']:
                node.start('client')

    node = nodes['client']
    if node:
        with progress("Mounting root volumes"):
            node.mtroot()

    logger.info("setup done")

def login(config, **kwargs):
    """Obtain a token.

    The test harness will obtain and remove tokens as needed for the RF
    tests. This sub-command is a useful short cut to get a token for
    the configured admin user.
    """
    user = kwargs.pop('user')
    if not user:
        user = config.optstr('cell', 'admin', 'admin')
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
    sys.path.append(os.path.join(config.get('test', 'libraries'), 'OpenAFSLibrary'))
    sys.path.append(config.get('test', 'resources'))

    # Create output dir if needed.
    output = config.optstr('test', 'output', required=True)
    if not os.path.isdir(output):
        os.makedirs(output)

    # Verify we have a afs service keytab.
    if config.optbool('kerberos', 'akimpersonate'):
        keytab = config.optstr('kerberos', 'fake')
    else:
        keytab = config.optstr('kerberos', 'afs')
    if not os.path.isfile(keytab):
        raise ValueError("Cannot find keytab file '%s'!\n" % keytab)

    # Additional variables.
    variable = [
        'AFS_CELL:%s' % config.get('cell', 'name'),
        'AFS_FILESERVERS:%s' % config.get('cell', 'fs'),
        'AFS_ADMIN:%s' % config.get('cell', 'admin'),
        'AFS_AKIMPERSONATE:%s' % akimpersonate,
        'KRB_REALM:%s' % config.get('kerberos', 'realm'),
        'KRB_AFS_KEYTAB:%s' % keytab,
    ]
    for o,v in config.items('test'):
        variable.append("%s:%s" % (o.upper(), v))

    # Determine tests to exclude.
    exclude = config.get('test', 'exclude').split(',')
    if not config.optstr('test', 'gfind'):
        logger.warning("Excluding 'requires-gfind'; gfind is not set in config.\n")
        exclude.append('requires-gfind')
    fs = config.optstr('cell', 'fs').split(',')
    if len(fs) < 2:
        exclude.append('requires-multi-fs')

    # Setup the rf options.
    tests = config.get('test', 'tests') # path to our tests
    options = {
        'report': 'index.html',
        'outputdir': output,
        'loglevel': config.get('test', 'loglevel'),
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
        logger.error("Tests failed.")
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

