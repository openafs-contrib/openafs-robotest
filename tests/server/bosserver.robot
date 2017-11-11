# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Bosserver tests
Resource          common.robot
Suite Setup       Setup Users and Groups
Suite Teardown    Teardown Users and Groups

*** Variables ***
${VOLUME}      test.basic
${PARTITION}   a
${SERVER}      ${FILESERVER}
${TESTPATH}    /afs/.${AFS_CELL}/test/${VOLUME}

*** Keywords ***
Setup Users and Groups
    Login  ${AFS_ADMIN}
    Command Should Succeed  ${PTS} createuser user1
    Command Should Succeed  ${PTS} createuser user2
    Command Should Succeed  ${PTS} creategroup group1 -owner ${AFS_ADMIN}
    Command Should Succeed  ${PTS} adduser user1 group1
    Command Should Succeed  ${PTS} adduser user2 group1

Teardown Users and Groups
    Command Should Succeed  ${PTS} delete user1
    Command Should Succeed  ${PTS} delete user2
    Command Should Succeed  ${PTS} delete group1
    Logout

Superusers Exclude User1
    ${output}=  Run           ${BOS} listusers ${FILESERVER}
    Should Not Contain        ${output}  user1

Superusers Include User1
    ${output}=  Run           ${BOS} listusers ${FILESERVER}
    Should Contain            ${output}  user1

Add Superuser
    Superusers Exclude User1
    Command Should Succeed    ${BOS} adduser ${FILESERVER} user1

Remove Superuser
    Command Should Succeed    ${BOS} removeuser ${FILESERVER} user1
    Superusers Exclude User1

*** Test Cases ***
Add a Bosserver Host
    [Tags]  todo  #(bosaddhost)
    TODO

List Server Hosts
    [Tags]  #(bostlisthosts)
    ${output}=  Run       ${BOS} listhosts ${FILESERVER}
    Should Contain        ${output}  ${AFS_CELL}

Remove a Server Host
    [Tags]  todo  #(bosremovehost)
    TODO

Add a Superuser
    [Tags]  #(bosadduser)
    [Setup]      Superusers Exclude User1
    Command Should Succeed    ${BOS} adduser ${FILESERVER} user1
    Superusers Include User1
    [Teardown]   Remove Superuser

List Superusers
    [Tags]  #(boslistusers)
    ${output}=  Run           ${BOS} listusers ${FILESERVER}
    Should Not Contain        ${output}  user1

Remove a Superuser
    [Tags]  #(bosremoveuser)
    [Setup]      Add Superuser
    Superusers Include User1
    Command Should Succeed    ${BOS} removeuser ${FILESERVER} user1
    [Teardown]   Superusers Exclude User1

Install an Executable Shell Script
    [Tags]  todo  #(bosinstall)
    TODO

Execute Something Via the bosserver
    [Tags]  todo  #(bosexec)
    TODO

Create a bos bnode
    [Tags]  todo  #(boscreate)
    TODO

Delete a Running bnode
    [Tags]  todo  #(bosdeleterunning)
    TODO

Get a bnode Status
    [Tags]  #(bosstatus)
    ${output}=  Run            ${BOS} status ${FILESERVER}
    Should Contain             ${output}  ptserver
    Should Contain             ${output}  vlserver
    Should Contain             ${output}  dafs

Stop a bos bnode
    [Tags]  todo  #(bosstop)
    TODO

Restart a bos bnode
    [Tags]  todo  #(bosrestartstopped)
    Command Should Succeed     ${BOS} restart ${FILESERVER} -instance ptserver vlserver
    ${output}=  Run            ${BOS} status ${FILESERVER}
    Should Contain             ${output}  ptserver
    Should Contain             ${output}  vlserver

Start a bos bnode
    [Tags]  todo  #(bosstart)
    TODO

Shutdown a bnode
    [Tags]  todo  #(bosshutdown)
    TODO

Delete a Stopped bnode
    [Tags]  todo  #(bosdelete)
    TODO

Add a Key
    [Tags]  todo  #(bosaddkey)
    TODO

List Keys
    [Tags]  todo  #(boslistkeys)
    TODO

Remove a Key
    [Tags]  todo  #(bosremovekey)
    TODO

Salvage a Volume
    [Tags]  todo  #(bossalvagevolume)
    TODO

Salvage a Partition
    [Tags]  todo  #(bossalvagepart)
    TODO

Salvage a Server
    [Tags]  todo  #(bossalvageserver)
    TODO

