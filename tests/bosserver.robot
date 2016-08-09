# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Bosserver tests
Resource          openafs.robot
Suite Setup       Setup Users and Groups
Suite Teardown    Teardown Users and Groups

*** Variables ***
${VOLUME}      test.basic
${PARTITION}   a
${SERVER}      ${HOSTNAME}
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

*** Test Cases ***
Add a Bosserver Host
    [Tags]  todo  arla  #(bosaddhost)
    TODO

List Server Hosts
    [Tags]  arla  #(bostlisthosts)
    ${output}=  Run       ${BOS} listhosts ${HOSTNAME}
    Should Contain        ${output}  ${AFS_CELL}

Remove a Server Host
    [Tags]  todo  arla  #(bosremovehost)
    TODO

Add a Superuser
    [Tags]  arla  #(bosadduser)
    ${output}=  Run           ${BOS} listusers ${HOSTNAME}
    Should Not Contain        ${output}  user1
    Command Should Succeed    ${BOS} adduser ${HOSTNAME} user1
    ${output}=  Run           ${BOS} listusers ${HOSTNAME}
    Should Contain            ${output}  user1
    Command Should Succeed    ${BOS} removeuser ${HOSTNAME} user1
    ${output}=  Run           ${BOS} listusers ${HOSTNAME}
    Should Not Contain        ${output}  user1

List Superusers
    [Tags]  arla  #(boslistusers)
    ${output}=  Run           ${BOS} listusers ${HOSTNAME}
    Should Not Contain        ${output}  user1

Remove a Superuser
    [Tags]  arla  #(bosremoveuser)
    ${output}=  Run           ${BOS} listusers ${HOSTNAME}
    Should Not Contain        ${output}  user2
    Command Should Succeed    ${BOS} adduser ${HOSTNAME} user2
    ${output}=  Run           ${BOS} listusers ${HOSTNAME}
    Should Contain            ${output}  user2
    Command Should Succeed    ${BOS} removeuser ${HOSTNAME} user2
    ${output}=  Run           ${BOS} listusers ${HOSTNAME}
    Should Not Contain        ${output}  user2

Install an Executable Shell Script
    [Tags]  todo  arla  #(bosinstall)
    TODO

Execute Something Via the bosserver
    [Tags]  todo  arla  #(bosexec)
    TODO

Create a bos bnode
    [Tags]  todo  arla  #(boscreate)
    TODO

Delete a Running bnode
    [Tags]  todo  arla  #(bosdeleterunning)
    TODO

Get a bnode Status
    [Tags]  arla  #(bosstatus)
    ${output}=  Run            ${BOS} status ${HOSTNAME}
    Should Contain             ${output}  ptserver
    Should Contain             ${output}  vlserver
    Should Contain             ${output}  dafs

Stop a bos bnode
    [Tags]  todo  arla  #(bosstop)
    TODO

Restart a bos bnode
    [Tags]  todo  arla  #(bosrestartstopped)
    Command Should Succeed     ${BOS} restart ${HOSTNAME} -instance ptserver vlserver
    ${output}=  Run            ${BOS} status ${HOSTNAME}
    Should Contain             ${output}  ptserver
    Should Contain             ${output}  vlserver

Start a bos bnode
    [Tags]  todo  arla  #(bosstart)
    TODO

Shutdown a bnode
    [Tags]  todo  arla  #(bosshutdown)
    TODO

Delete a Stopped bnode
    [Tags]  todo  arla  #(bosdelete)
    TODO

Add a Key
    [Tags]  todo  arla  #(bosaddkey)
    TODO

List Keys
    [Tags]  todo  arla  #(boslistkeys)
    TODO

Remove a Key
    [Tags]  todo  arla  #(bosremovekey)
    TODO

Salvage a Volume
    [Tags]  todo  arla  #(bossalvagevolume)
    TODO

Salvage a Partition
    [Tags]  todo  arla  #(bossalvagepart)
    TODO

Salvage a Server
    [Tags]  todo  arla  #(bossalvageserver)
    TODO

