import os as _os
import re as _re

def _release():
    try:
        file = open("/etc/SuSE-release", "r")
        release = file.readline().strip()
        version = file.readline().strip()
        patchlevel = file.readline().strip()
        file.close()
    except:
        release = ''
    return release

def _check_num(release):
    version = release.split("(")[0]
    match = _re.search(r"([0-9\.]+)", version)
    mainver = match.group(1).split(".")[0] if match else None
    return mainver

def _check(release, pattern):
    return True if _re.search(pattern, release) else False

def _check_sles(release):
    return _check(release, "SUSE Linux Enterprise Server") 

def _check_opensuse(release):
    return _check(release, "openSUSE")

def _dist():
    release = _release()
    distnum = _check_num(release)
    if distnum:
        if _check_opensuse(release):
	    disttype = "os"
        elif _check_sles(release):
	    disttype = "sles"
        else:
            disttype = None
    if distnum and disttype:
        dist = ".%s%s" % (disttype, distnum)
    else:
        dist = ""
    return dist


RPM_ARCH     = _os.uname()[4]
RPM_KFLAVOUR = _os.uname()[2].split("-")[-1:][0]
RPM_KVERSION = _os.uname()[2].replace('-','_')
RPM_DIST     = "" # _dist()


if __name__ == "__main__":
    for var in dir() :
        if var.startswith("_") : continue
        print "%s='%s'" % (var, eval(var))

