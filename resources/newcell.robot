# Copyright (c) 2014, Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation     Keywords for test cell setup and teardown.

*** Keywords ***
Set Kerberos Realm Name
    [arguments]    ${realm}
    Should Not Be Empty     ${realm}
    Should Not Be Empty     ${AFS_CONF_DIR}
    Create file    site/krb.conf    ${realm}
    Sudo    mkdir -p ${AFS_CONF_DIR}
    Sudo    chmod 755 ${AFS_CONF_DIR}
    Directory Should Exist  ${AFS_CONF_DIR}
    Sudo    cp site/krb.conf ${AFS_CONF_DIR}/krb.conf

Set Machine Interface
    ${address}=  Get Host By Name  ${HOSTNAME}
    Sudo  mkdir -p ${AFS_LOCAL_DIR}
    Sudo  chmod 755 ${AFS_LOCAL_DIR}
    Create File  site/NetInfo  ${address}
    Sudo  cp site/NetInfo  ${AFS_LOCAL_DIR}/NetInfo

Create Default Cell Config
    ${address}=  Get Host By Name  ${HOSTNAME}
    Create File  site/ThisCell  ${AFS_CELL}
    Create File  site/CellServDB  >${AFS_CELL}\t#Test cell\n${address}\t#${HOSTNAME}
    Sudo  mkdir -p ${AFS_CONF_DIR}
    Sudo  chmod 755 ${AFS_CONF_DIR}
    Sudo  cp site/ThisCell  ${AFS_CONF_DIR}/ThisCell
    Sudo  cp site/CellServDB  ${AFS_CONF_DIR}/CellServDB

Create Key File
    # Workaround: asetkey fails without a cell config (even though it does not use it) so create one first.
    Create Default Cell Config
    ${kvno}=  Get Key Version Number  ${KRB_AFS_KEYTAB}  ${AFS_CELL}  ${KRB_REALM}
    Sudo  ${ASETKEY} add ${kvno} ${KRB_AFS_KEYTAB} afs/${AFS_CELL}@${KRB_REALM}

Install rxkad-k5 Keytab
    Should Not Be Empty     ${KRB_AFS_KEYTAB}
    File Should Exist       ${KRB_AFS_KEYTAB}
    Should Not Be Empty     ${AFS_CONF_DIR}
    Sudo    mkdir -p ${AFS_CONF_DIR}
    Sudo    chmod 755 ${AFS_CONF_DIR}
    Directory Should Exist  ${AFS_CONF_DIR}
    Sudo    cp ${KRB_AFS_KEYTAB} ${AFS_CONF_DIR}/rxkad.keytab

Create Extended Key File
    [Arguments]    ${enctype}
    # Workaround: asetkey fails without a cell config (even though it does not use it) so create one first.
    Create Default Cell Config
    ${kvno}=  Get Key Version Number  ${KRB_AFS_KEYTAB}  ${AFS_CELL}  ${KRB_REALM}  ${enctype}
    ${eno}=   Get Encryption Type Number  ${enctype}
    Sudo  ${ASETKEY} add rxkad_krb5 ${kvno} ${eno} ${KRB_AFS_KEYTAB} afs/${AFS_CELL}@${KRB_REALM}

Cell Name Should Be
    [Arguments]    ${cellname}
    ${rc}  ${output}  Run And Return Rc And Output  ${BOS} listhosts ${HOSTNAME} -noauth
    Should Be Equal As Integers  ${rc}  0
    Should Contain    ${output}    Cell name is ${cellname}

Try To Set the Cell Name
    [Arguments]  ${cellname}
    Should Not Be Empty  ${cellname}
    Sudo  ${BOS} setcell ${HOSTNAME} -name ${cellname} -localauth
    Cell Name Should Be  ${cellname}

Set the Cell Name
    # Retry since the bosserver just started.
    [Arguments]  ${cellname}
    Wait Until Keyword Succeeds  1 min  1 sec  Try To Set the Cell Name  ${cellname}

Set the Cell Configuration
    [Documentation]  Set up the cell configuration for the admin clients this
    ...              host. This is needed for older versions of pts and vos,
    ...              which read the cell configuration from the client data
    ...              directory.
    # The bosserver tries to create symlinks for the client cell configuration
    # files. Some packaging and init scripts will write foreign cell entries
    # to the client CellServDB, and if that is a symlink, the server copy
    # of the cell CellServDB is clobbered! So, to be safe, remove the links
    # and make a copy of the server's files for the client.
    Should Not Be Empty  ${AFS_CONF_DIR}
    Should Not Be Empty  ${AFS_DATA_DIR}
    Directory Should Exist  ${AFS_CONF_DIR}
    File Should Exist       ${AFS_CONF_DIR}/CellServDB
    File Should Exist       ${AFS_CONF_DIR}/ThisCell
    Sudo  mkdir -p ${AFS_DATA_DIR}
    Sudo  rm -f ${AFS_DATA_DIR}/CellServDB
    Sudo  rm -f ${AFS_DATA_DIR}/ThisCell
    Sudo  cp ${AFS_CONF_DIR}/CellServDB ${AFS_DATA_DIR}/CellServDB.local
    Sudo  cp ${AFS_CONF_DIR}/ThisCell   ${AFS_DATA_DIR}/ThisCell
    Run Keyword If  '${AFS_CSDB_DIST}'==''  Sudo  touch -a ${AFS_DATA_DIR}/CellServDB.dist
    Run Keyword If  '${AFS_CSDB_DIST}'!=''  Sudo  cp ${AFS_CSDB_DIST} ${AFS_DATA_DIR}/CellServDB.dist
    Sudo  sh -c 'cat ${AFS_DATA_DIR}/CellServDB.local ${AFS_DATA_DIR}/CellServDB.dist > ${AFS_DATA_DIR}/CellServDB'

Database Should Have Quorum
    [Arguments]    ${port}
    ${rc}  ${output}  Run And Return Rc And Output  ${UDEBUG} ${HOSTNAME} ${port}
    Should Contain  ${output}  Recovery state 1f

Create Database Service
    [Arguments]    ${name}  ${port}
    Sudo  ${BOS} create ${HOSTNAME}
    ...   ${name} simple
    ...   -cmd  ${AFS_SRV_LIBEXEC_DIR}/${name}
    ...   -localauth
    Wait Until Keyword Succeeds  1 min  1 sec  Database Should Have Quorum  ${port}

Fileserver Should Be Running
    Wait Until Keyword Succeeds  1 min  5 sec    Rx Service Should Be Reachable  ${HOSTNAME}  7000
    Wait Until Keyword Succeeds  1 min  5 sec    Rx Service Should Be Reachable  ${HOSTNAME}  7003

Create File Service
    Sudo  ${BOS}  create ${HOSTNAME} fs fs
    ...   -cmd /usr/afs/bin/fileserver
    ...   -cmd /usr/afs/bin/volserver
    ...   -cmd /usr/afs/bin/salvager
    ...   -localauth
    Wait Until Keyword Succeeds  1 min  5 sec    Fileserver Should Be Running

Create Demand Attach File Service
    Sudo  ${BOS}  create ${HOSTNAME}
    ...   dafs dafs
    ...   -cmd /usr/afs/bin/dafileserver
    ...   -cmd /usr/afs/bin/davolserver
    ...   -cmd /usr/afs/bin/salvageserver
    ...   -cmd /usr/afs/bin/salvager
    ...   -localauth
    Wait Until Keyword Succeeds  1 min  5 sec    Fileserver Should Be Running

Create an Admin Account
    [Arguments]    ${name}
    Sudo  ${PTS} createuser ${name} -localauth
    Sudo  ${PTS} adduser ${name} system:administrators -localauth
    Sudo  ${BOS} adduser ${HOSTNAME} ${name} -localauth

Try To Create the root.afs Volume
    Sudo  ${VOS} create ${HOSTNAME} a root.afs -verbose -localauth

Create the root.afs Volume
    [Documentation]  Create the root.afs volume.
    ...              The root.afs volume is accessed by cache managers which are
    ...              not running in dynamic-root mode to mount the AFS file system.
    ...              Create this volume using -localauth before starting a cache managers
    ...              for this cell.  Retry this operation if it does not succeed at
    ...              first since the servers just started and may not be ready yet.
    Wait Until Keyword Succeeds  1 min  5 sec  Try To Create the root.afs Volume

Set Cache Manager Configuration
    [Documentation]  Setup the cache manager configuration and make sure
    ...              the /afs directory is available to mount the AFS filesystem.
    ...              See 'Set the Cell Configuration' for CellServDB and ThisCell
    ...              configuration.
    Should Not Be Empty  ${AFS_DATA_DIR}
    Should Not Be Empty  ${AFS_CACHE_DIR}
    Sudo    mkdir -p /afs
    Create File  site/cacheinfo    /afs:${AFS_CACHE_DIR}:50000
    Sudo  cp site/cacheinfo ${AFS_DATA_DIR}/cacheinfo

Mount Cell Root Volume
    ${afs}=  Set Variable If  ${AFSD_DYNROOT}  afs/.:mount/${AFS_CELL}:root.afs  afs
    Should Not Be Empty            ${afs}
    Directory Should Exist         /${afs}
    Directory Should Not Exist     /${afs}/${AFS_CELL}
    Directory Should Not Exist     /${afs}/.${AFS_CELL}
    Mount Volume       /${afs}/${AFS_CELL}    root.cell  -cell ${AFS_CELL}
    Mount Volume       /${afs}/.${AFS_CELL}   root.cell  -cell ${AFS_CELL}  -rw
    Add Access Rights  /${afs}/.              system:anyuser  read
    Add Access Rights  /${afs}/${AFS_CELL}/.  system:anyuser  read


