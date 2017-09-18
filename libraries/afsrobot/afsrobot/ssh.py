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
import subprocess
import shlex
from afsrobot.config import islocal
from afsutil.system import sh, CommandFailed

def _sudo(args):
    """Build sudo command line args."""
    return ['sudo', '-n'] + args

def ssh(hostname, args, ident=None, dryrun=False):
    """Execute the remote command with ssh."""
    cmdline = subprocess.list2cmdline(args)
    args = ['ssh', '-q', '-t', '-o', 'PasswordAuthentication=no']
    if ident:
        args.append('-i')
        args.append(ident)
    args.append(hostname)
    args.append(cmdline)
    sh(*args, prefix=hostname, quiet=False, output=False, dryrun=dryrun)

def create(config, keyfile, keytype='rsa', **kwargs):
    """Create a public/private key pair.

    Run ssh-keygen to create the ssh ident files."""
    if os.access(keyfile, os.F_OK):
        # Do not clobber the existing key file; it will confuse
        # the ssh-agents.
        sys.stderr.write("Skipping ssh-keygen; file %s already exists.\n" % (keyfile))
        return 1
    sys.stdout.write("Creating ssh key file %s.\n" % (keyfile))
    args = ['ssh-keygen', '-t', keytype, '-f', keyfile]
    sh(*args, quiet=False, output=False)
    config.set_value('ssh', 'keyfile', keyfile)
    config.save()

def dist(config, **kwargs):
    """Distribute the public key files to the configured remote hosts.

    The key file should have been prevously created with the create()
    function.

    Password authentication must be available for each configured host.
    """
    keyfile = config.optstr('ssh', 'keyfile', required=True)
    if not keyfile.endswith(".pub"):
        keyfile += ".pub"
    try:
        sys.stdout.write("Reading identities from file '%s'.\n" % (keyfile))
        with open(keyfile, 'r') as f:
            key = f.read()
    except Exception as e:
        sys.stderr.write("Cannot read ssh public key %s; %s.\n" % (keyfile, e))
        return 1
    if len(key) == 0:
        sys.stderr.write("No identities found in '%s'.\n" % (keyfile))
        return 1
    hostnames = config.opthostnames()
    for hostname in hostnames:
        if islocal(hostname):
            sys.stdout.write("Skipping local host '%s'.\n" % (hostname))
            continue
        # Avoid ssh-copy-id since it is not available on all platforms. Instead
        # copy the file using a pipe over ssh and this shell script (based on
        # ssh-copy-id).
        script = \
        "umask 077 ; " \
        "test -d ~/.ssh || mkdir ~/.ssh ; " \
        "cat >> ~/.ssh/authorized_keys && " \
        "(test -x /sbin/restorecon && " \
        "/sbin/restorecon ~/.ssh ~/.ssh/authorized_keys >/dev/null 2>&1 || true)"
        sys.stdout.write("Copying ssh identities in '%s' to host '%s'.\n" % (keyfile, hostname))
        p = subprocess.Popen(['ssh', hostname, script], stdin=subprocess.PIPE)
        p.stdin.write(key)
        p.stdin.close()
        code = p.wait()
        if code != 0:
            sys.stderr.write("Failed to copy ssh identities to host '%s'; exit code %d.\n" % (hostname, code))
            return 1
    return 0

def check(config, check_sudo=True, **kwargs):
    """Check ssh access to the remote hosts."""
    failed = []
    keyfile = config.optstr('ssh', 'keyfile', required=True)
    hostnames = config.opthostnames()
    if not keyfile:
        sys.stderr.write("Missing value for keyfile.\n")
        return 1
    if not os.access(keyfile, os.F_OK):
        sys.stderr.write("Cannot access keyfile %s.\n" % (keyfile))
        return 1
    for hostname in hostnames:
        if islocal(hostname):
            continue
        sys.stdout.write("Checking ssh access to host %s\n" % (hostname))
        try:
            ssh(hostname, ['uname', '-a'], ident=keyfile)
        except CommandFailed:
            failed.append(hostname)
            continue
        if not check_sudo:
            continue
        try:
            ssh(hostname, _sudo(['id']), ident=keyfile)
        except CommandFailed:
            failed.append(hostname)
    if failed:
        sys.stderr.write("Failed to access hosts: %s\n" % (",".join(failed)))
        return 1
    return 0

def execute(config, command, exclude='', quiet=False, sudo=False, **kwargs):
    """Run a command on each remote host."""
    keyfile = config.optstr('ssh', 'keyfile', required=True)
    hostnames = config.opthostnames()
    if not command:
        sys.stderr.write("Missing command")
        return 1
    exclude = exclude.split(',')
    args = shlex.split(command)  # Note: shlex handles quoting properly.
    if sudo:
        args = _sudo(args)
    if not keyfile:
        sys.stderr.write("Missing value for keyfile.\n")
        return 1
    if not os.access(keyfile, os.F_OK):
        sys.stderr.write("Cannot access keyfile %s.\n" % (keyfile))
        return 1
    code = 0
    for hostname in hostnames:
        if islocal(hostname):
            continue
        if hostname in exclude:
            continue
        code = ssh(hostname, args, ident=keyfile)
        if code != 0:
            sys.stderr.write("Failed to ssh to host %s.\n" % (hostname))
    return code
