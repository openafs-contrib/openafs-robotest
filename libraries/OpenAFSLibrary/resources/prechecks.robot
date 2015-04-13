# Copyright (c) 2014, Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation    Checks to verify this system is ready
...              to begin setup for testing.

*** Keywords ***
Non-interactive sudo is Required
    Command Should Succeed  sudo -n /usr/sbin/afs-robotest-sudo uname
    ...  Passwordless sudo is not available!

Required Variables Should Not Be Empty
    Should Not Be Empty  AFS_CELL
    Should Not Be Empty  AFS_DIST
    Should Not Be Empty  KRB_REALM

Transarc Variables Should Exist
    Should Not Be Empty     ${TRANSARC_DEST}
    Directory Should Exist  ${TRANSARC_DEST}
    Directory Should Exist  ${TRANSARC_DEST}/root.server

Host Address Should Not Be Loopback
    [Documentation]    Fail if a usable address is not found for this host.
    ...  Hopefully, this precheck can be removed in a future version of OpenAFS.
    ...  The fact that OpenAFS depends on gethostbyname() to resolve to a
    ...  non-loopback address during the setup is arguably a bug, but for now
    ...  we need the hostname to resolve to a non-loopback address.
    ...  This means the /etc/hosts may need to be changed on the test system.
    ${address}=   Get Host By Name  ${HOSTNAME}
    Should Not Match Regexp  ${address}  ^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$
    ...  Loopback address is assigned to ${HOSTNAME}

Network Interface Should Have The Host Address
    [Documentation]   Fail if a network interface is not found for the host address.
    ...               This can happen if the DNS (or /etc/hosts) has a different address
    ...               than the network interface.
    ${address}=     Get Host By Name  ${HOSTNAME}
    ${interfaces}=  Get Interfaces
    Should Contain  ${interfaces}  ${address}
    ...  msg=Network interface not found for host adddress ${address}!
    ...  values=False

OpenAFS Servers Should Not Be Running
    Program Should Not Be Running  bosserver
    Program Should Not Be Running  fileserver
    Program Should Not Be Running  volserver
    Program Should Not Be Running  dafileserver
    Program Should Not Be Running  davolserver
    Program Should Not Be Running  salvageserver
    Program Should Not Be Running  vlserver
    Program Should Not Be Running  ptserver

AFS Filesystem Should Not Be Mounted
    ${mount}              Run         mount
    Should Not Contain    ${mount}    AFS on /afs

OpenAFS Kernel Module Should Not Be Loaded
    ${modules}=  Get Modules
    Should Not Contain  ${modules}  openafs
    Should Not Contain  ${modules}  libafs

OpenAFS Installation Directories Should Not Exist
    Directory Should Not Exist  ${AFS_CONF_DIR}
    Directory Should Not Exist  ${AFS_KERNEL_DIR}
    Directory Should Not Exist  ${AFS_SRV_BIN_DIR}
    Directory Should Not Exist  ${AFS_SRV_SBIN_DIR}
    Directory Should Not Exist  ${AFS_SRV_LIBEXEC_DIR}
    Directory Should Not Exist  ${AFS_DB_DIR}
    Directory Should Not Exist  ${AFS_LOGS_DIR}
    Directory Should Not Exist  ${AFS_LOCAL_DIR}
    Directory Should Not Exist  ${AFS_BACKUP_DIR}
    Directory Should Not Exist  ${AFS_BOS_CONFIG_DIR}
    Directory Should Not Exist  ${AFS_DATA_DIR}

Cache Partition Should Be Empty
    [Documentation]   Fails unless the cache partition is available, empty
    Directory Should Exist   ${AFS_CACHE_DIR}
    File Should Not Exist    ${AFS_CACHE_DIR}/*

Vice Partition Should Be Empty
    [Documentation]   Fails unless the vice partition is available, empty
    [Arguments]  ${id}
    Directory Should Exist        /vicep${id}
    File Should Not Exist         /vicep${id}/*.vol
    Directory Should Not Exist    /vicepa/AFSIDat
    Directory Should Not Exist    /vicepa/Lock

Vice Partition Should Be Attachable
    [Documentation]   Fails if the vice partition is not attachable
    [Arguments]  ${id}
    Should Not Be Empty  ${id}
    Directory Should Exist        /vicep${id}/
    File Should Not Exist         /vicep${id}/NeverAttach
    ${root_device}=  Get Device   /
    ${vice_device}=  Get Device   /vicep${id}/
    Run Keyword If   '${vice_device}'=='${root_device}'
    ...  File Should Exist  /vicep${id}/AlwaysAttach
    ...  Missing 'AlwaysAttach' file in pseudo vice partition /vicep{$id}/

CellServDB.dist Should Exist
    Should Not Be Empty  ${AFS_CSDB_DIST}
    File Should Exist    ${AFS_CSDB_DIST}

Kerberos Client Must Be Installed
    Should Not Be Empty           ${KINIT}
    File Should Exist             ${KINIT}
    File Should Be Executable     ${KINIT}
    Should Not Be Empty           ${KLIST}
    File Should Exist             ${KLIST}
    File Should Be Executable     ${KLIST}

Kerberos Keytab Should Exist
    [Documentation]  Verify a keytab for the principal exists.
    [Arguments]  ${keytab}  ${principal}  ${realm}
    File Should Exist  ${keytab}
    ${rc}  ${output}  Run And Return Rc And Output  ${KLIST} -k -t ${keytab}
    Should Be Equal As Integers  ${rc}  0
    Should Contain  ${output}  ${principal}@${realm}

Service Keytab Should Exist
    [Documentation]   Verify the service key is present in the keyfile and the
    ...               enctype is appropriate for the AFS keyfile to be created.
    [Arguments]  ${keytab}  ${cell}  ${realm}  ${enctype}  ${keyfile}
    File Should Exist  ${keytab}
    ${eno}=  Get Encryption Type Number  ${enctype}
    ${des}=  Encryption Type Is DES      ${enctype}
    Should Be True
    ...  '${keyfile}' in ['KeyFile', 'rxkad.keytab', 'KeyFileExt']
    ...  Unknown AFS keyfile: ${keyfile}
    Run Keyword If   '${keyfile}'=='KeyFile'
    ...  Should Be True   ${des}      DES enctype is required for ${keyfile}: enctype=${enctype}
    Run Keyword If   '${keyfile}'=='KeyFileExt' or '${keyfile}'=='rxkad.keytab'
    ...  Should Be True   not ${des}  Non-DES enctype is required for ${keyfile}: enctype=${enctype}
    ${kvno}=  Get Key Version Number  ${keytab}  ${cell}  ${realm}  ${enctype}

Can Get a Kerberos Ticket
    [Arguments]  ${keytab}  ${principal}  ${realm}
    Command Should Succeed  ${KINIT} -5 -c ${SITE}/krb5cc -k -t ${keytab} ${principal}@${realm}
    Command Should Succeed  ${KDESTROY} -c ${SITE}/krb5cc


