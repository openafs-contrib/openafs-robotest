# Copyright (c) 2014-2015 Sine Nomine Associates
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

import os
import sys
from robot.libraries.BuiltIn import BuiltIn

def _get_var(name):
    return BuiltIn().get_variable_value("${%s}" % name)

def _get_list(name):
    items = []
    for v in _get_var(name).split(","):
        items.append(v.strip())
    return items

class Rpm:
    """Get the list of OpenAFS rpm files to be installed.

    The following global variables are required:

    AFS_DIST             -- must be set to 'rhel6' or 'suse'
    RPM_PACKAGE_DIR      -- path to rpm files to be installed
    RPM_AFSVERSION       -- rpm afs version number
    RPM_AFSRELEASE       -- rpm release number
    RPM_DIST             -- rpm dist number (suse only)
    RPM_SERVER_PACKAGES  -- comma separated list of server packages
    RPM_CLIENT_PACKAGES  -- comma separated list of client packages
    """
    @staticmethod
    def current():
        """Get the current rpm filename formatting object."""
        dist = _get_var('AFS_DIST')
        if dist == 'rhel6':
            return _Rhel6()
        if dist == 'suse':
            return _Suse()
        raise AssertionError("Unsupported AFS_DIST")

    def get_server_rpms(self):
        """Returns the list of rpm files for server installation."""
        rpms = []
        for package in _get_list('RPM_COMMON_PACKAGES'):
            rpms.append(self._rpm(package))
        for package in _get_list('RPM_SERVER_PACKAGES'):
            rpms.append(self._rpm(package))
        return rpms

    def get_client_rpms(self):
        """Returns the list of rpm files for client installation."""
        rpms = []
        for package in _get_list('RPM_COMMON_PACKAGES'):
            rpms.append(self._rpm(package))
        for package in _get_list('RPM_CLIENT_PACKAGES'):
            rpms.append(self._rpm(package))
        rpms.append(self._kmod())
        return rpms

class _Rhel6(Rpm):
    """Rhel6 specific rpm filename formats."""

    def _rpm(self, package):
        """Get the RHEL rpm filename from a package name."""
        rpm_arch = os.uname()[4]
        rpm_dist = ".el6"
        rpm = "%s/%s-%s-%s%s.%s.rpm" % \
            (_get_var('RPM_PACKAGE_DIR'),
             package,
             _get_var('RPM_AFSVERSION'),
             _get_var('RPM_AFSRELEASE'),
             rpm_dist,
             rpm_arch)
        return rpm

    def _kmod(self):
        """Get the RHEL rpm filename for the kernel module."""
        rpm_kversion = os.uname()[2].replace('-','_')
        kmod = "%s/kmod-openafs-%s-%s.%s.rpm" % \
            (_get_var('RPM_PACKAGE_DIR'),
             _get_var('RPM_AFSVERSION'),
             _get_var('RPM_AFSRELEASE'),
             rpm_kversion)
        return kmod

class _Suse(Rpm):
    """Suse specific rpm filename formats."""
    def _rpm(self, package):
        """Get the SuSE rpm filename from a package name."""
        rpm_arch = os.uname()[4]
        rpm = "%s/%s-%s-%s.%s.%s.rpm" % \
            (_get_var('RPM_PACKAGE_DIR'),
             package,
             _get_var('RPM_AFSVERSION'),
             _get_var('RPM_AFSRELEASE'),
             _get_var('RPM_DIST'),
             rpm_arch)
        return rpm

    def _kmod(self):
        """Get the SuSE rpm filename for the kernel module."""
        rpm_kflavour = os.uname()[2].split("-")[-1:][0]
        kmod = "%s/openafs-kmp-%s*.rpm" % \
            (_get_var('RPM_PACKAGE_DIR'),
             rpm_kflavour)
        return kmod

#
# Unit test
#

def main():
    t = {
        'AFS_DIST': None,
        'RPM_PACKAGE_DIR': '<d>',
        'RPM_AFSVERSION': '<v>',
        'RPM_AFSRELEASE': '<r>',
        'RPM_DIST': '1',
        'RPM_COMMON_PACKAGES': 'a,b',
        'RPM_SERVER_PACKAGES': 'x',
        'RPM_CLIENT_PACKAGES': 'y',
    }
    global _get_var  # monkey patch a test stub.
    _get_var = lambda name: t[name]

    t['AFS_DIST'] = 'rhel6'
    rpm = Rpm.current()
    print " ".join(rpm.get_server_rpms())
    print " ".join(rpm.get_client_rpms())

    t['AFS_DIST'] = 'suse'
    rpm = Rpm.current()
    print " ".join(rpm.get_server_rpms())
    print " ".join(rpm.get_client_rpms())

if __name__ == "__main__":
    main()
