# Copyright (c) 2015 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation     Mountpoint tests
Library           OperatingSystem
Library           String
Library           OpenAFSLibrary
Suite Setup       Setup
Suite Teardown    Teardown

*** Variables ***
${MTPT}         /afs/.${AFS_CELL}/test/mtpt
${MTPT2}         /afs/.${AFS_CELL}/mtpt
${MTPT3}         /afs/.${AFS_CELL}/mtpt3
${MTPT4}         /afs/.${AFS_CELL}/mtpt4
${VOLUME}     test.mtpt
${VOLUME2}     test2.mtpt
${PARTITION}  a
${SERVER}     ${AFS_FILESERVER_A}
${TESTPATH}   /afs/.${AFS_CELL}/test/${VOLUME}
${TESTPATH2}   /afs/.${AFS_CELL}/${VOLUME2}

*** Test Cases ***
Make and Remove a Mountpoint
    [Setup]    Run Keyword
    ...    Command Should Succeed  ${FS} mkmount -dir ${MTPT} -vol ${VOLUME}
    Directory Should Exist  ${MTPT}
    [Teardown]  Run Keywords
    ...    Command Should Succeed  ${FS} rmmount -dir ${MTPT}  AND
    ...    Directory Should Not Exist  ${MTPT}

Make and Remove a Mountpoint with Command Aliases
    [Setup]    Run Keyword
    ...    Command Should Succeed  ${FS} mkm ${MTPT} root.cell
    Directory Should Exist  ${MTPT}
    [Teardown]  Run Keywords
    ...    Command Should Succeed  ${FS} rmm ${MTPT}  AND
    ...    Directory Should Not Exist  ${MTPT}

Create a Mountpoint to a Nonexistent Volume
    [Documentation]   The fs command permits the creation of dangling mountpoints.
    ...               A directory entry is created, but the directory is not usable.
    [Setup]    Run Keyword
    ...    Command Should Succeed        ${FS} mkm ${MTPT} no-such-volume
    Directory Entry Should Exist  ${MTPT}
    Command Should Fail           test -d ${MTPT}
    Command Should Fail           touch ${MTPT}/foo
    [Teardown]    Run Keyword
    ...    Command Should Succeed        ${FS} rmm ${MTPT}

Set RW ACL in root.cell for system:authuser
    [Documentation]   Setting ACL for root.cell volume which is mounted /afs/.${AFS_CELL}
    [Setup]    Run Keyword
    ...    Add Access Rights  /afs/.${AFS_CELL}  system:authuser  rlidwk
    Access Control List Contains  /afs/.${AFS_CELL}  system:authuser  rlidwk

Make a Mountpoint in root.cell volume
    [Setup]    Run Keyword
    ...    Command Should Succeed  ${FS} mkmount -dir ${MTPT2} -vol ${VOLUME2}
    Directory Should Exist  ${MTPT2}
    [Teardown]  Run Keywords
    ...    Command Should Succeed  ${FS} rmmount -dir ${MTPT2}  AND
    ...    Directory Should Not Exist  ${MTPT2}

Make and Remove a Mountpoint with Command Aliases in root.cell volume
    [Setup]    Run Keyword
    ...    Command Should Succeed  ${FS} mkm ${MTPT3} root.cell
    Directory Should Exist  ${MTPT3}
    [Teardown]  Run Keywords
    ...    Command Should Succeed  ${FS} rmm ${MTPT3}  AND
    ...    Directory Should Not Exist  ${MTPT3}

Create a Mountpoint to a Nonexistent Volume in root.cell volume
    [Documentation]   The fs command permits the creation of dangling mountpoints.
    ...               A directory entry is created, but the directory is not usable.
    [Setup]    Run Keyword
    ...    Command Should Succeed        ${FS} mkm ${MTPT4} no-such-volume
    Directory Entry Should Exist  ${MTPT4}
    Command Should Fail           test -d ${MTPT4}
    Command Should Fail           touch ${MTPT4}/foo
    [Teardown]    Run Keyword
    ...    Command Should Succeed        ${FS} rmm ${MTPT4}

*** Keywords ***
Setup
    Login  ${AFS_ADMIN}  keytab=${AFS_ADMIN_KEYTAB}
    Command Should Succeed  ${VOS} create ${SERVER} ${PARTITION} ${VOLUME}
    Command Should Succeed  ${VOS} create ${SERVER} ${PARTITION} ${VOLUME2}

Teardown
    Remove Volume  ${VOLUME}
    Remove Volume  ${VOLUME2}
    Logout
