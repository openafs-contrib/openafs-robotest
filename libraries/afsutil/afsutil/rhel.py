# Copyright (c) 2014-2016 Sine Nomine Associates
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

"""Helper to install and remove OpenAFS RPM packages."""

import logging
import os
import sys
import re

from afsutil.system import sh

logger = logging.getLogger(__name__)


def get_release():
    """Read the current Redhat release string."""
    try:
        file = open("/etc/redhat-release", "r")
        release = file.readline().rstrip()
        file.close()
    except:
        release = ''
    return release

def _get_dist_num(release):
    """Extra the dist number from the release string, if one."""
    version = release.split("(")[0]
    match = re.search(r"([0-9\.]+)", version)
    mainver = match.group(1).split(".")[0] if match else None
    return mainver

def get_dist():
    """Determine the value of the rpm 'dist' tag.

    Adapted from the redhat-rpm-config package dist.sh script by Tom Calloway.
    The dist tag takes the format,

        .$type$num

    where $type is one of: el, fc, rh
    (for RHEL, Fedora Core, and RHL, respectively)
    CentOS is mapped to el.
    """
    release = get_release()
    distnum = _get_dist_num(release)
    if distnum:
        if re.search(r'Fedora', release):
            disttype = "fc"
        elif re.search(r'(Enterprise|Advanced|CentOS)', release):
            disttype = "el"
        elif re.search(r'Red Hat Linux', release) and not re.search(r'Advanced', release):
            disttype = "rhl"
        else:
            disttype = None
    if distnum and disttype:
        dist = ".%s%s" % (disttype, distnum)
    else:
        dist = ""
    return dist

def get_afsversion(path, arch):
    """Get the afs version and release number from the rpm files in path."""
    path = os.path.join(path, arch)
    for f in os.listdir(path):
        m = re.search(r'^openafs-(\d+\.\d+\.\d+)-(\d+)\..*\.rpm$', f)
        if m:
            afsversion = m.group(1)
            afsrelease = m.group(2)
            return (afsversion, afsrelease)
    raise ValueError("Cannot find afs version number from rpms.")

def rpm(*args):
    """Helper to run the rpm command."""
    sh('rpm', *args)

class RhelRpmInstaller(object):
    def __init__(self, pkgdir=None, cell='localcell', hosts=None, realm=None, csdb=None, force=False, **kwargs):
        if pkgdir is None:
            raise ValueError("pkgdir not set.")
        if not os.path.exists(pkgdir):
            raise ValueError("pkgdir path '%s' not found." % pkgdir)
        self.pkgdir = pkgdir
        self.arch = os.uname()[4]
        self.kversion = os.uname()[2].replace('-', '_')
        self.dist = get_dist()
        self.release = get_release()
        self.afsversion, self.afsrelease = get_afsversion(self.pkgdir, self.arch)

    def get_package_file(self, name):
        """Get the fully qualified path to the rpm file for package name."""
        afsversion = self.afsversion
        afsrelease = self.afsrelease
        dist = self.dist
        arch = self.arch
        file = "%(name)s-%(afsversion)s-%(afsrelease)s%(dist)s.%(arch)s.rpm" % (locals())
        path = os.path.join(self.pkgdir, self.arch, file)
        if not os.path.exists(path):
            raise ValueError("File not found '%s' for package '%s'." % (path, name))
        return path

    def get_kmod_package_file(self):
        """Get the fully qualified path to the rpm kmod package file."""
        afsversion = self.afsversion
        afsrelease = self.afsrelease
        kversion = self.kversion
        file = "kmod-openafs-%(afsversion)s-%(afsrelease)s.%(kversion)s.rpm" % (locals())
        path = os.path.join(self.pkgdir, self.arch, file)
        if not os.path.exists(path):
            raise ValueError("File not found '%s' for kversion '%s'." % (path, kversion))
        return path

    def install_server(self):
        """Install server packages."""
        logger.info("Installing server packages.")
        packages = [
            self.get_package_file('openafs'),
            self.get_package_file('openafs-krb5'),
            self.get_package_file('openafs-server'),
        ]
        rpm('-v', '--install', '--replacepkgs', *packages)

    def install_client(self):
        """Install client packages."""
        logger.info("Installing client packages.")
        packages = [
            self.get_package_file('openafs'),
            self.get_package_file('openafs-krb5'),
            self.get_package_file('openafs-client'),
            self.get_kmod_package_file(),
        ]
        rpm('-v', '--install', '--replacepkgs', *packages)

class RhelRpmUninstaller(object):
    def __init__(self, purge=False, **kwargs):
        logger.info("TODO")
        pass

    def remove_client(self):
        logger.info("TODO")
        pass

    def remove_server(self):
        logger.info("TODO")
        pass


def main():
    from pprint import pprint
    pkgdir = "/home/mmeffie/src/openafs/packages/rpmbuild/RPMS"
    x = RhelRpmInstaller(pkgdir=pkgdir)
    x.install_client()
    x.install_server()

if __name__ == '__main__':
    main()
