"""Utility classes to build, install, and setup OpenAFS."""

from afsutil.__version__ import VERSION as __version__

def print_version(**kwargs):
    import sys
    sys.stdout.write("afsutil version {0}\n".format(__version__))
