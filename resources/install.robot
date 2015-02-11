# Copyright (c) 2014, Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation     Keywords for OpenAFS installation and removal.

*** Keywords ***
#--------------------------------------------------------------------------------
# Keywords for transarc-style intallations.
#
Untar Binaries
    [Documentation]  Untar transarc style binaries
    Should Not Be Empty  ${GTAR}
    Should Not Be Empty  ${TRANSARC_TARBALL}
    Create Directory     site/binaries
    Run Command          cd site/binaries && ${GTAR} xvzf ${TRANSARC_TARBALL}

Install Server Binaries
    [Documentation]  Install transarc style server binaries
    Should Not Be Empty     ${TRANSARC_DEST}
    Directory Should Exist  ${TRANSARC_DEST}
    Directory Should Exist  ${TRANSARC_DEST}/root.server
    Sudo    mkdir -p /usr/afs
    Sudo    cp -r -p ${TRANSARC_DEST}/root.server/usr/afs/bin /usr/afs

Install Client Binaries
    [Documentation]  Install transarc style cache manager binaries
    Should Not Be Empty     ${TRANSARC_DEST}
    Directory Should Exist  ${TRANSARC_DEST}
    Directory Should Exist  ${TRANSARC_DEST}/root.client
    Sudo    mkdir -p /usr/vice/etc
    Sudo    cp -r -p ${TRANSARC_DEST}/root.client/usr/vice/etc /usr/vice

Install Init Script on Linux
    [Documentation]  Install the transarc style init script for linux. Do not
    ...              make it run automatically on reboot.
    Should Not Be Empty  ${TRANSARC_DEST}
    Should Not Be Empty  ${AFSD_CONFIG_DIR}
    Sudo  cp ${TRANSARC_DEST}/root.client/usr/vice/etc/afs.rc /etc/init.d/afs
    Sudo  chmod +x /etc/init.d/afs
    # Set the afsd command line options.
    Sudo  mkdir -p ${AFSD_CONFIG_DIR}
    Sudo  cp ${TRANSARC_DEST}/root.client/usr/vice/etc/afs.conf ${AFSD_CONFIG_DIR}

Install Init Script on Solaris
    [Documentation]  Install the transarc style init script for solaris. Do not
    ...              make it run automatically on reboot.  Patch the init script
    ...              so the client can be started independently from the server.
    Should Not Be Empty  ${TRANSARC_DEST}
    Should Not Be Empty  ${AFSD_CONFIG_DIR}
    Should Not Be Empty  ${AFSD_OPTIONS}
    ${afsrc}=  Get File  ${TRANSARC_DEST}/root.client/usr/vice/etc/modload/afs.rc
    ${afsrc}=  Replace String  ${afsrc}
    ...  if [ -x /usr/afs/bin/bosserver ]; then
    ...  if [ "\${AFS_SERVER}" == "on" -a -x /usr/afs/bin/bosserver ]; then
    ${afsrc}=  Replace String  ${afsrc}
    ...  if [ "\${bosrunning}" != "" ]; then
    ...  if [ "\${AFS_SERVER}" == "on" -a "\${bosrunning}" != "" ]; then
    Create File  site/afs.rc  ${afsrc}
    Sudo  cp site/afs.rc /etc/init.d/afs
    Sudo  chmod +x /etc/init.d/afs
    # Set the afsd command line options.
    Create File  site/afsd.options  ${AFSD_OPTIONS}
    Sudo  mkdir -p ${AFSD_CONFIG_DIR}
    Sudo  cp site/afsd.options ${AFSD_CONFIG_DIR}

Install Workstation Binaries
    [Documentation]  Install transarc style workstation binaries
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
    [Documentation]  Remove transarc style server binaries.
    Purge Directory  /usr/afs/bin

Remove Client Binaries
    [Documentation]  Remove transarc style cache manager binaries.
    Purge Directory  /usr/vice/etc

Remove Workstation Binaries
    [Documentation]  Remove transarc style workstation binaries.
    Purge Directory  /usr/afsws

Start the bosserver
    File Should Exist              ${AFS_SRV_LIBEXEC_DIR}/bosserver
    File Should Be Executable      ${AFS_SRV_LIBEXEC_DIR}/bosserver
    Program Should Not Be Running  bosserver
    Sudo  ${AFS_SRV_LIBEXEC_DIR}/bosserver  ${BOSSERVER_OPTIONS}
    Program Should Be Running      bosserver

Stop the bosserver
    Program Should Be Running    bosserver
    Sudo  ${BOS} shutdown localhost -wait -localauth
    Sudo  pkill bosserver

Start the Cache Manager on Linux
    ${kmod}=  Set Variable  ${AFS_KERNEL_DIR}/modload/libafs-${OS_RELEASE}.mp.ko
    File Should Exist  ${kmod}
    Sudo  insmod ${kmod}
    Sudo  /usr/vice/etc/afsd ${AFSD_OPTIONS}

Stop the Cache Manager on Linux
    Sudo  umount /afs
    Sudo  /usr/vice/etc/afsd -shutdown
    Unload Module  libafs

Start the Cache Manager on Solaris
    Sudo  /etc/init.d/afs start

Stop the Cache Manager on Solaris
    Sudo  umount /afs
    Sudo  /usr/vice/etc/afsd -shutdown
    Unload Module  afs


#--------------------------------------------------------------------------------
# Keywords for RPM based installs. The list of packages to install are given
# in the per platform variable file.
#
Install RPM Files
    [Arguments]  @{packages}
    Sudo  rpm -v --test --install --replacepkgs  @{packages}
    Sudo  rpm -v --install --replacepkgs  @{packages}

Install OpenAFS Server RPM Files
    Install RPM Files  @{RPM_SERVER_FILES}

Install OpenAFS Client RPM Files
    Install RPM Files  @{RPM_CLIENT_FILES}

Remove OpenAFS RPM Packages
    ${rc}  ${output}  Run And Return Rc And Output  rpm -qa '(kmod-)?openafs*'
    Should Be Equal As Integers  ${rc}  0
    @{packages}=  Split To Lines  ${output}
    Sudo  rpm -v --test --erase  @{packages}
    Sudo  rpm -v --erase  @{packages}

#--------------------------------------------------------------------------------
# Keywords for post-uninstall clean up.
#
Purge Directory
    [Documentation]  Delete directory entry and contents (if it exists).
    [Arguments]  ${dir}
    Should Not Be Empty  ${dir}
    Should Not Be Equal  ${dir}  /
    Sudo  rm -rf ${dir}

Purge Cache Manager Configuration
    Purge Directory  ${AFS_KERNEL_DIR}
    Purge Directory  /afs

Purge Cache
    [Documentation]  Delete all of the cache files. AFS_CACHE_DIR may be
    ...              a unix mount point, so do not remove it.
    Purge Directory  ${AFS_CACHE_DIR}/*

Purge Server Configuration
    Purge Directory  ${AFS_LOGS_DIR}
    Purge Directory  ${AFS_DB_DIR}
    Purge Directory  ${AFS_LOCAL_DIR}
    Purge Directory  ${AFS_CONF_DIR}

Purge Volumes On Partition
    [Arguments]    ${vice}
    Sudo  rm -f ${vice}/V*.vol
    Purge Directory  ${vice}/AFSIDat
    Purge Directory  ${vice}/Lock

