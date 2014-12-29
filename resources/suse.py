# Copyright (c) 2014, Sine Nomine Associates
# See LICENSE
#
# Variables for SuSE installs.
#


AFS_SERVER_ETC_DIR = "/etc/openafs/server"
AFS_SERVER_LIB_DIR  = "/var/lib/openafs"
AFS_SERVER_LIBEXEC_DIR  = "/usr/lib64/openafs"
AFS_CLIENT_ETC_DIR = "/etc/openafs"

AFS_CONF_DIR = "/etc/openafs/server"
AFS_KERNEL_DIR = "/etc/openafs"
AFS_SRV_BIN_DIR =  "/usr/lib64/openafs"
AFS_SRV_SBIN_DIR = "/usr/lib64/openafs"
AFS_SRV_LIBEXEC_DIR = "/usr/lib64/openafs"
AFS_DB_DIR = "/var/lib/openafs/db"
AFS_LOGS_DIR = "/var/log/openafs"
AFS_LOCAL_DIR = "/var/lib/openafs"
AFS_BACKUP_DIR = "/var/lib/openafs/backup" # ??
AFS_BOS_CONFIG_DIR = "/etc/openafs/server"
AFS_DATA_DIR = "/etc/openafs"
AFS_CACHE_DIR = "/var/cache/openafs"

#
# Fully qualified AFS command paths for SuSE installs.
#
AKLOG = "/usr/bin/aklog"
ASETKEY = "/usr/sbin/asetkey"
BOS = "/usr/sbin/bos"
FS = "/usr/bin/fs"
PTS = "/usr/bin/pts"
RXDEBUG = "/usr/sbin/rxdebug"
TOKENS = "/usr/bin/tokens"
UDEBUG = "/usr/sbin/udebug"
VOS = "/usr/sbin/vos"

#
# afsd options
#
AFSD_DYNROOT = True

#
# RPM package name components
#
import os
RPM_ARCH     = os.uname()[4]
RPM_KVERSION = os.uname()[2].replace('-','_')
RPM_DIST     = ".1" # ?
RPM_KFLAVOUR = os.uname()[2].split("-")[-1:][0]

