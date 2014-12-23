# Copyright (c) 2014, Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation     Keywords for Transarc style installations.

*** Keywords ***
Untar Binaries
    Should Not Be Empty  ${GTAR}
    Should Not Be Empty  ${TRANSARC_TARBALL}
    Create Directory     site/binaries
    Run Command          cd site/binaries && ${GTAR} xvzf ${TRANSARC_TARBALL}

Install Server Binaries
    Should Not Be Empty     ${TRANSARC_DEST}
    Directory Should Exist  ${TRANSARC_DEST}
    Directory Should Exist  ${TRANSARC_DEST}/root.server
    Sudo    mkdir -p /usr/afs
    Sudo    cp -r -p ${TRANSARC_DEST}/root.server/usr/afs/bin /usr/afs

Install Client Binaries
    Should Not Be Empty     ${TRANSARC_DEST}
    Directory Should Exist  ${TRANSARC_DEST}
    Directory Should Exist  ${TRANSARC_DEST}/root.client
    Sudo    mkdir -p /usr/vice/etc
    Sudo    cp -r -p ${TRANSARC_DEST}/root.client/usr/vice/etc /usr/vice

Install Workstation Binaries
    Should Not Be Empty     ${TRANSARC_DEST}
    Directory Should Exist  ${TRANSARC_DEST}
    Directory Should Exist  ${TRANSARC_DEST}/bin
    Directory Should Exist  ${TRANSARC_DEST}/etc
    Directory Should Exist  ${TRANSARC_DEST}/include
    Directory Should Exist  ${TRANSARC_DEST}/lib
    Directory Should Exist  ${TRANSARC_DEST}/man
    Sudo    mkdir -p /usr/afsws
    Sudo    cp -r -p ${TRANSARC_DEST}/bin /usr/afsws
    Sudo    cp -r -p ${TRANSARC_DEST}/etc /usr/afsws
    Sudo    cp -r -p ${TRANSARC_DEST}/include /usr/afsws
    Sudo    cp -r -p ${TRANSARC_DEST}/lib /usr/afsws
    Sudo    cp -r -p ${TRANSARC_DEST}/man /usr/afsws

Remove Server Binaries
    Sudo    rm -rf /usr/afs

Remove Client Binaries
    Sudo    rm -rf /usr/vice/etc

Remove Workstation Binaries
    Sudo    rm -rf /usr/afsws

Start the bosserver
    File Should Exist              ${AFS_SRV_LIBEXEC_DIR}/bosserver
    File Should Be Executable      ${AFS_SRV_LIBEXEC_DIR}/bosserver
    Program Should Not Be Running  bosserver
    Sudo  ${AFS_SRV_LIBEXEC_DIR}/bosserver
    Program Should Be Running      bosserver

Stop the bosserver
    Program Should Be Running    bosserver
    Sudo  ${BOS} shutdown localhost -wait -localauth
    Sudo  killall bosserver

Remove Cache Manager Configuration
    Sudo  rm -rf /usr/vice/etc
    Sudo  rmdir /afs

Start the Cache Manager
    ${kmod}=  Set Variable  ${AFS_KERNEL_DIR}/modload/libafs-${OS_RELEASE}.mp.ko
    File Should Exist  ${kmod}
    Sudo  insmod ${kmod}
    Sudo  /usr/vice/etc/afsd ${AFSD_OPTIONS}

Stop the Cache Manager
    Sudo  umount /afs
    Sudo  rmmod libafs

