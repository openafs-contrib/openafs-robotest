# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Mountpoint tests
Resource          common.robot
Suite Setup       Setup
Suite Teardown    Teardown

*** Variables ***
${MTPT}         /afs/.${AFS_CELL}/test/mtpt
${VOLUME}     test.mtpt
${PARTITION}  a
${SERVER}     @{AFS_FILESERVERS}[0]
${TESTPATH}   /afs/.${AFS_CELL}/test/${VOLUME}

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

*** Keywords ***
Setup
    Login  ${AFS_ADMIN}
    Command Should Succeed  ${VOS} create ${SERVER} ${PARTITION} ${VOLUME}

Teardown
    Remove Volume  ${VOLUME}
    Logout
