#!/usr/bin/env python

import sys
import os

from robot.libdoc import libdoc

ROOT = os.path.normpath(os.path.join(os.path.abspath(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'lib'))

if __name__ == '__main__':
    ipath = os.path.join(ROOT, 'lib', 'OpenAFSLibrary')
    opath = os.path.join(ROOT, 'doc', 'OpenAFSLibrary.html')
    try:
        libdoc(ipath, opath)
    except (IndexError, KeyError):
        print __doc__

