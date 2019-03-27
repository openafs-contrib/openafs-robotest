# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Library           OperatingSystem
Library           String
Library           OpenAFSLibrary
Suite Setup       Login  ${AFS_ADMIN}  password=${AFS_ADMIN_LOGIN}
Suite Teardown    Logout

*** Variables ***
${SERVER}        @{AFS_FILESERVERS}[0]
${PART}          a
${OTHERPART}     b


*** Test Cases ***
Release a Volume
    [Setup]     Create Volume  xyzzy  ${SERVER}  ${PART}
    [Teardown]  Remove Volume  xyzzy
    Command Should Succeed    ${VOS} addsite ${SERVER} ${PART} xyzzy
    Command Should Succeed    ${VOS} release xyzzy
    Volume Should Exist       xyzzy.readonly
    Volume Location Matches   xyzzy  server=${SERVER}  part=${PART}  vtype=ro

Avoid creating a rogue volume during release
    [Tags]         rogue-avoidance
    [Teardown]     Run Keywords    Remove volume    xyzzz
    ...            AND             Cleanup Rogue    ${vid}
    Set test variable    ${vid}    0
    ${vid}=        Create volume    xyzzy    ${SERVER}    ${OTHERPART}    orphan=True
    Command Should Succeed    ${VOS} create ${SERVER} a xyzzz -roid ${vid}
    Command Should Succeed    ${VOS} addsite ${SERVER} a xyzzz
    Command Should Fail       ${VOS} release xyzzz

*** Keywords ***
Cleanup Rogue
    [Arguments]     ${vid}
    Remove volume   ${vid}    server=${SERVER}
    Remove volume   ${vid}    server=${SERVER}    zap=True
