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
import logging
import os
import socket
import StringIO
import sys
import afsutil.system

logger = logging.getLogger(__name__)

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

    def _afsrobot_root(self):
        """Return path to afsrobot installation.

        Note: AFSROBOT_ROOT env var must be set if installed to a custom path.
        """
        logger.debug("looking for afsrobot root directory")
        afsrobot_root = os.getenv('AFSROBOT_ROOT')
        if not afsrobot_root is None:
            logger.debug("found AFSROBOT_ROOT=%s", afsrobot_root)
            if not os.path.exists(afsrobot_root):
                raise AssertionError("AFSROBOT_ROOT dir %s is missing" % afsrobot_root)
            logger.debug("afsrobot_root=%s", afsrobot_root)
            return afsrobot_root
        afsrobot_root = '/usr/local/afsrobot'
        logger.debug("trying %s", afsrobot_root)
        if os.path.exists(afsrobot_root):
            logger.debug("afsrobot_root=%s", afsrobot_root)
            return afsrobot_root
        afsrobot_root = '/opt/afsrobot'
        logger.debug("trying %s", afsrobot_root)
        if os.path.exists(afsrobot_root):
            logger.debug("afsrobot_root=%s", afsrobot_root)
            return afsrobot_root
        afsrobot_root = os.path.expanduser("~/afsrobot")
        logger.debug("trying %s", afsrobot_root)
        if os.path.exists(afsrobot_root):
            logger.debug("afsrobot_root=%s", afsrobot_root)
            return afsrobot_root
        raise AssertionError("afsrobot directory not found.")

    def _afsrobot_data(self):
        """Return path to afsrobot data and logs."""
        afsrobot_data = os.path.expanduser("~/afsrobot");
        logger.debug("afsrobot_data=%s" % afsrobot_data)
        return afsrobot_data

    def _gfind(self):
        """Attempt to detect path to gnu/find, if one."""
        gfind = afsutil.system.detect_gfind()
        if gfind is None:
            gfind = '' # Convert None to empty string.
        return gfind

    def _get_defaults(self):
        """Determine default values for new configs."""
        defaults = {
            'AFSROBOT_ROOT': self._afsrobot_root(),
            'AFSROBOT_DATA': self._afsrobot_data(),
            'HOME': os.environ['HOME'],
            'HOSTNAME': socket.gethostname(),
            'GFIND': self._gfind(),
        }
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
        for k,v in self.items(section, raw=raw):
            out.write("%s = %s\n" % (k, v))

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
                out.write("[%s]\n" % section)
                self._print_section(out, section, raw)
                out.write("\n")

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

    def optcomponents(self, hostname):
        """List of components for install, start, and stop for this host.."""
        section = "host:%s" % (hostname)
        comp = []
        if self.optbool(section, 'isfileserver') or self.optbool(section, 'isdbserver'):
            comp.append('server')
        if self.optbool(section, 'isclient'):
            comp.append('client')
        return comp

def init(config, ini, **kwargs):
    afsrobot_data = os.path.expanduser("~/afsrobot");
    if not os.path.isdir(afsrobot_data):
        sys.stdout.write("Making data directory %s\n" % (afsrobot_data))
        os.makedirs(afsrobot_data)
    config = Config()
    config.load_defaults()
    if os.path.exists(ini):
        msg = "Updating config file"
        config.load_from_file(ini)
    else:
        msg = "Creating config file"
        if not os.path.isdir(os.path.dirname(ini)):
            sys.stdout.write("Making config file directory %s\n" % (os.path.dirname(ini)))
            os.makedirs(os.path.dirname(ini))
    sys.stdout.write("%s %s\n" % (msg, ini))
    config.save_as(ini)

def list(config, out, section, raw=False, sections=False, **kwargs):
    if sections and section is None:
       for name in config.sections():
           out.write("%s\n" % name)
    else:
        config.print_values(out, section, raw)

def set(config, section, option, value, **kwargs):
    try:
        config.set_value(section, option, value)
        config.save()
    except Exception as e:
        sys.stderr.write("Unable to set: %s\n" % (e))
        return 1

def unset(config, section, option, **kwargs):
    try:
        config.unset_value(section, option)
        config.save()
    except Exception as e:
        sys.stderr.write("Unable to remove: %s\n" % (e))
        return 1

