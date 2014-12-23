#!/bin/sh
# Copyright (c) 2014, Sine Nomine Associates
# See LICENSE
#
# WARNING!
# ========
#
# This script will destroy all OpenAFS files on this system!  You should
# not need to run this script unless you are debugging the test harness
# and you want to wipe the system.
#

if [ `id -u` != 0 ]; then
    echo "reset: Must run as root." >&2
    exit 1
fi

case $1 in
rhel6)
    service openafs-server stop 2>/dev/null
    service openafs-client stop 2>/dev/null
    rpm --erase --noscripts openafs-server 2>/dev/null
    rpm --erase --noscripts openafs-client kmod-openafs 2>/dev/null
    rpm --erase --noscripts openafs-krb5 2>/dev/null
    rpm --erase --noscripts openafs 2>/dev/null
    rm -f /var/lock/subsys/openafs-server 2>/dev/null
    rm -f /var/lock/subsys/openafs-client 2>/dev/null
    rm -f /etc/sysconfig/openafs* 2>/dev/null
    rm -rf /usr/vice/etc 2>/dev/null
    rm -rf /usr/afs 2>/dev/null
    ;;
suse)
    service openafs-server stop >/dev/null  2>&1
    service openafs-client stop >/dev/null 2>&1
    packages=`rpm -qa | grep openafs`
    rpm --erase --noscripts $packages 2>/dev/null
    rm -rf /etc/openafs 2>/dev/null
    rm -rf /var/lib/openafs 2>/dev/null
    rm -rf /var/log/openafs 2>/dev/null
    ;;
transarc)
    killall -QUIT bosserver 2>/dev/null
    umount /afs 2>/dev/null
    rmmod libafs 2>/dev/null
    rm -rf /usr/afsws 2>/dev/null
    rm -rf /usr/vice/etc 2>/dev/null
    rm -rf /usr/afs 2>/dev/null
    ;;
*)
    echo "usage: sudo tools/reset.sh <mode>" >&2
    echo "       where <mode> is one of rhel6, suse, transarc" >&2
    echo "warning: This tool will destroy all OpenAFS data files on this system!" >&2
    exit 1
    ;;
esac

# Just in case bosserver is still here.
killall bosserver 2>/dev/null

# Try to remove the afs mountpoint
if [ -d /afs ]; then
    rmdir /afs 2>/dev/null
fi

# Remove all vice files! Leave the /vicep* mount points
# in place. Leave AlwaysAttach files alone, if any.
for vice in /vicep*
do
    rm -f $vice/*.vol
    rm -rf $vice/AFSIDat
    rm -rf $vice/Lock
done

# Remove test harness state info, if any.
if [ -d site ]; then
    rm -f site/.stage
fi

