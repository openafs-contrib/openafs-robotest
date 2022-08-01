*** Comments ***
# Copyright (c) 2015 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation       Volserver/vlserver tests

Library             OperatingSystem
Library             String
Library             OpenAFSLibrary

Suite Setup         Login    ${AFS_ADMIN}    keytab=${AFS_ADMIN_KEYTAB}
Suite Teardown      Logout

*** Variables ***
${SERVER}       ${AFS_FILESERVER_A}
${VOLID}        0
${PART}         a

*** Test Cases ***
| Create a Volume
|  | Volume Should Not Exist | xyzzy
|  | Command Should Succeed  | ${VOS} create ${SERVER} ${PART} xyzzy
|  | Volume Should Exist     | xyzzy
|  | Volume Location Matches | xyzzy                                 | server=${SERVER} | part=${PART}
|  | [Teardown]              | Remove Volume                         | xyzzy
|
| Add a Replication Site
|  | [Setup]                | Create Volume                    | xyzzy | ${SERVER} | ${PART}
|  | Command Should Succeed | ${VOS} addsite ${SERVER} a xyzzy
|  | Command Should Succeed | ${VOS} remsite ${SERVER} a xyzzy
|  | [Teardown]             | Remove Volume                    | xyzzy
|
| Remove a Replication Site
|  | [Setup]                | Create Volume                    | xyzzy                  | ${SERVER}                                | ${PART}
|  | Command Should Succeed | ${VOS} addsite ${SERVER} a xyzzy
|  | Command Should Succeed | ${VOS} release xyzzy
|  | Command Should Succeed | ${VOS} remsite ${SERVER} a xyzzy
|  | Volume Should Exist    | xyzzy.readonly
|  | [Teardown]             | Run Keywords                     | Command Should Succeed | ${VOS} remove ${SERVER} a xyzzy.readonly
|  | ...                    | AND                              | Remove Volume          | xyzzy
|
| Remove a Replicated Volume
|  | [Setup]                 | Create Volume                                | xyzzy | ${SERVER} | ${PART}
|  | Command Should Succeed  | ${VOS} addsite ${SERVER} a xyzzy
|  | Command Should Succeed  | ${VOS} release xyzzy
|  | Command Should Succeed  | ${VOS} remove ${SERVER} a -id xyzzy.readonly
|  | Command Should Succeed  | ${VOS} remove -id xyzzy
|  | Volume Should Not Exist | xyzzy.readonly
|  | Volume Should Not Exist | xyzzy
|  | [Teardown]              | Remove Volume                                | xyzzy
|
| Display Volume Header Information
|  | [Setup]        | Create Volume | xyzzy                      | ${SERVER} | ${PART}
|  | ${output}=     | Run           | ${VOS} listvol ${SERVER} a
|  | Should Contain | ${output}     | xyzzy
|  | [Teardown]     | Remove Volume | xyzzy
|
| Display VLDB Information
|  | [Setup]        | Create Volume | xyzzy                             | ${SERVER} | ${PART}
|  | ${output}=     | Run           | ${VOS} listvldb -server ${SERVER}
|  | Should Contain | ${output}     | xyzzy
|  | [Teardown]     | Remove Volume | xyzzy
|
| Display Header and VLDB Information
|  | [Setup]        | Create Volume | xyzzy                | ${SERVER} | ${PART}
|  | ${output}=     | Run           | ${VOS} examine xyzzy
|  | Should Contain | ${output}     | xyzzy
|  | [Teardown]     | Remove Volume | xyzzy
|
| Avoid creating a rogue volume during create
|  | [Tags]              | rogue-avoidance
|  | Set test variable   | ${vid}                                                         | 0
|  | ${vid}=             | Create volume                                                  | xyzzy  | ${SERVER} | a | orphan=True
|  | Command Should Fail | ${VOS} create -server ${SERVER} -part b -name xyzzy -id ${vid}
|  | [Teardown]          | Cleanup Rogue                                                  | ${vid}

*** Keywords ***
| Cleanup Rogue
|  | [Arguments]   | ${vid}
|  | Remove volume | ${vid} | server=${SERVER}
|  | Remove volume | ${vid} | server=${SERVER} | zap=True
