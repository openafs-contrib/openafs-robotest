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
import tools.setup
import robot.run

def usage():
    print "usage: run-tests"

def main(args):
    try:
        import settings
    except ImportError:
        print "Please do `./run setup' first."
        sys.exit(1)
    try:
        opts, args = getopt.getopt(args, "h", ["help"])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err))
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        else:
            assert False, "unhandled option"

    # Setup paths for local libraries and keywords.
    for name in ['./resources', './libraries']:
        if not os.path.isdir(name):
            raise AssertionError("Directory '%s' is missing! (Wrong current working directory?)" % name)
        else:
            sys.path.append(name)

    # Create directories for output and input.
    for name in ['site', settings.RF_OUTPUT]:
        if not os.path.exists(name):
            os.makedirs(name)
        elif not os.path.isdir(name):
            raise AssertionError("File '%s' is in the way!" % (name))

    # Run the tests.
    rc = robot.run(
        "tests",
        variable="HOSTNAME:%s" % os.uname()[1],
        variablefile="settings.py",
        outputdir=settings.RF_OUTPUT,
        loglevel=settings.RF_LOGLEVEL,
        runemptysuite=True,
    )
    return rc

if __name__ == "__main__":
   sys.exit(main(sys.argv[1:]))
