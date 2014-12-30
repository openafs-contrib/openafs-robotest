# Copyright (c) 2014, Sine Nomine Associates
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
import cmd
import glob
import getopt
import subprocess
from tools.download import download
from tools.partition import create_fake_partition
from libraries.Kerberos import Kerberos

try:
    import settings as old_settings
except:
    old_settings = None


INTRO = \
"""OpenAFS RoboTest Setup
Type help for information.
"""


SETTINGS = {
   'AFS_ADMIN':        {'t':'name', 'dv':"robotest.admin", 'desc':"Admin username"},
   'AFS_CELL':         {'t':'name', 'dv':"robotest",       'desc':"Test cell name"},
   'AFS_CSDB_DIST':    {'t':'path', 'dv':"",               'desc':"Extra CSDB Entries"},
   'AFS_DAFS':         {'t':'bool', 'dv':"true",           'desc':"Run DAFS fileserver"},
   'AFS_DIST':         {'t':'enum', 'dv':"transarc",       'desc':"Distribution style", 'e':('rhel6','suse','transarc')},
   'AFS_KEY_FILE':     {'t':'enum', 'dv':"KeyFileExt",     'desc':"Service key style", 'e':('KeyFile','rxkad.keytab','KeyFileExt')},
   'AFS_USER':         {'t':'name', 'dv':"robotest",       'desc':"Test username"},
   'DO_INSTALL':       {'t':'bool', 'dv':"true",           'desc':"Perform the installation"},
   'DO_REMOVE':        {'t':'bool', 'dv':"true",           'desc':"Perform the uninstallation"},
   'DO_TEARDOWN':      {'t':'bool', 'dv':"true",           'desc':"Perform the cell teardown"},
   'GTAR':             {'t':'path', 'dv':"/bin/tar",       'desc':"GNU tar utility"},
   'KADMIN_LOCAL':     {'t':'path', 'dv':"/usr/sbin/kadmin.local", 'desc':"Kerberos kadmin.local program"},
   'KADMIN':           {'t':'path', 'dv':"/usr/sbin/kadmin", 'desc':"Kerberos kadmin program"},
   'KDESTROY':         {'t':'path', 'dv':"/usr/bin/kdestroy", 'desc':"Kerberos kdestroy program."},
   'KINIT':            {'t':'path', 'dv':"/usr/bin/kinit", 'desc':"Kerberos kinit program."},
   'KLIST':            {'t':'path', 'dv':"/usr/bin/klist", 'desc':"Kerberos klist program."},
   'KRB_AFS_ENCTYPE':  {'t':'enum', 'dv':'aes256-cts-hmac-sha1-96', 'desc':"AFS service key encryption type", 'e':Kerberos().get_encryption_types()},
   'KRB_ADMIN_KEYTAB': {'t':'path', 'dv':"",               'desc':"Admin user keytab file."},
   'KRB_AFS_KEYTAB':   {'t':'path', 'dv':"",               'desc':"AFS service keytab file."},
   'KRB_REALM':        {'t':'name', 'dv':"ROBOTEST",       'desc':"The kerberos realm name."},
   'KRB_USER_KEYTAB':  {'t':'path', 'dv':"",               'desc':"Test user keytab."},
   'RF_LOGLEVEL':      {'t':'enum', 'dv':"INFO",           'desc':"RF Logging level", 'e':('TRACE','DEBUG','INFO','WARN')},
   'RF_OUTPUT':        {'t':'path', 'dv':"./output/",      'desc':"Location for RF reports and logs."},
   'RF_TESTBED':       {'t':'enum', 'dv':"",               'desc':"System type", 'e':('debian', 'rhel6')},
   'RPM_AFSRELEASE':   {'t':'name', 'dv':"",               'desc':"RPM release number"},
   'RPM_AFSVERSION':   {'t':'name', 'dv':"",               'desc':"AFS Version Number"},
   'RPM_PACKAGE_DIR':  {'t':'path', 'dv':"",               'desc':"Path the RPM packages"},
   'TRANSARC_DEST':    {'t':'path', 'dv':"",               'desc':"Directory for binaries when AFS_DIST is 'transarc'."},
   'TRANSARC_TARBALL': {'t':'path', 'dv':"",               'desc':"Tarball filename when AFS_DIST is 'transarc'."},
   'WEBSERVER_PORT':   {'t':'int',  'dv':8000,             'desc':"Results webserver port number."},
}



class Setting:
    def __init__(self, name, t='name', value=None, dv=None, desc=None, e=()):
        self.name = name
        self.value = None
        self.t = t
        self.dv = dv
        self.desc = desc
        self.e = e
        if not value is None:
            self.set(value)
        elif not dv is None:
            self.set(dv)

    def set(self, value):
        if self.t == 'bool':
            if value is None:
                self.value = False
            elif value.lower() in ['1', 'yes', 'true']:
                self.value = True
            elif value.lower() in ['0', 'no', 'false']:
                self.value = False
            else:
                sys.stderr.write("Expected 'true' or 'false' for %s.\n" % (self.name))
        elif self.t == 'int':
            self.value = int(value)
        else:
            self.value = value

    def reset(self):
        if not self.dv is None:
            self.set(self.dv)

    def emit(self, f):
        if self.t == 'bool':
            if self.value:
                v = 'True'
            else:
                v = 'False'
        elif self.t == 'int':
            if self.value:
                v = '%d' % self.value
            else:
                v = '0'
        else:
            if self.value:
                v = '"%s"' % self.value.replace('"', '\\"')
            else:
                v = '""'
        f.write("%-24s = %s\n" % (self.name, v))

class Settings:
    """The collection of setting values."""
    def __init__(self):
        """Intialize the setting collection.

        Start with default values and then overlay with the
        values in the existing settings.py file (if one).
        This preserves any extra user defined values in
        settings.py, even if they are not in the SETTINGS table."""
        self.saved = False
        self.settings = dict()
        for name in SETTINGS.keys():
            self.settings[name] = Setting(name, **SETTINGS[name])
        if old_settings:
            for name in dir(old_settings):
                if name.startswith('__') and name.endswith('__'):
                    continue  # skip module attrs
                value = "%s" % (getattr(old_settings, name))
                if name in self.settings:
                    self.settings[name].set(value)
                else:
                    self.settings[name] = Setting(name, value=value)

    def get_dict(self):
        settings = {}
        for name in self.settings.keys():
            settings[name] = self.settings[name].value
        return settings

    def list(self):
        seen = {}
        for name in sorted(self.settings.keys()):
            value = self.settings[name].value
            if value == '':
               value = '(empty)'
            sys.stdout.write("%18s  %s\n" % (name, value))

    def set(self, name, value):
        name = name.upper()
        if name in self.settings:
            self.settings[name].set(value)
        else:
            self.settings[name] = Setting(name, value=value)
        self.save()

    def get(self, name):
        name = name.upper()
        value = None
        if name in self.settings:
            value = self.settings[name].value
        return value

    def unset(self, name):
        name = name.upper()
        if name in self.settings:
            del self.settings[name.upper()]
        self.save()

    def reset(self):
        for setting in self.settings.values():
            setting.reset()
        self.save()

    def save(self):
        f = open("settings.py", "w+")
        f.write("# OpenAFS RobotTest Settings\n")
        f.write("# Use `./run setup' to change this file.\n")
        for name in sorted(self.settings.keys()):
            setting = self.settings[name]
            setting.emit(f)
        f.close()
        self.saved = True

class DummyLogger:
    def __init__(self, verbose=False):
        self.verbose = verbose
    def info(self, msg):
        if self.verbose:
            print "INFO:", msg
    def debug(self, msg):
        if self.verbose:
            print "DEBUG:", msg

class SetupShell(cmd.Cmd):

    def __init__(self, script=None, settings=None):
        if settings is None:
            settings = Settings()
        if script:
            cmd.Cmd.__init__(self, stdin=script)
            self.use_rawinput = False
            self.prompt = ''
            self.intro = ''
        else:
            cmd.Cmd.__init__(self)
            if sys.stdin.isatty():
                #self.cmdqueue.append('guided')
                self.prompt = '(setup): '
                self.intro = INTRO
            else:
                self.prompt = ''
                self.intro = ''
        self.doc_header = "Commands (Type help <command>)"
        self.settings = settings

    def _set(self, name, value):
        self.settings.set(name,value)

    def _get(self, name, default=None):
        """Get a setting value."""
        value = self.settings.get(name)
        if not value and default:
            value = default
        return value

    def emptyline(self):
        pass  # do not repeat last command

    def default(self, line):
        if not line.startswith("#"):
            cmd.Cmd.default(self, line)

    def _complete_value(self, text, values):
        if text:
            completions = [v for v in values if v.startswith(text)]
        else:
            completions = values
        return completions

    def _complete_filename(self, text, line, begidx, endidx):
        """Filename completion.

        Only the 'text' portion of the pathname is returned in the
        completion list. The underlying readline module parses
        the line into arguments with slashes and other separators, so
        we must use the 'line' string, 'begidx', and 'endidx' to determine
        the fixed portion of the argument, which mush not be included
        in the completions.

        Slashes are appended to directories to make it clear which
        completions are directories. This also reduces the number of
        tabs you need to hit while traversing directories.
        """
        arg_index = line.rfind(" ", 0, begidx)
        if arg_index == -1:
            return
        else:
           arg_index += 1
        fixed = line[arg_index:begidx]    # fixed portion of the argument
        arg = line[arg_index:endidx]      # arg is fixed + text
        completions = []
        for path in glob.glob(arg + '*'):
            if os.path.isdir(path) and path[-1] != os.sep:
                path += os.sep
            completions.append(path.replace(fixed, "", 1))
        return completions

    def help_quit(self):
        print "Quit program."
        self.syntax_quit()
    def syntax_quit(self):
        print "syntax: quit"
        print "alias: quit, exit, ^D"
    def do_quit(self, line):
        self.settings.save()
        return True
    do_exit = do_quit         # exit is an alias for quit
    help_exit = help_quit
    do_EOF = do_quit          # end of file implies quit
    help_EOF = help_quit

    def help_shell(self):
        print "Run a command using the shell."
        self.syntax_shell()
    def syntax_shell(self):
        print "syntax: shell <command-line>"
        print "alias: ! <command-line>"
    def do_shell(self, line):
        subprocess.call(line, shell=True)

    def help_call(self):
        print "Execute commands in a file."
        self.syntax_call()
    def syntax_call(self):
        print "syntax: call <filename>"
    def do_call(self, line):
        args = line.split()
        if len(args) != 1:
            print "syntax: call <filename>"
            return
        filename = args[0].strip()
        try:
            input_file = open(filename, "r")
        except IOError as e:
            sys.stderr.write("Unable to open input-file %s: %s\n" % (filename, e.message))
            return
        shell = SetupShell(script=input_file, settings=self.settings)
        shell.cmdloop()
        input_file.close()
    def complete_call(self, text, line, begidx, endidx):
        return self._complete_filename(text, line, begidx, endidx)

    def help_list(self):
        print "List setting names and values."
        self.syntax_list()
    def syntax_list(self):
        print "syntax: list"
    def do_list(self, line):
        self.settings.list()

    def help_set(self):
        print "Assign a setting value."
        self.syntax_set()
    def syntax_set(self):
        print "syntax: set <name> <value>"
        print "sets: <name>"
    def do_set(self, line):
        name,value,line = self.parseline(line)
        if not name or not value:
            self.syntax_set()
            return
        self.settings.set(name, value)
    def complete_set(self, text, line, begidx, endidx):
        m = re.match(r'set\s+(\w*)$', line)
        if m:
            name = m.group(1)
            if re.match(r'[a-z_]+$', name):
                names = [n.lower() for n in SETTINGS.keys()]
            else:
                names = SETTINGS.keys()
            return self._complete_value(text, names)
        m = re.match(r'set\s+(\w+)\s+\S*$', line)
        if m:
            name = m.group(1).upper()
            if name in SETTINGS and 't' in SETTINGS[name]:
                t = SETTINGS[name]['t']
                if t == 'path':
                    return self._complete_filename(text, line, begidx, endidx)
                elif t == 'bool':
                    return self._complete_value(text, ['true', 'false'])
                elif t == 'enum':
                    return self._complete_value(text, SETTINGS[name]['e'])

    def help_unset(self):
        print "Remove a setting."
        self.syntax_unset()
    def syntax_unset(self):
        print "syntax: unset <name>"
    def do_unset(self, line):
        name,value,line = self.parseline(line)
        if not name:
            self.syntax_unset()
            return
        self.settings.unset(name)

    def help_reset(self):
        print "Reset all settings to default values."
        self.syntax_reset()
    def syntax_reset(self):
        print "syntax: reset"
    def do_reset(self, line):
        self.settings.reset()

    def help_create_partition(self):
        print "Create a fake fileserver partition."
        self.syntax_create_partition()
    def syntax_create_partition(self):
        print "syntax: create_partition <id>"
        print "where <id> is a..z, aa..iv"
    def do_create_partition(self, line):
        args = line.split()
        if len(args) != 1:
            self.syntax_create_partition()
            return
        try:
            create_fake_partition(args[0])
        except Exception as e:
            sys.stderr.write("Fail: %s\n" % (e))

    def help_create_afs_keytab(self):
        print "Create a service key and write it to a keytab file."
        self.syntax_create_afs_keytab()
    def syntax_create_afs_keytab(self):
        print "syntax: create_afs_keytab [--keytab=<file>] [--enctype=<enctype>] [--verbose]"
        print "where <keytab> is keytab filename. default: site/afs.keytab"
        print "      <enctype> is a krb5 enctype. default: aes256-cts-hmac-sha1-96"
        print "requires: AFS_CELL, KRB_REALM"
        print "sets: KRB_AFS_ENCTYPE, KRB_AFS_KEYTAB"
    def do_create_afs_keytab(self, line):
        args = line.split()
        cell = self._get("AFS_CELL")
        if not cell:
            sys.stderr.write("AFS_CELL is required\n")
            return
        realm = self._get("KRB_REALM")
        if not realm:
            sys.stderr.write("KRB_REALM is required\n")
            return
        keytab = self._get("KRB_AFS_KEYTAB", './site/afs.keytab')
        enctype = self._get("KRB_AFS_ENCTYPE", 'aes256-cts-hmac-sha1-96')
        verbose = False
        try:
            opts, args = getopt.getopt(args, "", ['keytab=','enctype=','verbose'])
        except getopt.GetoptError as err:
            sys.stderr.write("error: %s\n" % (str(err)))
            self.syntax_create_afs_keytab()
            return
        for o, a in opts:
           if '--keytab' == o:
               keytab = a
           elif '--enctype' == o:
               enctype = a
           elif o == "--verbose":
               verbose = True
           else:
               raise AssertionError("Unhandled option")
        try:
            k = Kerberos()
            k._set_settings(self.settings.get_dict()) # for path to kadmin.local
            k._set_logger(DummyLogger(verbose=verbose))
            k.create_afs_service_keytab(keytab, cell, realm, enctype)
        except Exception as e:
            sys.stderr.write("Failed to create keytab: %s\n" % (e))
            return
        self._set("KRB_AFS_KEYTAB", keytab)
        self._set("KRB_AFS_ENCTYPE", enctype)

    def help_create_user_keytab(self):
        print "Create a principal key and write it to a keytab file."
        self.syntax_create_user_keytab()
    def syntax_create_user_keytab(self):
        print "syntax: create_user_keytab [--principal=<principal>] [--principal=<keytab>] [--admin] [--verbose]"
        print "where <principal> is the user principal name"
        print "      <keytab> is keytab filename"
        print "requires: AFS_CELL, KRB_REALM"
        print "sets: AFS_USER, KRB_USER_KEYTAB if --admin is not given"
        print "      AFS_ADMIN, KRB_ADMIN_KEYTAB if --admin is given"
    def do_create_user_keytab(self, line):
        args = line.split()
        principal = None
        keytab = None
        admin = False
        verbose = False
        cell = self._get("AFS_CELL")
        if not cell:
            sys.stderr.write("AFS_CELL is required\n")
            return
        realm = self._get("KRB_REALM")
        if not realm:
            sys.stderr.write("KRB_REALM is required\n")
            return
        try:
            opts, args = getopt.getopt(args, "", ['principal=', 'keytab=','admin','verbose'])
        except getopt.GetoptError as err:
            sys.stderr.write("error: %s\n" % (str(err)))
            self.syntax_create_afs_keytab()
            return
        for o, a in opts:
           if '--principal' == o:
               principal = a
           elif '--keytab' == o:
               keytab = a
           elif '--enctype' == o:
               enctype = a
           elif o == "--admin":
               admin = True
           elif o == "--verbose":
               verbose = True
           else:
               raise AssertionError("Unhandled option: %s" % o)
        if not principal:
            if admin:
                principal = self._get("AFS_ADMIN", "robotest/admin")
            else:
                principal = self._get("AFS_USER", "robotest")
        if not keytab:
            if admin:
                keytab = self._get("KRB_ADMIN_KEYTAB", "./site/admin.keytab")
            else:
                keytab = self._get("KRB_USER_KEYTAB", "./site/user.keytab")
        try:
            k = Kerberos()
            k._set_settings(self.settings.get_dict()) # for path to kadmin.local
            k._set_logger(DummyLogger(verbose=verbose))
            k.create_keytab(keytab, principal, realm)
        except AssertionError as e:
            sys.stderr.write("Error: %s\n" % (e))
            return
        if admin:
            self._set("AFS_ADMIN", principal)
            self._set("KRB_ADMIN_KEYTAB", keytab)
        else:
            self._set("AFS_USER", principal)
            self._set("KRB_USER_KEYTAB", keytab)

    def help_download(self):
        print "Download RPM files"
        self.syntax_download()
    def syntax_download(self):
        print "syntax: download <version> <platform> [<directory>]"
        print "where: <version> is the openafs version number; e.g. 1.6.10"
        print "       <platform> is one of: rhel5, rhel6, openSUSE_12.3"
        print "       <directory> is destination for downloads; default is ./site/rpms"
        print "sets: RPM_AFSRELEASE, RPM_AFSVERSION, RPM_PACKAGE_DIR"
    def do_download(self, line):
        args = line.split()
        if len(args) == 2:
            version,platform = args
            directory = self._get('RPM_PACKAGE_DIR', './site/rpms')
        elif len(args) == 3:
            version,platform,directory = args
        else:
            self.syntax_download()
            return
        options = {
            'dryrun': False,
            'directory': directory,
        }
        try:
            status = download(version, platform, **options)
        except Exception as e:
            sys.stderr.write("Fail: %s\n" % e.message)
            return
        self._set('RPM_AFSVERSION', version)
        self._set('RPM_PACKAGE_DIR', directory)
        # Determine the release number from the downloaded filenames.
        afsrelease = None
        for f in status['files']:
            m = re.match(r'openafs-\d+\.\d+\.\d+\-(\d+)\..*', os.path.basename(f))
            if m:
                afsrelease = m.group(1)
        if afsrelease:
            self._set('RPM_AFSRELEASE', afsrelease)
        else:
            sys.stderr.write("Failed to find rpm release!\n")

    def help_guided(self):
        print "Enter guided setup mode"
        self.syntax_guided(self)
    def syntax_guided(self):
        print "syntax: guided"
    def do_guided(self, line):
        stop = None
        while not stop:
            answer = raw_input("Now what? ")
            print "Are you kidding?", answer, "?"
            if "xyzzy" in answer:
                stop = True


def main(args):
    """Command line entry for the setup shell. """
    # Setup paths for local libraries.
    for name in ['./libraries']:
        if not os.path.isdir(name):
            raise AssertionError("Directory '%s' is missing! (Wrong current working directory?)" % name)
        else:
            sys.path.append(name)

    if len(args) == 0:
        shell = SetupShell()
        shell.cmdloop()
    elif len(args) == 1:
        filename = args[0]
        try:
            input_file = open(filename, "r")
        except IOError as e:
            sys.stderr.write("Unable to open input file '%s': %s, errno=%d\n" % \
                (filename, e.strerror, e.errno))
            return e.errno
        shell = SetupShell(script=input_file)
        shell.cmdloop()
        input_file.close()
    else:
       sys.stderr.write("usage: setup [filename]\n")
       return 1
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
