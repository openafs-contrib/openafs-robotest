# Copyright (c) 2014, Sine Nomine Associates
# See LICENSE
#
# Variables for Transarc-style environments.
#

import os as _os

#
# Transarc style install paths.
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
# Fully qualified AFS command paths for Transarc style installs.
#
AKLOG = "/usr/afsws/bin/aklog"
ASETKEY = "/usr/afs/bin/asetkey"
BOS = "/usr/afs/bin/bos"
FS = "/usr/afs/bin/fs"
PTS = "/usr/afs/bin/pts"
RXDEBUG = "/usr/afsws/etc/rxdebug"
TOKENS = "/usr/afsws/bin/tokens"
UDEBUG = "/usr/afs/bin/udebug"
UNLOG = "/usr/afsws/bin/unlog"
VOS = "/usr/afs/bin/vos"

#
# afsd options
#
AFSD_OPTIONS = "-dynroot -fakestat"
AFSD_DYNROOT = '-dynroot' in AFSD_OPTIONS

if _os.uname()[0] == 'Linux':
    AFSD_CONFIG_DIR ="/etc/sysconfig"
elif _os.uname()[0] == 'SunOS':
    AFSD_CONFIG_DIR ="/usr/vice/etc/config"


BOSSERVER_OPTIONS = "-pidfiles"
