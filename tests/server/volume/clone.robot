# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Library           OperatingSystem
Library           String
Library           OpenAFSLibrary
Suite Setup       Login  ${AFS_ADMIN}  password=${AFS_ADMIN_PASSWORD}
Suite Teardown    Logout

*** Variables ***
${SERVER}      @{AFS_FILESERVERS}[0]
${PART}        a
${OTHERPART}   b

*** Test Cases ***
Avoid creating a rogue volume during clone
    [Tags]         rogue-avoidance
    [Teardown]     Run Keywords    Remove volume    xyzzz
    ...            AND             Cleanup Rogue    ${vid}
    Set test variable    ${vid}    0
    ${vid}=        Create volume    xyzzy    ${SERVER}    ${OTHERPART}    orphan=True
    Command Should Succeed    ${VOS} create ${SERVER} ${PART} xyzzz
    Command Should Fail       ${VOS} clone xyzzz ${SERVER} ${PART} -toid ${vid}

*** Keywords ***
Cleanup Rogue
    [Arguments]     ${vid}
    Remove volume   ${vid}    server=${SERVER}
    Remove volume   ${vid}    server=${SERVER}    zap=True
