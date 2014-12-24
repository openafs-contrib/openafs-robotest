# Copyright (c) 2014, Sine Nomine Associates
# See LICENSE
#
# Determine the value of the rpm 'dist' tag. Adapted from the redhat-rpm-config
# package dist.sh script by Tom Calloway.
#
# The dist tag takes the following format: .$type$num
# Where $type is one of: el, fc, rh
# (for RHEL, Fedora Core, and RHL, respectively)
# CentOS is mapped to el.

import os
import re

def _release():
    try:
        file = open("/etc/redhat-release", "r")
        release = file.readline().rstrip()
        file.close()
    except:
        release = ''
    return release

def _check_num(release):
    version = release.split("(")[0]
    match = re.search(r"([0-9\.]+)", version)
    mainver = match.group(1).split(".")[0] if match else None
    return mainver

def _check(release, pattern):
    return True if re.search(pattern, release) else False

def _check_rhl(release):
    return _check(release, "Red Hat Linux") and not _check(release, "Advanced")

def _check_rhel(release):
    return _check(release, "(Enterprise|Advanced|CentOS)")

def _check_fedora(release):
    return _check(release, "Fedora")

def _dist():
    release = _release()
    distnum = _check_num(release)
    if distnum:
        if _check_fedora(release):
	    disttype = "fc"
        elif _check_rhel(release):
	    disttype = "el"
        elif _check_rhl(release):
	    disttype = "rhl"
        else:
            disttype = None
    if distnum and disttype:
        dist = ".%s%s" % (disttype, distnum)
    else:
        dist = ""
    return dist


RPM_ARCH     = os.uname()[4]
RPM_KVERSION = os.uname()[2].replace('-','_')
RPM_DIST     = _dist()

