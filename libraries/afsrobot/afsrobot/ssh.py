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
import logging
import subprocess
import shlex
from afsrobot.config import islocal
from afsutil.system import sh, CommandFailed

logger = logging.getLogger(__name__)

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
        logger.error("Skipping ssh-keygen; file %s already exists." % (keyfile))
        return 1
    logger.info("Creating ssh key file %s." % (keyfile))
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
        logger.info("Reading identities from file '%s'." % (keyfile))
        with open(keyfile, 'r') as f:
            key = f.read()
    except Exception as e:
        logger.error("Cannot read ssh public key %s; %s." % (keyfile, e))
        return 1
    if len(key) == 0:
        logger.error("No identities found in '%s'." % (keyfile))
        return 1
    for hostname in config.opthostnames():
        if islocal(hostname):
            logger.info("Skipping local host '%s'." % (hostname))
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
        logger.info("Copying ssh identities in '%s' to host '%s'." % (keyfile, hostname))
        p = subprocess.Popen(['ssh', hostname, script], stdin=subprocess.PIPE)
        p.stdin.write(key)
        p.stdin.close()
        code = p.wait()
        if code != 0:
            logger.error("Failed to copy ssh identities to host '%s'; exit code %d." % (hostname, code))
            return 1
    return 0

def check(config, check_sudo=True, **kwargs):
    """Check ssh access to the remote hosts."""
    failed = []
    keyfile = config.optstr('ssh', 'keyfile', required=True)
    if not keyfile:
        logger.error("Missing value for keyfile.")
        return 1
    if not os.access(keyfile, os.F_OK):
        logger.error("Cannot access keyfile %s." % (keyfile))
        return 1
    for hostname in config.opthostnames():
        logger.debug("hostname=%s", hostname)
        if islocal(hostname):
            logger.debug("skipping local host %s", hostname)
            continue
        logger.info("Checking ssh access to host %s" % (hostname))
        try:
            ssh(hostname, ['uname', '-a'], ident=keyfile)
        except CommandFailed:
            failed.append(hostname)
            continue
        if not check_sudo:
            continue
        try:
            ssh(hostname, _sudo(['afsutil', 'version']), ident=keyfile)
        except CommandFailed:
            failed.append(hostname)
    if failed:
        logger.error("Failed to access hosts: %s" % (",".join(failed)))
        return 1
    return 0

def copy(config, source, dest, quiet=False, exclude='', sudo=False, local=False, **kwargs):
    """Copy a file to the remote hosts."""
    keyfile = config.optstr('ssh', 'keyfile', required=True)
    script = "/bin/sh -c 'cat > %s'" % (dest)
    if sudo:
        script = 'sudo -n %s' % (script)
    try:
        with open(source, 'r') as f:
            data = f.read()
    except Exception as e:
        logger.error("Cannot read file %s: %s." % (source, e))
        return 1
    code = 0
    for hostname in config.opthostnames():
        if hostname in exclude:
            continue
        if islocal(hostname):
            if local:
                if not quiet:
                    logger.info("Copying file %s to localhost:%s" % (source, dest))
                if sudo:
                    sh('sudo', '-n', 'cp', source, dest)
                else:
                    sh('cp', source, dest, quiet=True)
        else:
            if not quiet:
                logger.info("Copying file %s to %s:%s" % (source, hostname, dest))
            args = ['ssh', '-q', '-t', '-o', 'PasswordAuthentication=no', '-i', keyfile, hostname, script]
            p = subprocess.Popen(args, stdin=subprocess.PIPE)
            p.stdin.write(data)
            p.stdin.close()
            code = p.wait()
            if code != 0:
                logger.error("Failed to copy file to host '%s'; exit code %d." % (hostname, code))
                break
    return code

def execute(config, command, exclude='', quiet=False, sudo=False, local=False, **kwargs):
    """Run a command on each remote host."""
    keyfile = config.optstr('ssh', 'keyfile', required=True)
    if not command:
        logger.error("Missing command")
        return 1
    exclude = exclude.split(',')
    args = shlex.split(command)  # Note: shlex handles quoting properly.
    if sudo:
        args = _sudo(args)
    if not keyfile:
        logger.error("Missing value for keyfile.")
        return 1
    if not os.access(keyfile, os.F_OK):
        logger.error("Cannot access keyfile %s." % (keyfile))
        return 1
    code = 0
    for hostname in config.opthostnames():
        if hostname in exclude:
            continue
        if islocal(hostname):
            if local:
                try:
                    sh(*args, quiet=False, output=False)
                except CommandFailed as e:
                    logger.error("local command failed: %s" % (e.out))
                    code = e.code
                    break
        else:
            try:
                ssh(hostname, args, ident=keyfile)
            except CommandFailed as e:
                logger.error("remote command failed; host=%s: %s" % (hostname, e.out))
                code = e.code
                break
    return code
