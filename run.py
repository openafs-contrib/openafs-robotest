#!/usr/bin/env python
# Copyright (c) 2014, Sine Nomine Associates
# See LICENSE
#
# Must be run in the top level openafs-robotest directory.
#

import os
import sys
import tools.setup
import tools.tests
import tools.webserver

if not os.path.exists('./resources') or not os.path.exists('./libraries'):
   sys.stderr.write("Must be run in the top level directory.")
   sys.exit(1)

def usage():
    print "usage: ./run.py setup"
    print "       ./run.py tests"
    print "       ./run.py webserver"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
        rc = 1
    elif sys.argv[1] == 'setup':
        rc = tools.setup.main(sys.argv[2:])
    elif sys.argv[1] == 'tests':
        rc = tools.tests.main(sys.argv[2:])
    elif sys.argv[1] == 'webserver':
        rc = tools.webserver.main(sys.argv[2:])
    else:
        usage()
        rc = 2
    sys.exit(rc)
