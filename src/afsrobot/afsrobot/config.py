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
[setup]
log = <AFSROBOT_DATA>/log/setup.log
loglevel = INFO

[run]
tests = <AFSROBOT_ROOT>/tests
libraries = <AFSROBOT_ROOT>/libraries
resources = <AFSROBOT_ROOT>/resources
output = <AFSROBOT_DATA>/output
exclude = bug,slow,rogue-avoidance
loglevel = INFO
host = <HOSTNAME>

[teardown]
log = <AFSROBOT_DATA>/log/teardown.log
loglevel = INFO

[login]
log = <AFSROBOT_DATA>/log/login.log
loglevel = INFO

[ssh]
keyfile = <HOME>/.ssh/afsrobot

[web]
docroot = <AFSROBOT_DATA>/output
port = 8000
foreground = no

[cell]
name = example.com
user = afsrobot
admin = afsrobot.admin
db = <HOSTNAME>
fs = <HOSTNAME>
cm = <HOSTNAME>
afsd = -dynroot -fakestat -afsdb
bosserver =
dafileserver =
davolserver =

[kerberos]
akimpersonate = yes
realm = EXAMPLE.COM
fake = <AFSROBOT_DATA>/fake.keytab
afs = <AFSROBOT_DATA>/afs.keytab
user = <AFSROBOT_DATA>/user.keytab

[paths]
gfind = <GFIND>

[paths.transarc]
aklog = /usr/afsws/bin/aklog
asetkey = /usr/afs/bin/asetkey
bos = /usr/afs/bin/bos
fs = /usr/afs/bin/fs
pagsh = /usr/afsws/bin/pagsh
pts = /usr/afs/bin/pts
rxdebug = /usr/afsws/etc/rxdebug
tokens = /usr/afsws/bin/tokens
udebug = /usr/afs/bin/udebug
unlog = /usr/afsws/bin/unlog
vos = /usr/afs/bin/vos

[paths.rhel]
aklog = /usr/bin/aklog
asetkey = /usr/sbin/asetkey
bos = /usr/bin/bos
fs = /usr/bin/fs
pagsh = /usr/bin/pagsh
pts = /usr/bin/pts
rxdebug = /usr/sbin/rxdebug
tokens = /usr/bin/tokens
udebug = /usr/bin/udebug
unlog = /usr/bin/unlog
vos = /usr/sbin/vos

[paths.suse]
aklog = /usr/bin/aklog
asetkey = /usr/sbin/asetkey
bos = /usr/sbin/bos
fs = /usr/bin/fs
pagsh = /usr/bin/pagsh
pts = /usr/bin/pts
rxdebug = /usr/sbin/rxdebug
tokens = /usr/bin/tokens
udebug = /usr/sbin/udebug
unlog = /usr/bin/unlog
vos = /usr/sbin/vos

[host.0]
name = <HOSTNAME>
installer = transarc
keyformat = detect
dafileserver = -d 1 -L
davolserver = -d 1
pag_onegroup = yes

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
                logger.error("Section not found: %s" % (section))
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

    def opthostnames(self):
        """Return a list of active hostnames."""
        hostnames = []
        for cat in ('db', 'fs', 'cm'):
            names = self.optstr('cell', cat)
            if names:
                for name in names.split(','):
                    if name not in hostnames:
                        hostnames.append(name)
        return hostnames

    def get_host_section(self, hostname):
        for section in self.sections():
            if not section.startswith('host.'):
                continue
            if hostname == self.optstr(section, 'name'):
                return section
        raise ValueError("Host section not found for hostname %s" % (hostname))


def init(config, cfg, **kwargs):
    afsrobot_data = os.path.expanduser("~/afsrobot");
    if not os.path.isdir(afsrobot_data):
        logger.info("Making data directory %s" % (afsrobot_data))
        os.makedirs(afsrobot_data)
    config = Config()
    config.load_defaults()
    if os.path.exists(cfg):
        msg = "Updating config file"
        config.load_from_file(cfg)
    else:
        msg = "Creating config file"
        if not os.path.isdir(os.path.dirname(cfg)):
            logger.info("Making config file directory %s" % (os.path.dirname(cfg)))
            os.makedirs(os.path.dirname(cfg))
    logger.info("%s %s" % (msg, cfg))
    config.save_as(cfg)

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
        logger.error("Unable to set: %s" % (e))
        return 1

def unset(config, section, option, **kwargs):
    try:
        config.unset_value(section, option)
        config.save()
    except Exception as e:
        logger.error("Unable to remove: %s" % (e))
        return 1

