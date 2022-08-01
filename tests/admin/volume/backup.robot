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
| Create a Backup Volume
|  | [Setup]        | Create Volume | xyzzy               | ${SERVER} | ${PART}
|  | ${output}=     | Run           | ${VOS} backup xyzzy
|  | Should Contain | ${output}     | xyzzy
|  | [Teardown]     | Remove Volume | xyzzy
|
| Avoid creating a rogue volume during backup
|  | [Tags]                 | rogue-avoidance
|  | Set test variable      | ${vid}                                           | 0
|  | Command Should Succeed | ${VOS} create ${SERVER} ${PART} xyzzy
|  | Command Should Succeed | ${VOS} remove ${SERVER} ${PART} -id xyzzy
|  | ${vid_bk}=             | Create volume                                    | xyzzy         | ${SERVER} | ${OTHERPART} | orphan=True
|  | ${vid}=                | Evaluate                                         | ${vid_bk} - 2
|  | Command Should Succeed | ${VOS} create ${SERVER} ${PART} xyzzz -id ${vid}
|  | Command Should Fail    | ${VOS} backup xyzzz
|  | [Teardown]             | Run Keywords                                     | Remove volume | xyzzz
|  | ...                    | AND                                              | Cleanup Rogue | ${vid_bk}

*** Keywords ***
| Cleanup Rogue
|  | [Arguments]   | ${vid}
|  | Remove volume | ${vid} | server=${SERVER}
|  | Remove volume | ${vid} | server=${SERVER} | zap=True
