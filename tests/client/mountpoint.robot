# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Mountpoint tests
Resource          openafs.robot
Suite Setup       Login  ${AFS_ADMIN}
Suite Teardown    Logout


*** Test Cases ***
Make and Remove a Mountpoint
    [Tags]  #(mkm-rmm)
    ${mtpt}=  Set Variable  /afs/.${AFS_CELL}/test/mtpt1
    Command Should Succeed  ${FS} mkmount -dir ${mtpt} -vol root.cell
    Directory Should Exist  ${mtpt}
    Command Should Succeed  ${FS} rmmount -dir ${mtpt}
    Directory Should Not Exist  ${mtpt}

Make and Remove a Mountpoint with Command Aliases
    [Tags]
    ${mtpt}=  Set Variable  /afs/.${AFS_CELL}/test/mtpt2
    Command Should Succeed  ${FS} mkm ${mtpt} root.cell
    Directory Should Exist  ${mtpt}
    Command Should Succeed  ${FS} rmm ${mtpt}
    Directory Should Not Exist  ${mtpt}

Create a Mountpoint to a Nonexistent Volume
    [Tags]  #(mountpoint)
    [Documentation]   The fs command permits the creation of dangling mountpoints.
    ...               A directory entry in created, but the directory is not usable.
    ${mtpt}=  Set Variable        /afs/.${AFS_CELL}/test/mtpt3
    Command Should Succeed        ${FS} mkm ${mtpt} no-such-volume
    Directory Entry Should Exist  ${mtpt}
    Command Should Fail           test -d ${mtpt}
    Command Should Fail           touch ${mtpt}/foo
    Command Should Succeed        ${FS} rmm ${mtpt}

