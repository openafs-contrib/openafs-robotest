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
${SERVER}      @{AFS_FILESERVERS}[0]
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
    ${output}=  Run           ${BOS} listusers ${SERVER}
    Should Not Contain        ${output}  user1

Superusers Include User1
    ${output}=  Run           ${BOS} listusers ${SERVER}
    Should Contain            ${output}  user1

Add Superuser
    Superusers Exclude User1
    Command Should Succeed    ${BOS} adduser ${SERVER} user1

Remove Superuser
    Command Should Succeed    ${BOS} removeuser ${SERVER} user1
    Superusers Exclude User1

*** Test Cases ***
List Server Hosts
    ${output}=  Run       ${BOS} listhosts ${SERVER}
    Should Contain        ${output}  ${AFS_CELL}

Add a Superuser
    [Setup]      Superusers Exclude User1
    Command Should Succeed    ${BOS} adduser ${SERVER} user1
    Superusers Include User1
    [Teardown]   Remove Superuser

List Superusers
    ${output}=  Run           ${BOS} listusers ${SERVER}
    Should Not Contain        ${output}  user1

Remove a Superuser
    [Setup]      Add Superuser
    Superusers Include User1
    Command Should Succeed    ${BOS} removeuser ${SERVER} user1
    [Teardown]   Superusers Exclude User1

Get a bnode Status
    ${output}=  Run            ${BOS} status ${SERVER}
    Should Contain             ${output}  ptserver
    Should Contain             ${output}  vlserver
    Should Contain             ${output}  dafs
