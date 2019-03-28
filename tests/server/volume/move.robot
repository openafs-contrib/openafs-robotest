# Copyright (c) 2015 Sine Nomine Associates
# See LICENSE

*** Settings ***
Library           OperatingSystem
Library           String
Library           OpenAFSLibrary
Suite Setup       Login  ${AFS_ADMIN}  password=${AFS_ADMIN_PASSWORD}
Suite Teardown    Logout

*** Variables ***
${SERVER1}       @{AFS_FILESERVERS}[0]
${SERVER2}       @{AFS_FILESERVERS}[1]
${PART1}         a
${PART2}         b

*** Test Cases ***
Move a Volume
    [Setup]     Create Volume  xyzzy  ${SERVER1}  ${PART1}
    [Teardown]  Remove Volume  xyzzy
    Command Should Succeed   ${VOS} move xyzzy ${SERVER1} ${PART1} ${SERVER1} ${PART2}
    Volume Should Exist      xyzzy
    Volume Location Matches  xyzzy  server=${SERVER1}  part=${PART2}

Move a volume between servers
    [Tags]      requires-multi-fs
    [Setup]     Create Volume  xyzzy  ${SERVER1}  ${PART1}
    [Teardown]  Remove Volume  xyzzy
    Command Should Succeed   ${VOS} move xyzzy ${SERVER1} ${PART1} ${SERVER2} ${PART1}

Avoid creating a rogue volume during move
    [Tags]      requires-multi-fs  bug
    [Teardown]  Cleanup Rogue    ${vid}   @{AFS_FILESERVERS}[1]
    ${vid}=            Create volume    xyzzy    ${SERVER2}    ${PART2}    orphan=True
    Command Should Succeed    ${VOS} create -server ${SERVER1} -part ${PART1} -name xyzzy -id ${vid}
    Command Should Fail       ${VOS} move xyzzy ${SERVER1} ${PART1} ${SERVER2} ${PART1}

*** Keywords ***
Cleanup Rogue
    [Arguments]     ${vid}    ${server}
    Remove volume   ${vid}
    Remove volume   ${vid}    server=${server}    zap=True
