# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Mountpoint tests
Resource          openafs.robot
Suite Setup       Login  ${AFS_ADMIN}
Suite Teardown    Logout

*** Variables ***
${MTPT}         /afs/.${AFS_CELL}/test/mtpt

*** Test Cases ***
Make and Remove a Mountpoint
    [Setup]    Run Keyword
    ...    Command Should Succeed  ${FS} mkmount -dir ${MTPT} -vol root.cell
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

