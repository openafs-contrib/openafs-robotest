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
    Command Should Succeed    ${FS} setacl ${PRIV_PATH} user1 none
    Command Should Succeed    ${FS} setacl ${PRIV_PATH} system:anyuser none
    Command Should Succeed    ${FS} setacl ${PRIV_PATH} system:administrators all
    Command Should Succeed    ${FS} setacl ${PUB_PATH} system:anyuser rlidwk
    Logout

Teardown Test Directory
    Login  ${AFS_ADMIN}
    Remove Directory    ${PATH}    recursive=True
    Logout

List PUB and PRIV ACLs
    ${output}=   Run              ${FS} listacl ${PUB_PATH}
    ${output}=   Run              ${FS} listacl ${PRIV_PATH}

Admin
    Login  ${AFS_ADMIN}

User1
    Login  user1

Create PRIV File
    Admin
    Create File                   ${PRIV_PATH}/privfile
    Create File                   ${PUB_PATH}/pubfile
    Logout

Remove PRIV File
    Admin
    Remove File                   ${PRIV_PATH}/privfile
    Remove File                   ${PUB_PATH}/pubfile
    Logout

*** Test Cases ***
Write Permissions for User1
    User1
    List PUB and PRIV ACLs
    Touch                         ${PUB_PATH}/pubfile
    Command Should Fail           touch ${PRIV_PATH}/privfile
    Remove File                   ${PUB_PATH}/pubfile
    Logout

Write Permissions for Anyuser
    List PUB and PRIV ACLs
    Touch                         ${PUB_PATH}/pubfile
    Command Should Fail           touch ${PRIV_PATH}/privfile
    Remove File                   ${PUB_PATH}/pubfile

Read Permissions for User1
    Create PRIV File
    User1
    Command Should Succeed        cat ${PUB_PATH}/pubfile
    Command Should Fail           cat ${PRIV_PATH}/privfile
    Logout
    Remove PRIV File

Read Permissions for Anyuser
    Create PRIV File
    Command Should Succeed        cat ${PUB_PATH}/pubfile
    Command Should Fail           cat ${PRIV_PATH}/privfile
    Remove PRIV File

Lookup Permissions for User1
    Create PRIV File
    User1
    Command Should Succeed        ls ${PUB_PATH}/
    Command Should Fail           ls ${PRIV_PATH}/
    Logout
    Remove PRIV File

Lookup Permissions for Anyuser
    Create PRIV File
    Command Should Succeed        ls ${PUB_PATH}/
    Command Should Fail           ls ${PRIV_PATH}/
    Remove PRIV File

Delete Permissions for User1
    Create PRIV File
    # HACK: The user needs l access to attempt to unlink the file.
    Login    ${AFS_ADMIN}
    Command Should Succeed    ${FS} sa ${PRIV_PATH} user1 l
    Logout
    User1
    Run Keyword and Expect Error    *
    ...    Remove File    ${PRIV_PATH}/privfile
    Logout
    # HACK: we need proper setup and teardowns!
    Login    ${AFS_ADMIN}
    Command Should Succeed    ${FS} sa ${PRIV_PATH} user1 none
    Logout
    Remove PRIV File

Delete Permissions for Anyuser
    Create PRIV File
    # HACK: The user needs l access to attempt to unlink the file.
    Login    ${AFS_ADMIN}
    Command Should Succeed    ${FS} sa ${PRIV_PATH} system:anyuser l
    Logout
    Run Keyword and Expect Error    *
    ...    Remove File    ${PRIV_PATH}/privfile
    # HACK: we need proper setup and teardowns!
    Login    ${AFS_ADMIN}
    Command Should Succeed    ${FS} sa ${PRIV_PATH} user1 none
    Logout
    Remove PRIV File

New Directory for User1
    User1
    Command Should Fail           mkdir ${PRIV_PATH}/new_priv
    Command Should Succeed        mkdir ${PUB_PATH}/new_pub
    Remove Directory              ${PUB_PATH}/new_pub
    Logout

New Directory for Anyuser
    Command Should Fail           mkdir ${PRIV_PATH}/new_priv
    Command Should Succeed        mkdir ${PUB_PATH}/new_pub
    Remove Directory              ${PUB_PATH}/new_pub

