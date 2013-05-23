
*** Setting ***
Library        OperatingSystem
Resource       keywords/utility.robot
Variables    variables/system.py

*** Keywords ***
start the overseer server
    sudo    /usr/afs/bin/bosserver

start client
    file should exist    /usr/vice/etc/modload/libafs-${SYS_RELEASE}.mp.ko
    sudo    insmod /usr/vice/etc/modload/libafs-${SYS_RELEASE}.mp.ko
    sudo    /usr/vice/etc/afsd -dynroot -fakestat

set client configuration
    sudo    rm -f /usr/vice/etc/CellServDB /usr/vice/etc/ThisCell
    sudo    cp /usr/afs/etc/CellServDB /usr/vice/etc/CellServDB
    sudo    cp /usr/afs/etc/ThisCell /usr/vice/etc/ThisCell
    sudo    cp /usr/afs/etc/CellServDB /usr/vice/etc/CellServDB.local
    Sudo    mkdir /afs
    create file    /tmp/cacheinfo    /afs:/usr/vice/cache:50000
    sudo    cp /tmp/cacheinfo /usr/vice/etc/cacheinfo
    remove file    /tmp/cacheinfo
