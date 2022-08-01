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
| Release a Volume
|  | [Setup]                 | Create Volume                          | xyzzy            | ${SERVER}    | ${PART}
|  | Command Should Succeed  | ${VOS} addsite ${SERVER} ${PART} xyzzy
|  | Command Should Succeed  | ${VOS} release xyzzy
|  | Volume Should Exist     | xyzzy.readonly
|  | Volume Location Matches | xyzzy                                  | server=${SERVER} | part=${PART} | vtype=ro
|  | [Teardown]              | Remove Volume                          | xyzzy
|
| Avoid creating a rogue volume during release
|  | [Tags]                 | rogue-avoidance
|  | Set test variable      | ${vid}                                       | 0
|  | ${vid}=                | Create volume                                | xyzzy         | ${SERVER} | ${OTHERPART} | orphan=True
|  | Command Should Succeed | ${VOS} create ${SERVER} a xyzzz -roid ${vid}
|  | Command Should Succeed | ${VOS} addsite ${SERVER} a xyzzz
|  | Command Should Fail    | ${VOS} release xyzzz
|  | [Teardown]             | Run Keywords                                 | Remove volume | xyzzz
|  | ...                    | AND                                          | Cleanup Rogue | ${vid}

*** Keywords ***
| Cleanup Rogue
|  | [Arguments]   | ${vid}
|  | Remove volume | ${vid} | server=${SERVER}
|  | Remove volume | ${vid} | server=${SERVER} | zap=True
