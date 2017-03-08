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

def ssh(hostname, args, keyfile=None, sudo=False):
    """Helper to run command on remote hosts using ssh."""
    if sudo:
        args.insert(0, "-n")  # requires NOPASSWD in sudoers
        args.insert(0, "sudo")
    command = subprocess.list2cmdline(args)
    if keyfile:  # passwordless
        args = ['ssh', '-q', '-t', '-i', keyfile, '-o', 'PasswordAuthentication no', hostname, command]
    else:
        args = ['ssh', '-q', hostname, command]
    return subprocess.call(args)

def generate_key(keyfile, keytype='rsa'):
    """Create a public/private key pair.

    Uses ssh-keygen to create the key files."""
    if os.access(keyfile, os.F_OK):
        # No not clobber the existing key file. (It can confuse the
        # ssh-agent.)
        sys.stderr.write("Key file %s already exists.\n" % (keyfile))
        return 1
    sys.stdout.write("Creating ssh key file %s.\n" % (keyfile))
    cmd = ['ssh-keygen', '-t', keytype, '-f', keyfile]
    code = subprocess.call(cmd)
    if code != 0:
        sys.stderr.write("ssh-keygen failed; exit code %d\n" % (code))
    return code

def _copyid(key, hostname):
    """Distribute the public key files to the remote host.

    Do not use ssh-copy-id, since that is not available everywhere. Instead
    copy the file using ssh. This assumes password authentication is available.
    """
    copyid = \
        "umask 077 ; " \
        "test -d ~/.ssh || mkdir ~/.ssh ; " \
        "cat >> ~/.ssh/authorized_keys && " \
        "(test -x /sbin/restorecon && " \
        "/sbin/restorecon ~/.ssh ~/.ssh/authorized_keys >/dev/null 2>&1 || " \
        "true)"
    p = subprocess.Popen(['ssh', hostname, copyid], stdin=subprocess.PIPE)
    p.stdin.write(key)
    p.stdin.close()
    return p.wait()

def distribute_key(keyfile, hostnames):
    """Distribute the public key files to the remote hosts.

    The key file should have been prevously created with ssh-keygen."""
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
    result = 0
    for hostname in hostnames:
        if islocal(hostname):
            sys.stdout.write("Skipping local host '%s'.\n" % (hostname))
            continue
        sys.stdout.write("Copying ssh identities in '%s' to host '%s'.\n" % (keyfile, hostname))
        code = _copyid(key, hostname)
        if code != 0:
            sys.stderr.write("Failed to copy ssh identities to host '%s'; exit code %d.\n" % (hostname, code))
            result = 1
    return result

def check_access(keyfile, hostnames, check_sudo=True):
    """Check ssh access to the remote hosts."""
    if not os.access(keyfile, os.F_OK):
        sys.stderr.write("Cannot access keyfile %s.\n" % (keyfile))
        return 1
    sys.stdout.write("Checking ssh access...\n")
    failed = False
    for hostname in hostnames:
        if islocal(hostname):
            continue
        sys.stdout.write("Checking access to host %s...\n" % (hostname))
        code = ssh(hostname, ['uname', '-a'], keyfile=keyfile, sudo=False)
        if code != 0:
            sys.stderr.write("Failed to ssh to host %s.\n" % (hostname))
            failed = True
            continue
        if check_sudo:
            code = ssh(hostname, ['uname', '-a'], keyfile=keyfile, sudo=True)
            if code != 0:
                sys.stderr.write("Failed to run passwordless sudo on host %s.\n" % (hostname))
                failed = True
                continue
    if failed:
        sys.stderr.write("Failed to access all hosts.\n");
        code = 1
    else:
        sys.stdout.write("Ok.\n");
        code = 0
    return code

def execute(keyfile, hostnames, command, exclude='', quiet=False, sudo=False):
    """Run a command on each remote host."""
    if not command:
        sys.stderr.write("Missing command")
        return 1
    exclude = exclude.split(',')
    cargs = shlex.split(command)  # Note: shlex handles quoting properly.
    if not os.access(keyfile, os.F_OK):
        sys.stderr.write("Cannot access keyfile %s.\n" % (keyfile))
        return 1
    code = 0
    for hostname in hostnames:
        if islocal(hostname):
            continue
        if hostname in exclude:
            continue
        if not quiet:
            sys.stdout.write("%s\n" % (hostname))
        code = ssh(hostname, cargs, keyfile=keyfile, sudo=sudo)
        if code != 0:
            sys.stderr.write("Failed to ssh to host %s.\n" % (hostname))
    return code

