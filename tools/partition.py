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
import getopt
import re
import subprocess


def create_fake_partition(id):
    """Create a pseudo vice partition for testing."""
    if not re.match(r'([a-z]|[a-h][a-z]|i[a-v])$', id):
        raise ValueError("Partition id is out of range: %s" % (id))
    path = "/vicep%s" % id
    if os.path.exists(path):
        if not os.path.isdir(path):
            raise AssertionError("File %s is in the way!" % path)
        return
    rc = subprocess.call(['sudo', '-n', 'mkdir', path])
    if rc:
        raise OSError(rc, "Failed to make directory.", path)
    aa = "/".join([path, "AlwaysAttach"])
    rc = subprocess.call(['sudo', '-n', 'touch', aa])
    if rc:
        raise OSError(rc, "Failed to create file.", aa)

def usage():
    print "usage: python -m tools.partition create <id>"

def main(args):
    """Helper script to create partitions."""
    if len(args) != 2:
        usage()
        return 1
    command,id = args
    if command == 'create':
        try:
            create_fake_partition(id)
        except Exception as e:
            sys.stderr.write("Fail: %s\n" % (e))
            return 2
    else:
        sys.stderr.write("unknown command: %s\n" % command)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
