# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Resource          common.robot
Suite Setup       Login  ${AFS_ADMIN}
Suite Teardown    Logout

*** Variables ***
${SERVER}        @{AFS_FILESERVERS}[0]


*** Test Cases ***
Move a Volume
    [Setup]     Create Volume  xyzzy
    [Teardown]  Remove Volume  xyzzy
    Command Should Succeed   ${VOS} move xyzzy ${SERVER} a ${SERVER} b
    Volume Should Exist      xyzzy
    Volume Location Matches  xyzzy  server=${SERVER}  part=b

Move a volume between servers
    [Tags]      requires-multi-fs
    [Setup]     Create Volume  xyzzy
    [Teardown]  Remove Volume  xyzzy
    Log Variables
    ${from_server}=    Set Variable    @{AFS_FILESERVERS}[0]
    ${to_server}=      Set Variable    @{AFS_FILESERVERS}[1]
    Command Should Succeed   ${VOS} move xyzzy ${from_server} a ${to_server} a

Avoid creating a rogue volume during move
    [Tags]      requires-multi-fs
    [Teardown]  Cleanup Rogue    ${vid}   @{AFS_FILESERVERS}[1]
    ${from_server}=    Set Variable    @{AFS_FILESERVERS}[0]
    ${to_server}=      Set Variable    @{AFS_FILESERVERS}[1]
    ${vid}=            Create volume    xyzzy    ${to_server}    b    orphan=True
    Command Should Succeed    ${VOS} create -server ${from_server} -part a -name xyzzy -id ${vid}
    Command Should Fail       ${VOS} move xyzzy ${from_server} a ${to_server} a

*** Keywords ***
Cleanup Rogue
    [Arguments]     ${vid}    ${server}
    Remove volume   ${vid}
    Remove volume   ${vid}    server=${server}    zap=True
