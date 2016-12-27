# Copyright (c) 2014, Sine Nomine Associates
# See LICENSE
#
# RHEL/CentOS 6.x default settings.
#
# Variables may be added to the settings.py file in order to
# override these default values.
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
PAGSH = "/usr/bin/pagsh"
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
# RPM package names
#
RPM_COMMON_PACKAGES = "openafs,openafs-krb5,openafs-docs"
RPM_SERVER_PACKAGES = "openafs-server"
RPM_CLIENT_PACKAGES = "openafs-client"

