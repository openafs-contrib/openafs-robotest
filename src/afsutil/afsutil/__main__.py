# Copyright (c) 2014-2017 Sine Nomine Associates
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

"""OpenAFS utilities"""

from __future__ import print_function
import sys
from afsutil.cli import subcommand, argument, usage, dispatch
import afsutil.system
import afsutil.build

@subcommand()
def version(**args):
    """Print version"""
    from afsutil import __version__
    print("afsutil version", __version__)
    return 0

@subcommand()
def help(**args):
    "Print usage"
    return usage()

@subcommand(
    argument('--creds', help='path or url of repo creds',
                        default='/root/creds'),
    requires_root=True,
    )
def getdeps(**args):
    "Install build dependencies"
    from afsutil.getdeps import getdeps
    return getdeps(**args)

@subcommand(
    argument('--fix-hosts', help='fix /etc/hosts file by replacing loopback entry.',
                            action='store_true')
    )
def check(**args):
    "Check hostname"
    from afsutil.check import check
    return check(**args)

@subcommand(
    argument('--chdir', help='change to directory'),
    argument('--cf', help='configure options', default=afsutil.build.cfopts()),
    argument('--target', help='make target', default='all'),
    argument('--no-clean', help='do not run git clean',
                           dest='clean', default=True, action='store_false'),
    argument('--no-transarc-paths', help='do not use transarc paths', action='store_true'),
    argument('--no-modern-kmod-name', help='use the legacy kernel module name (linux only)', action='store_true'),
    argument('-j', '--jobs', help='parallel build jobs', default=afsutil.system.nproc()),
    argument('--srcdir', help='source code directory', default='.'),
    argument('--tarball', help='path and file name of dest tarball'),
    )
def build(**args):
    "Build binaries"
    from afsutil.build import build
    return build(**args)

@subcommand(
    argument('--chdir', help='change to directory'),
    requires_root=True,
    )
def reload(**args):
    "Reload the kernel module from the build tree"
    from afsutil.modreload import modreload
    return modreload(**args)

@subcommand(
    argument('--chdir', help='change to directory', metavar='<path>'),
    argument('--mock', help='build in mock chroot',
                           metavar='<chroot>', dest='chroot'),
    argument('--dstdir', help='where to place rpms (--mock only)',
                           metavar='<dstdir>'),
    argument('--clobber', help='rebuild and overwrite existing kmods (--mock only)',
                           action='store_true'),
    argument('--no-clean', help='do not clean after build (--mock only)', dest='autoclean', action='store_false'),
    argument('--build', help='what to build: all, srpm, userspace, kmods', metavar='<target>', default='all',
                        choices=['all','srpm','userspace','kmods']),
    argument('--csdb', help='CellServDB file path (default: download)', metavar='<csdb>'),
    argument('--spec', help='spec file path', metavar='<spec>'),
    argument('--version', help='target version number'),
    argument('--arch', help='target architecture, e.g. x86_64', metavar='<arch>'),
    argument('--kversion', help='linux kernel versions; may be given more than once',
                           metavar='<kernel-version>', dest='kversions',
                           nargs='+', action='append', default=[]),
    argument('--with', help='build with optional feature (e.g. --with kauth)',
                       dest='with_', metavar='<feature>',
                       nargs='+', action='append', default=[]),
    argument('--without', help='build without optional feature (e.g. --without kauth)',
                       metavar='<feature>',
                       nargs='+', action='append', default=[]),
    )
def package(**args):
    "Build packages"
    from afsutil.package import package
    return package(**args)

@subcommand(
    argument('--chdir', help='change to directory'),
    argument('--dist', help='distribution type',
                       choices=['transarc', 'rpm'], default='transarc'),
    argument('--dir', help='distribution directory'),
    argument('--components', help='components to install',
                             metavar='<name>',
                             choices=['client', 'server'],
                             nargs='+', default=['client', 'server']),
    argument('--cell', help='cell name', default='localcell'),
    argument('--hosts', help='cell service db hosts', nargs='+', default=[]),
    argument('--realm', help='realm name'),
    argument('--csdb', help='path to CellServDB.dist file for client'),
    argument('--force', help='overwrite existing files', action='store_true'),
    argument('-o', '--options', help="command line args: <name>=<value>",
                                action='append', nargs='+', default=[]),
    argument('--pre', help='pre-install command', dest='pre_install'),
    argument('--post', help='post-install command', dest='post_install'),
    requires_root=True,
    )
def install(**args):
    "Install binaries"
    from afsutil.install import install
    return install(**args)

@subcommand(
    argument('--dist', help='distribution type',
                       choices=['transarc', 'rpm'], default='transarc'),
    argument('--components', help='components to remove',
                             metavar='<name>', nargs='+',
                             choices=['client', 'server'],
                             default=['client', 'server']),
    argument('--purge', help='remove config and data too', action='store_true'),
    argument('--pre', help='pre-remove command', dest='pre_remove'),
    argument('--post', help='post-remove command', dest='post_remove'),
    requires_root=True,
    )
def remove(**args):
    "Remove binaries"
    from afsutil.install import remove
    return remove(**args)

@subcommand(
    argument('components', help='Services to start',
                           metavar='<name>', nargs='*',
                           default=['client','server']),
    requires_root=True,
    )
def start(**args):
    "Start AFS services"
    from afsutil.service import start
    return start(**args)

@subcommand(
    argument('components', help='services to stop',
                           metavar='<name>', nargs='*',
                           default=['client','server']),
    requires_root=True,
    )
def stop(**args):
    "Stop AFS services"
    from afsutil.service import stop
    return stop(**args)

@subcommand(
    argument('--keytab', help='keytab file to be created', default='/tmp/afs.keytab'),
    argument('--cell', help='cell name', default='localcell'),
    argument('--realm', help='realm name'),
    argument('--enctype', help='encryption type', default='aes256-cts-hmac-sha1-96'),
    argument('--secret', help='passphrase'),
    )
def ktcreate(**args):
    "Create a fake keytab"
    from afsutil.keytab import create
    return create(**args)

@subcommand(
    argument('--keytab', help='keytab file to be destroyed', default='/tmp/afs.keytab'),
    argument('--force', help='ignore errors', action='store_true'),
    )
def ktdestroy(**args):
    "Destroy a keytab"
    from afsutil.keytab import destroy
    return destroy(**args)

@subcommand(
    argument('--keytab', help="keytab file", default="/tmp/afs.keytab"),
    argument('--cell', help="cell name"),
    argument('--realm', help="realm name" ),
    argument('--confdir', help="server config directory", default="/usr/afs/etc"),
    argument('--format', help="key file format",
                         choices=['detect', 'transarc', 'rxkad-k5', 'extended'],
                         default='detect', dest='kformat'),
    argument('-n', '--dry-run', help="do not make changes",
                                dest='dryrun', action='store_true'),
    argument('-p', '--paths', help="command paths: <cmd>=<path-to-cmd>",
                                nargs='+', action='append', default=[]),
    requires_root=True,
    )
def ktsetkey(**args):
    "Add a service key from a keytab file"
    from afsutil.keytab import setkey
    return setkey(**args)

@subcommand(
    argument('--akimpersonate', help="print a ticket for the service key in the keytab", action='store_true'),
    argument('--keytab', help="keytab file", default="/tmp/afs.keytab"),
    argument('--user', help="user name", default="admin"),
    argument('--cell', help="cell name", default="localcell"),
    argument('--realm', help="realm name", default="LOCALCELL"),
    argument('-p', '--paths', help="command paths: <cmd>=<path-to-cmd>",
                                nargs='+', action='append', default=[]),
    )
def ktlogin(**args):
    "Obtain a token with a keytab"
    from afsutil.cell import login
    return login(**args)

@subcommand(
    argument('--cell', help="cell name", default='localcell'),
    argument('--realm', help="realm name"),
    argument('--admin', help="admin username", default='admin'),
    argument('--db', help="cell database hosts", nargs='+', default=[]),
    argument('--fs', help="cell fileserver hosts", nargs='+', default=[]),
    argument('-o', '--options', help="command line args: <[hostname:]name>=<value>",
                                nargs='+', action='append', default=[]),
    argument('-p', '--paths', help="command paths: <cmd>=<path-to-cmd>",
                                nargs='+', action='append', default=[]),
    requires_root=True,
    )
def newcell(**args):
    "Setup a new cell"
    from afsutil.cell import newcell
    return newcell(**args)

@subcommand(
    argument('--cell', help="cell name", default='localcell'),
    argument('--realm', help="realm name"),
    argument('--akimpersonate', help="print a ticket for admin user", action='store_true'),
    argument('--keytab', help="keytab file", default="/tmp/afs.keytab"),
    argument('--admin', help="admin username", default='admin'),
    argument('--fs', help="cell fileserver hosts", nargs='+', default=[]),
    argument('--top', help="top level volumes", nargs='+', default=[]),
    argument('--aklog', help="path to aklog program"),
    argument('--kinit', help="path to kinit program"),
    argument('-o', '--options', help="command line args: <name>=<value>",
                                action='append', nargs='+', default=[]),
    argument('-p', '--paths', help="command paths: <cmd>=<path-to-cmd>",
                                action='append', nargs='+', default=[]),
    )
def mtroot(**args):
    "Mount root volumes in a new cell"
    from afsutil.cell import mtroot
    return mtroot(**args)

@subcommand(
    argument('hostname', help="fileserver hostname"),
    argument('--keytab', help="keytab file", default="/tmp/afs.keytab"),
    argument('-o', '--options', help="command line args; <name>=<value>",
                                nargs='+', action='append', default=[]),
    argument('-p', '--paths', help="command paths: <cmd>=<path-to-cmd>",
                                action='append', nargs='+', default=[]),
    requires_root=True,
    )
def addfs(**args):
    "Add a new fileserver to a cell"
    from afsutil.cell import addfs
    return addfs(**args)

def main():
    return dispatch()

if __name__ == '__main__':
    sys.exit(main())
