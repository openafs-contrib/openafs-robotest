from __future__ import print_function
from os import geteuid, getenv
from os.path import isdir

def isroot():
    return geteuid() == 0

def prefix():
    prefix = getenv('PREFIX')
    if prefix:
        return prefix
    if isroot() and isdir('/usr/local'):
        return '/usr/local'
    if isroot() and isdir('/opt'):
        return '/opt'
    return getenv('HOME')

PREFIX = prefix()

print("""\
PREFIX="{PREFIX}"\
""".format(**locals()))
