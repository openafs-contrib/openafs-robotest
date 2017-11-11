# Copyright (c) 2017 Sine Nomine Associates
# See LICENSE

*** Settings ***
Resource           common.robot
Suite Setup        Setup Users and Groups
Suite Teardown     Teardown Users and Groups
Test Setup         Setup Test Directory
Test Teardown      Teardown Test Directory

*** Variables ***
${PATH}            /afs/.${AFS_CELL}/test/permtest
${PRIV_PATH}       /afs/.${AFS_CELL}/test/permtest/privdir
${PUB_PATH}        /afs/.${AFS_CELL}/test/permtest/pubdir

*** Keywords ***
Setup Users and Groups
    Logout
    Login  ${AFS_ADMIN}
    Command Should Succeed   ${PTS} createuser user1
    Command Should Succeed   ${PTS} creategroup group1 -owner ${AFS_ADMIN}
    Command Should Succeed   ${PTS} adduser user1 group1

Teardown Users and Groups
    Login  ${AFS_ADMIN}
    Command Should Succeed   ${PTS} delete user1
    Command Should Succeed   ${PTS} delete group1
    Logout

Setup Test Directory
    Login  ${AFS_ADMIN}
    Create Directory          ${PATH}
    Create Directory          ${PRIV_PATH}
    Create Directory          ${PUB_PATH}
    ${output}=  Run           ${FS} listacl ${PATH}
    #setacl needs a keyword
    Command Should Succeed    ${FS} setacl ${PATH} user1 rl
    Command Should Succeed    ${FS} setacl ${PRIV_PATH} user1 rlidwka
    Command Should Succeed    ${FS} setacl ${PRIV_PATH} system:anyuser none
    Command Should Succeed    ${FS} setacl ${PRIV_PATH} system:administrators rl
    Command Should Succeed    ${FS} setacl ${PUB_PATH} system:anyuser rlidwk
    Logout
    List PUB and PRIV ACLs

Teardown Test Directory
    Login  ${AFS_ADMIN}
    Remove Directory          ${PUB_PATH}
    Remove Directory          ${PRIV_PATH}
    Remove Directory          ${PATH}
    Logout

List PUB and PRIV ACLs
    ${output}=   Run              ${FS} listacl ${PUB_PATH}
    ${output}=   Run              ${FS} listacl ${PRIV_PATH}

User1 Create File
    Login  user1
    Create File                   ${PRIV_PATH}/privfile
    Logout

User1 Remove File
    Login  user1
    Remove File                   ${PRIV_PATH}/privfile
    Logout

*** Test Cases ***
Write Permissions as Admin
    Login  ${AFS_ADMIN}
    Touch                         ${PUB_PATH}/pubfile
    Command Should Fail           touch ${PRIV_PATH}/privfile
    Remove File                   ${PUB_PATH}/pubfile
    Logout

Write Permissions as Anyuser
    Touch                         ${PUB_PATH}/pubfile2
    # need a keyword for expecting touch to fail
    Command Should Fail           touch ${PRIV_PATH}/privfile
    Remove File                   ${PUB_PATH}/pubfile2

Write Permissions as User1
    Login  user1
    Touch                         ${PUB_PATH}/pubfile3
    Touch                         ${PRIV_PATH}/privfile
    Remove File                   ${PUB_PATH}/pubfile3
    Remove File                   ${PRIV_PATH}/privfile
    Logout

Read Permissions as Anyuser
    User1 Create File
    Create File                   ${PUB_PATH}/pubfile
    Command Should Succeed        cat ${PUB_PATH}/pubfile
    Command Should Fail           cat ${PRIV_PATH}/privfile
    Remove File                   ${PUB_PATH}/pubfile
    User1 Remove File

Read Permissions as User1
    Login  user1
    Create File                   ${PRIV_PATH}/privfile
    Create File                   ${PUB_PATH}/pubfile
    Command Should Succeed        cat ${PRIV_PATH}/privfile
    Command Should Succeed        cat ${PUB_PATH}/pubfile
    Remove File                   ${PRIV_PATH}/privfile
    Remove File                   ${PUB_PATH}/pubfile
    Logout

Lookup Permissions as Anyuser
    Command Should Succeed        ls ${PUB_PATH}
    Command Should Fail           ls ${PRIV_PATH}

Lookup Permissions as User1
    Login  user1
    Command Should Succeed        ls ${PUB_PATH}
    Command Should Succeed        ls ${PRIV_PATH}
    Logout

Delete Permissions as User1
    Login  user1
    Create File                   ${PRIV_PATH}/privfile
    Create File                   ${PUB_PATH}/pubfile
    Remove File                   ${PRIV_PATH}/privfile
    Remove File                   ${PUB_PATH}/pubfile
    Logout

New Directory for User1
    Login  user1
    Command Should Succeed        mkdir ${PRIV_PATH}/new_priv
    Command Should Succeed        mkdir ${PUB_PATH}/new_pub
    Remove Directory              ${PRIV_PATH}/new_priv
    Remove Directory              ${PUB_PATH}/new_pub
    Logout

New Directory for Anyuser
    Command Should Fail           mkdir ${PRIV_PATH}/new_priv
    Command Should Succeed        mkdir ${PUB_PATH}/new_pub
    Remove Directory              ${PUB_PATH}/new_pub
