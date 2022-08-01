*** Comments ***
# Copyright (c) 2015 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation       Client stess tests

Library             OperatingSystem
Library             String
Library             OpenAFSLibrary

*** Variables ***
${VOLUME}       test.stress
${PARTITION}    a
${SERVER}       ${AFS_FILESERVER_A}
${RWPATH}       /afs/.${AFS_CELL}/test/stress

*** Test Cases ***
| Create a Large Number of Entries in a Directory
|  | [Tags]       | slow
|  | [Setup]      | Create Stress Test Volume
|  | Create Files | ${RWPATH}                 | 31707 | 0
|  | [Teardown]   | Remove Stress Test Volume

*** Keywords ***
| Create Stress Test Volume
|  | Login         | ${AFS_ADMIN} | keytab=${AFS_ADMIN_KEYTAB}
|  | Create Volume | ${VOLUME}    | server=${SERVER}           | part=${PARTITION} | path=${RWPATH} | ro=True | acl=system:anyuser,read
|
| Remove Stress Test Volume
|  | Remove Volume | ${VOLUME} | path=${RWPATH}
|  | Logout
