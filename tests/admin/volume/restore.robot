*** Comments ***
# Copyright (c) 2015-2017 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation       Tests to verify volume restore operations with the
...                 various of the restore options and to test the volume
...                 server robustness while attempting to restore invalid
...                 volume dump streams.

Library             OperatingSystem
Library             String
Library             OpenAFSLibrary

Suite Setup         Login    ${AFS_ADMIN}    keytab=${AFS_ADMIN_KEYTAB}
Suite Teardown      Logout
Test Teardown       Cleanup

*** Variables ***
${VOLUME}       test.restore
${PART}         a
${SERVER}       ${AFS_FILESERVER_A}
${DUMP}         /tmp/test.dump

*** Test Cases ***
| Restore a volume
|  | Volume should not exist | ${VOLUME}
|  | Create dump             | ${DUMP}                                                                  | size=small
|  | Command should succeed  | ${VOS} restore ${SERVER} ${PART} ${VOLUME} -file ${DUMP} -overwrite full
|  | Volume should exist     | ${VOLUME}
|  | Volume location matches | ${VOLUME}                                                                | ${SERVER}  | ${PART} | vtype=rw
|
| Restore an empty volume
|  | Volume should not exist | ${VOLUME}
|  | Create dump             | ${DUMP}                                                                  | size=empty
|  | Command should succeed  | ${VOS} restore ${SERVER} ${PART} ${VOLUME} -file ${DUMP} -overwrite full
|  | Volume should exist     | ${VOLUME}
|  | Volume location matches | ${VOLUME}                                                                | ${SERVER}  | ${PART} | vtype=rw
|
| Restore a Volume Containing a Bogus ACL
|  | Volume should not exist | ${VOLUME}
|  | Create dump             | ${DUMP}                                                                  | size=small | contains=bogus-acl
|  | Command Should Fail     | ${VOS} restore ${SERVER} ${PART} ${VOLUME} -file ${DUMP} -overwrite full
|
| Avoid creating a rogue volume during restore
|  | [Tags]              | rogue-avoidance
|  | Set test variable   | ${vid}                                                                                            | 0
|  | ${vid}=             | Create volume                                                                                     | ${VOLUME}  | ${SERVER} | a | orphan=True
|  | Create dump         | ${DUMP}                                                                                           | size=small
|  | Command should fail
|  | ...                 | ${VOS} restore -server ${SERVER} -part b -name ${VOLUME} -id ${vid} -file ${DUMP} -overwrite full
|  | [Teardown]          | Cleanup Rogue                                                                                     | ${vid}

*** Keywords ***
| Cleanup
|  | Remove volume | ${VOLUME}
|  | Remove file   | ${DUMP}
|
| Cleanup Rogue
|  | [Arguments]   | ${vid}
|  | Remove volume | ${vid}  | server=${SERVER}
|  | Remove volume | ${vid}  | server=${SERVER} | zap=True
|  | Remove file   | ${DUMP}
