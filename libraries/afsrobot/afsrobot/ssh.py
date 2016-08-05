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

def distribute_key(keyfile, hostnames):
    """Distribute the public key files to the remote hosts.

    Uses ssh-copy-id to copy the key.
    The key file should have been prevously created with ssh-keygen."""
    if not os.access(keyfile, os.F_OK):
        sys.stderr.write("Cannot access keyfile %s.\n" % (keyfile))
        return 1
    for hostname in hostnames:
        if islocal(hostname):
            continue
        # Unfortunately ssh-copy-id will create a duplicate key in the authorized_keys
        # file if the key is already present. To keep this simple, for now, just
        # let it make the duplicates (these are test systems anyway).
        cmd = ['ssh-copy-id', '-i', keyfile, hostname]
        sys.stdout.write("Installing public key on %s...\n" % (hostname))
        code = subprocess.call(cmd)
        if code != 0:
            sys.stderr.write("Failed to copy ssh identity to host %s; exit code %d.\n" % (hostname, code))
            return code
    return 0

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
    for hostname in opthostnames:
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

