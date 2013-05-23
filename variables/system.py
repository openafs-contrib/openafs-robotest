import os as _os

#  (sysname, nodename, release, version, machine)
SYS_NAME = _os.uname()[0]
SYS_NODE = _os.uname()[1]
SYS_RELEASE = _os.uname()[2]
SYS_VERSION = _os.uname()[3]
SYS_MACHINE = _os.uname()[4]

if __name__ == "__main__":
    print "SYS_NAME = '%s'" % SYS_NAME
    print "SYS_NODE = '%s'" % SYS_NODE
    print "SYS_RELEASE = '%s'" % SYS_RELEASE
    print "SYS_VERSION = '%s'" % SYS_VERSION
    print "SYS_MACHINE = '%s'" % SYS_MACHINE
