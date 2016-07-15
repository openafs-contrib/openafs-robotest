#!/usr/bin/env python
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

import subprocess
import sys

class Command(object):
    """Run commands locally or remotely, with or without sudo.

    This helper class runs afsutil commands locally when the hostname is
    'localhost', otherwise uses ssh to run the command on the remote
    host. The output is sent to the log file.
    """

    def __init__(self, hostname, keyfile, logfile=None, verbose=False):
        self.hostname = hostname
        self.keyfile = keyfile
        self.logfile = logfile
        self.verbose = verbose

    def _exec(self, args): # args is a list here
        """Run the process and print the stdout and stderr to a log file."""
        if self.hostname != 'localhost':
            command = subprocess.list2cmdline(args)
            args = [
                'ssh', '-q', '-t', '-o', 'PasswordAuthentication no',
                '-i', self.keyfile, self.hostname, command
            ]
        cmdline = subprocess.list2cmdline(args)
        if self.logfile is None:
            if self.verbose:
                sys.stdout.writelines(["Running:", " ", cmdline, "\n"])
            code = subprocess.call(args)
        else:
            with open(self.logfile, 'a') as log:
                log.writelines(["localhost", " ", "INFO", " ", cmdline, "\n"])
                p = subprocess.Popen(args, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                with p.stdout:
                    for line in iter(p.stdout.readline, ''):
                        line = line.rstrip()
                        log.writelines([self.hostname, " ", line, "\n"])
                        log.flush()
                code = p.wait()
        return code

    def sh(self, command, *args):
        """Run the command."""
        return self._exec([command] + list(args))

    def sudo(self, command, *args):
        """Run the command as sudo."""
        return self._exec(['sudo', '-n', command] + list(args))

    def afsutil(self, command, *args):
        """Run the afsutil command on hostname as root."""
        args = list(args)
        if self.verbose:
            args.append('--verbose')
        return self._exec(['sudo', '-n', 'afsutil', command] + args)

