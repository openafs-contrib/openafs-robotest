*** Comments ***
# Copyright (c) 2015 Sine Nomine Associates
# See LICENSE

*** Settings ***
Library             OperatingSystem
Library             String
Library             OpenAFSLibrary

Suite Setup         Login    ${AFS_ADMIN}    keytab=${AFS_ADMIN_KEYTAB}
Suite Teardown      Logout

*** Variables ***
${SERVER}       ${AFS_FILESERVER_A}
${PART}         a
${OTHERPART}    b

*** Test Cases ***
| Avoid creating a rogue volume during clone
|  | [Tags]                 | rogue-avoidance
|  | Set test variable      | ${vid}                                            | 0
|  | ${vid}=                | Create volume                                     | xyzzy         | ${SERVER} | ${OTHERPART} | orphan=True
|  | Command Should Succeed | ${VOS} create ${SERVER} ${PART} xyzzz
|  | Command Should Fail    | ${VOS} clone xyzzz ${SERVER} ${PART} -toid ${vid}
|  | [Teardown]             | Run Keywords                                      | Remove volume | xyzzz
|  | ...                    | AND                                               | Cleanup Rogue | ${vid}

*** Keywords ***
| Cleanup Rogue
|  | [Arguments]   | ${vid}
|  | Remove volume | ${vid} | server=${SERVER}
|  | Remove volume | ${vid} | server=${SERVER} | zap=True
