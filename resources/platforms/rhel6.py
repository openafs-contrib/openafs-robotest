# Copyright (c) 2014, Sine Nomine Associates
# See LICENSE
#
# Variables OpenAFS on RHEL/CentOS 6.x
#

#
# Installation Paths
#
AFS_CONF_DIR = "/usr/afs/etc"
AFS_KERNEL_DIR = "/usr/vice/etc"
AFS_SRV_BIN_DIR =  "/usr/afs/bin"
AFS_SRV_SBIN_DIR = "/usr/afs/bin"
AFS_SRV_LIBEXEC_DIR = "/usr/afs/bin"
AFS_DB_DIR = "/usr/afs/db"
AFS_LOGS_DIR = "/usr/afs/logs"
AFS_LOCAL_DIR = "/usr/afs/local"
AFS_BACKUP_DIR = "/usr/afs/backup"
AFS_BOS_CONFIG_DIR = "/usr/afs/local"
AFS_DATA_DIR = "/usr/vice/etc"
AFS_CACHE_DIR = "/usr/vice/cache"

#
# Fully qualified AFS command paths for rpm-based installs.
#
AKLOG = "/usr/bin/aklog"
ASETKEY = "/usr/sbin/asetkey"
BOS = "/usr/bin/bos"
FS = "/usr/bin/fs"
PTS = "/usr/bin/pts"
RXDEBUG = "/usr/sbin/rxdebug"
TOKENS = "/usr/bin/tokens"
UDEBUG = "/usr/bin/udebug"
UNLOG = "/usr/bin/unlog"
VOS = "/usr/sbin/vos"

#
# afsd options
#
AFSD_DYNROOT = True

#
# RPM package files to install
#
import os
import settings as _s

RPM_SERVER_PACKAGES = ('openafs', 'openafs-krb5', 'openafs-docs', 'openafs-server')
RPM_CLIENT_PACKAGES = ('openafs', 'openafs-krb5', 'openafs-docs', 'openafs-client')

def _rhel_rpm(package):
    """Get the RHEL rpm filename from a package name."""
    rpm_arch = os.uname()[4]
    rpm_dist = ".el6"
    return "%s/%s-%s-%s%s.%s.rpm" % \
        (_s.RPM_PACKAGE_DIR, package, _s.RPM_AFSVERSION, _s.RPM_AFSRELEASE,
         rpm_dist, rpm_arch)

def _rhel_kmod():
    """Get the RHEL rpm filename for the kernel module."""
    rpm_kversion  = os.uname()[2].replace('-','_')
    return "%s/kmod-openafs-%s-%s.%s.rpm" % \
        (_s.RPM_PACKAGE_DIR, _s.RPM_AFSVERSION, _s.RPM_AFSRELEASE, rpm_kversion)

# Generate the list of rpm filenames from the package names.
RPM_KMOD_FILE = _rhel_kmod()
RPM_SERVER_FILES = [_rhel_rpm(p) for p in RPM_SERVER_PACKAGES]
RPM_CLIENT_FILES = [_rhel_rpm(p) for p in RPM_CLIENT_PACKAGES] + [RPM_KMOD_FILE]

