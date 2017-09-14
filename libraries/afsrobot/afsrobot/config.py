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

import ConfigParser
import os
import socket
import StringIO
import sys
import afsutil.system

# Configuration defaults.
DEFAULT_CONFIG_DATA = """
[paths]
doc = <AFSROBOT_ROOT>/doc
tests = <AFSROBOT_ROOT>/tests
libraries = <AFSROBOT_ROOT>/libraries
resources = <AFSROBOT_ROOT>/resources
html = <AFSROBOT_DATA>
log = <AFSROBOT_DATA>/log
output = <AFSROBOT_DATA>/output

[run]
exclude_tags = todo,bug,slow
log_level = INFO

[variables]
afs_dist = transarc
pag_onegroup = yes
gfind = <GFIND>

[cell]
name = robotest
user = robotest
admin = robotest.admin

[kerberos]
akimpersonate = yes
realm = ROBOTEST
fake_keytab = <AFSROBOT_DATA>/fake.keytab
afs_keytab = <AFSROBOT_DATA>/afs.keytab
user_keytab = <AFSROBOT_DATA>/user.keytab

[web]
port = 8000
foreground = no

[options]
dafs = yes
afsd = -dynroot -fakestat -afsdb
bosserver =
dafileserver = -d 1 -L
davolserver = -d 1

[ssh]
keyfile =

[host:<HOSTNAME>]
use = yes
installer = none
isfileserver = yes
isdbserver = yes
isclient = yes
keyformat = detect

"""

def islocal(hostname):
    """Return true if hostname is for the local system."""
    if hostname == 'localhost':
        return True
    if hostname == socket.gethostname():
        return True
    if hostname == socket.getfqdn():
        return True
    return False

class Config(ConfigParser.SafeConfigParser):
    """Config parser wrapper."""

    def __init__(self, **kwargs):
        """Initalize the configuration."""
        ConfigParser.SafeConfigParser.__init__(self)
        self.filename = None

    def load_from_string(self, string):
        """Load values from a string."""
        fp = StringIO.StringIO(string)
        self.readfp(fp)

    def _get_defaults(self):
        """Determine default values for new configs."""
        defaults = {
            'AFSROBOT_ROOT': '/usr/local/afsrobot',
            'AFSROBOT_DATA': os.path.join(os.environ['HOME'], 'afsrobot'),
            'HOME': os.environ['HOME'],
            'HOSTNAME': socket.gethostname(),
            'GFIND': '',
        }
        # Attempt to detect path to gnu/find, if one.
        gfind = afsutil.system.detect_gfind()
        if gfind:
            defaults['GFIND'] = gfind
        # Read global settings saved during install.
        settings = '/etc/afsrobot.rc'
        if os.path.exists(settings):
            with open(settings) as f:
                for line in f.read().splitlines():
                    line = line.strip()
                    if len(line) == 0:
                        continue
                    if line.startswith('#'):
                        continue
                    if not '=' in line:
                        continue
                    k,v = line.split('=',1)
                    v = v.strip('"')
                    defaults[k] = v
        return defaults

    def load_defaults(self):
        """Load default values."""
        text = DEFAULT_CONFIG_DATA
        defaults = self._get_defaults()
        for key in defaults.keys():
            text = text.replace("<{0}>".format(key), defaults[key])
        self.load_from_string(text)

    def load_from_file(self, filename):
        """Load values from a file."""
        ok = self.read(filename)
        if filename not in ok:
            raise AssertionError("Failed to read config file %s." % (filename))
        self.filename = filename

    def set_value(self, section, option, value):
        """Set an option value."""
        if section not in self.sections():
            self.add_section(section)
        self.set(section, option, value)

    def unset_value(self, section, option):
        """Remove an option value."""
        self.remove_option(section, option) # raise exception if not found.
        if len(self.items(section)) == 0:
            self.remove_section(section)

    def save_as(self, filename):
        """Save values to a file. Will overwrite an existing file."""
        with open(filename, 'w') as f:
            self.write(f)
        self.filename = filename

    def save(self):
        """Save values to the current file. load_from_file() or save_as() must
        be called sometime before this function."""
        if self.filename is None:
            raise AssertionError("No filename.")
        with open(self.filename, 'w') as f:
            self.write(f)

    def _print_section(self, out, section, raw):
        """Print one section to stdout."""
        out.write("[%s]\n" % section)
        for k,v in self.items(section, raw=raw):
            out.write("%s = %s\n" % (k, v))
        out.write("\n")

    def print_values(self, out=sys.stdout, section=None, raw=False):
        """Print the values to stdout.

        out:      output stream
        section:  section name to print [optional]
        raw:      do not expand %() interpolations
        """
        if section:
            if not self.has_section(section):
                sys.stderr.write("Section not found: %s\n" % (section))
                return 1
            self._print_section(out, section, raw)
        else:
            for section in self.sections():
                self._print_section(out, section, raw)

    def optstr(self, section, option, default=None, required=False):
        """Helper to lookup a configuration string option."""
        value = default
        try:
            value = self.get(section, option)
        except ConfigParser.NoSectionError:
            if required:
                raise ValueError("Required config section '%s' is missing while looking for option '%s'." % (section, option))
        except ConfigParser.NoOptionError:
            if required:
                raise ValueError("Required config option '%s' is missing in section '%s'." % (option, section))
        if required and len(value) == 0:
            raise ValueError("Required config option '%s' is empty in section '%s'." % (option, section))
        return value

    def optbool(self, section, option, default=False, required=False):
        """Helper to lookup a configuration boolean option."""
        value = default
        try:
            value = self.getboolean(section, option)
        except ConfigParser.NoSectionError:
            if required:
                raise ValueError("Required config section is missing; section=%s, option=%s." % (section, option))
        except ConfigParser.NoOptionError:
            if required:
                raise ValueError("Required config option is missing; section=%s, option=%s." % (section, option))
        return value

    def optkeytab(self, name):
        """Return the named keytab file."""
        return self.optstr('kerberos', '%s_keytab' % (name))

    def opthostnames(self, filter=None, lookupname=False):
        """Return a list of host sections."""
        hostnames = []
        for s in self.sections():
            if not s.startswith('host:'):
                continue
            hostname = s.replace('host:', '')
            if hostname == '':
                sys.stderr.write("Invalid config section name: %s\n" % (s))
                sys.exit(1)
            if not self.optbool(s, 'use', default='yes'):
                continue
            if filter is not None and not self.optbool(s, filter):
                continue
            if lookupname and islocal(hostname):
                hostname = socket.gethostname()
            hostnames.append(hostname)
        return hostnames

    def optfakekey(self):
        """Command line options for afsutil fakekey."""
        if not self.optbool('kerberos', 'akimpersonate'):
            raise AssertionError('Trying to get fakekey options without akimpersonate.')
        cell = self.optstr('cell', 'name')
        keytab = self.optkeytab('fake')
        realm = self.optstr('kerberos', 'realm')
        enctype = self.optstr('kerberos', 'enctype')
        secret = self.optstr('kerberos', 'secret')
        args = []
        if cell:
            args.append('--cell')
            args.append(cell)
        if keytab:
            args.append('--keytab')
            args.append(keytab)
        if realm:
            args.append('--realm')
            args.append(realm)
        if enctype:
            args.append('--enctype')
            args.append(enctype)
        if secret:
            args.append('--secret')
            args.append(secret)
        return args

    def optremovekey(self):
        """Command line options for afsutil keytab remove."""
        if not self.optbool('kerberos', 'akimpersonate'):
            raise AssertionError('Trying to get fakekey options without akimpersonate.')
        keytab = self.optkeytab('fake')
        args = []
        if keytab:
            args.append('--keytab')
            args.append(keytab)
        args.append('--force')
        return args

    def optlogin(self, user=None):
        """Command line options for afsutil login."""
        if not user:
            user = self.optstr('cell', 'admin', 'admin')
        cell = self.optstr('cell', 'name')
        realm = self.optstr('kerberos', 'realm')
        aklog = self.optstr('variables', 'aklog')
        args = []
        if user:
            args.append('--user')
            args.append(user)
        if cell:
            args.append('--cell')
            args.append(cell)
        if realm:
            args.append('--realm')
            args.append(realm)
        if aklog:
            args.append('--aklog')
            args.append(aklog)
        if self.optbool('kerberos', 'akimpersonate'):
            args.append('--akimpersonate')
            keytab = self.optkeytab('fake')
            if keytab:
                args.append('--keytab')
                args.append(keytab)
        else:
            keytab = self.optkeytab('user')
            if keytab:
                args.append('--keytab')
                args.append(keytab)
        return args

    def optcomponents(self, hostname):
        """List of components for install, start, and stop for this host.."""
        section = "host:%s" % (hostname)
        comp = []
        if self.optbool(section, 'isfileserver') or self.optbool(section, 'isdbserver'):
            comp.append('server')
        if self.optbool(section, 'isclient'):
            comp.append('client')
        return comp

    def optinstall(self, hostname):
        """Command line options for afsutil install."""
        section = "host:%s" % (hostname)
        hosts = self.opthostnames(filter='isdbserver', lookupname=True)
        args = []
        dist = self.optstr(section, 'installer', default='transarc')
        args.append('--dist')
        args.append(dist)
        comp = self.optcomponents(hostname)
        if comp:
            args.append('--components')
            args += comp
        if dist == 'transarc':
            dest = self.optstr(section, 'dest')
            if dest:
                args.append('--dir')
                args.append(dest)
        elif dist == 'rpm':
            rpms = self.optstr(section, 'rpms')
            if rpms:
                args.append('--dir')
                args.append(rpms)
        cell = self.optstr('cell', 'name')
        if cell:
            args.append('--cell')
            args.append(cell)
        if hosts:
            args.append('--hosts')
            args += hosts
        realm = self.optstr('kerberos', 'realm')
        if realm:
            args.append('--realm')
            args.append(realm)
        csdb = self.optstr(section, 'csdb')
        if csdb:
            args.append('--csdb')
            args.append(csdb)
        args.append('--force')
        if self.has_section('options'):
            for k,v in self.items('options'):
                if k == 'afsd' or k == 'bosserver':
                    args.append('-o')
                    args.append("%s=%s" % (k,v))
        return args

    def optsetkey(self, hostname):
        section = "host:%s" % (hostname)
        args = []
        cell = self.optstr('cell', 'name')
        if cell:
            args.append('--cell')
            args.append(cell)
        realm = self.optstr('kerberos', 'realm')
        if realm:
            args.append('--realm')
            args.append(realm)
        if self.optbool('kerberos', 'akimpersonate'):
            name = 'fake'
        else:
            name = 'afs'
        keytab = self.optkeytab(name)
        if keytab:
            args.append('--keytab')
            args.append(keytab)
        keyformat = self.optstr(section, 'keyformat')
        if keyformat:
            args.append('--format')
            args.append(keyformat)
        return args

    def optnewcell(self):
        """Command line options for afsutil newcell."""
        realm = self.optstr('kerberos', 'realm')
        fs = self.opthostnames(filter='isfileserver', lookupname=True)
        db = self.opthostnames(filter='isdbserver', lookupname=True)
        args = [
            '--cell', self.optstr('cell', 'name', 'localcell'),
            '--admin', self.optstr('cell', 'admin', 'admin'),
        ]
        if realm:
            args.append('--realm')
            args.append(realm)
        if fs:
            args.append('--fs')
            args += fs
        if db:
            args.append('--db')
            args += db
        # Server command line options.
        if self.has_section('options'):
            for k,v in self.items('options'):
                args.append('-o')
                args.append("%s=%s" % (k,v))
        return args

    def optmtroot(self):
        """Command line options for afsutil mtroot."""
        realm = self.optstr('kerberos', 'realm')
        akimpersonate = self.optbool('kerberos', 'akimpersonate')
        fs = self.opthostnames(filter='isfileserver', lookupname=True)
        aklog = self.optstr('variables', 'aklog')
        args = [
            '--cell', self.optstr('cell', 'name', 'localcell'),
            '--admin', self.optstr('cell', 'admin', 'admin'),
            '--top', 'test',
        ]
        if realm:
            args.append('--realm')
            args.append(realm)
        if akimpersonate:
            args.append('--akimpersonate')
            keytab = self.optkeytab('fake')
            if keytab:
                args.append('--keytab')
                args.append(keytab)
        else:
            keytab = self.optkeytab('user')
            if keytab:
                args.append('--keytab')
                args.append(keytab)
        if fs:
            args.append('--fs')
            args += fs
        if aklog:
            args.append('--aklog')
            args.append(aklog)
        if self.has_section('options'):
            for k,v in self.items('options'):
                args.append('-o')
                args.append("%s=%s" % (k,v))
        return args

