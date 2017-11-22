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

"""System checks"""

import logging
import re
import socket
import sys
from afsutil.system import network_interfaces

logger = logging.getLogger(__name__)

def check_hosts_file():
    """Check for loopback addresses in the /etc/hosts file.

    Modern linux distros assign a loopback address to the hostname. While not
    strictly incorrect, this can confuse OpenAFS which gets our IP address from
    gethostbyname()."""
    result = True
    nr = 0
    hostname = socket.gethostname()
    with open('/etc/hosts', 'r') as f:
        for line in f.readlines():
            nr += 1
            if line.startswith('127.'):
                if hostname in line.split()[1:]:
                    sys.stderr.write(
                        "Warning: loopback address '%s' assigned to our hostname '%s' on line %d of /etc/hosts.\n" % \
                        (line.split()[0], hostname, nr))
                    result = False
    return result

def fix_hosts_file():
    hostname = socket.gethostname()
    ips = network_interfaces()
    if len(ips) == 0:
        raise AssertionError("Unable to detect any non-loopback network interfaces.")
    ip = ips[0]

    with open('/etc/hosts', 'r') as f:
        hosts = f.read()

    with open('/etc/hosts', 'w') as f:
        for line in hosts.splitlines():
            line = line.strip()
            if not re.search(r'\b%s\b' % (hostname), line):
                f.write("%s\n" % line)
        f.write("%s\t%s\n" % (ip, hostname))

def check_host_address():
    """Verify our hostname resolves to a useable address."""
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    ips = network_interfaces()
    if len(ips) == 0:
        sys.stderr.write("Warning: Unable to detect any non-loopback network interfaces.\n")
        return False
    if not ip in ips:
        sys.stderr.write("Warning: hostname '%s' resolves to '%s', not found in network interfaces: '%s'.\n" % \
                         (hostname, ip, " ".join(ips)))
        return False
    return True

def check(**kwargs):
    result = 0
    if not check_hosts_file():
        if kwargs['fix_hosts']:
            sys.stdout.write("Attempting to fix /etc/hosts file.\n")
            fix_hosts_file()
        else:
            result = 1
    if not check_host_address():
        result = 2
    return result
