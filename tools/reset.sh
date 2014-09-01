#!/bin/sh


if [ -f ./settings ]; then
    . ./settings
fi

if [ "$ENV_DIST" = "redhat" ]; then
    sudo service openafs-server stop 2>/dev/null
    sudo service openafs-client stop 2>/dev/null
    sudo rpm --erase --noscripts openafs-server 2>/dev/null
    sudo rpm --erase --noscripts openafs-client kmod-openafs 2>/dev/null
    sudo rpm --erase --noscripts openafs-krb5 2>/dev/null
    sudo rpm --erase --noscripts openafs 2>/dev/null
    sudo rm -f /var/lock/subsys/openafs-server 2>/dev/null
    sudo rm -f /var/lock/subsys/openafs-client 2>/dev/null
    sudo rm -f /etc/sysconfig/openafs* 2>/dev/null
    sudo rm -rf /usr/vice 2>/dev/null
    sudo rm -rf /usr/afs 2>/dev/null
fi
if [ "$ENV_DIST" = "suse" ]; then
    sudo service openafs-server stop >/dev/null  2>&1
    sudo service openafs-client stop >/dev/null 2>&1
    packages=`rpm -qa | grep openafs`
    sudo rpm --erase --noscripts $packages 2>/dev/null
    sudo rm -rf /etc/openafs 2>/dev/null
    sudo rm -rf /var/lib/openafs 2>/dev/null
    sudo rm -rf /var/log/openafs 2>/dev/null
fi
if [ "$ENV_DIST" = "transarc" ]; then
    sudo killall -QUIT bosserver 2>/dev/null
    sudo umount /afs 2>/dev/null
    sudo rmmod libafs 2>/dev/null
    sudo rm -rf /usr/afsws 2>/dev/null
    sudo rm -rf /usr/vice 2>/dev/null
    sudo rm -rf /usr/afs 2>/dev/null
fi

sudo rmdir /afs 2>/dev/null
sudo rm -rf /vicepa 2>/dev/null
sudo rmdir /vicepa 2>/dev/null
sudo killall bosserver 2>/dev/null
kdestroy 2>/dev/null

# create empty vice "partition"
sudo mkdir /vicepa 2>/dev/null
sudo touch /vicepa/AlwaysAttach 2>/dev/null

