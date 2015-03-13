#!/usr/bin/env python
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
import getopt
import os
import robot.run

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
site = os.path.join(root, 'site')
resources = os.path.join(root, 'resources')
libraries = os.path.join(root, 'libraries')
sys.path.append(root)
sys.path.append(libraries)
sys.path.append(resources)

try:
    import settings
except ImportError:
    print "Please run `./run.py setup'."
    sys.exit(1)

def usage():
    print "usage: ./run.py tests [-s <suites>] [-x <tags>]"

def main(args):
    rf = {
        "variable": [
            "ROOT:%s" % root,
            "SITE:%s" % site,
        ],
        "variablefile": [
            os.path.join(root,"settings.py"),
            os.path.join(root,"resources/sysinfo.py"),
        ],
        "outputdir": settings.RF_OUTPUT,
        "loglevel": settings.RF_LOGLEVEL,
        "exclude": settings.RF_EXCLUDE,
        "runemptysuite": True,
    }
    try:
        opts, args = getopt.getopt(args, "hs:x:", ["help", "suite=", "exclude="])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err))
        sys.stderr.write("\n")
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o in ("-s", "--suite"):
            rf['suite'] = a.split(",")
        elif o in ("-x", "--exclude"):
            rf['exclude'] = a.split(",")
        else:
            raise AssertionError("Unhandled option: %s" % o)

    # Setup the path for our shared libraries.
    if settings.AFS_DIST == "transarc":
        os.environ['LD_LIBRARY_PATH'] = '/usr/afs/lib'

    # Create directories for output and input.
    if settings.RF_OUTPUT.startswith("."):
        output = os.path.abspath(os.path.join(root, settings.RF_OUTPUT))
    else:
        output = os.path.abspath(settings.RF_OUTPUT)
    for name in [site, output]:
        if not os.path.exists(name):
            os.makedirs(name)
        elif not os.path.isdir(name):
            raise AssertionError("File '%s' is in the way!" % (name))

    # Run the tests.
    rc = robot.run(os.path.join(root,"tests"), **rf)
    return rc

if __name__ == "__main__":
   sys.exit(main(sys.argv[1:]))
