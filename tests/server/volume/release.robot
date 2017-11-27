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
Release a Volume
    [Setup]     Create Volume  xyzzy
    [Teardown]  Remove Volume  xyzzy
    Command Should Succeed    ${VOS} addsite ${SERVER} a xyzzy
    Command Should Succeed    ${VOS} release xyzzy
    Volume Should Exist       xyzzy.readonly
    Volume Location Matches   xyzzy  server=${SERVER}  part=a  vtype=ro

Avoid creating a rogue volume during release
    [Tags]         rogue-avoidance
    [Teardown]     Run Keywords    Remove volume    xyzzz
    ...            AND             Cleanup Rogue    ${vid}
    Set test variable    ${vid}    0
    ${vid}=        Create volume    xyzzy    ${SERVER}    b    orphan=True
    Command Should Succeed    ${VOS} create ${SERVER} a xyzzz -roid ${vid}
    Command Should Succeed    ${VOS} addsite ${SERVER} a xyzzz
    Command Should Fail       ${VOS} release xyzzz

*** Keywords ***
Cleanup Rogue
    [Arguments]     ${vid}
    Remove volume   ${vid}    server=${SERVER}
    Remove volume   ${vid}    server=${SERVER}    zap=True
