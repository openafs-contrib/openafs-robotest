*** Comments ***
# Copyright (c) 2022 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation       Reverse Index tests

Library             OperatingSystem
Library             String
Library             OpenAFSLibrary

Suite Setup         Setup
Suite Teardown      Teardown

*** Variables ***
${VOLUME}       test.ri
${PARTITION}    a
${SERVER}       ${AFS_FILESERVER_A}
${PATH}         /afs/.${AFS_CELL}/test/${VOLUME}
${FILE}         hello.txt


*** Test Cases ***
| Name from FID
|  | [Setup]                    | Create File      | ${PATH}/${FILE}  | Hello world
|  | ${FID}=                    | Get FID          | ${PATH}/${FILE}
|  | ${NAME}                    | Get Name by FID  | ${FID}
|  | Should be equal as strings | ${FILE}          | ${NAME}
|  | [Teardown]                 | Remove File      | ${PATH}/${FILE}


*** Keywords ***
| Setup
|  | Login         | ${AFS_ADMIN} | keytab=${AFS_ADMIN_KEYTAB}
|  | Create Volume | ${VOLUME}    | server=${SERVER}           | part=${PARTITION} | path=${PATH} | acl=system:anyuser,read
|
| Teardown
|  | Remove Volume | ${VOLUME} | path=${PATH}
|  | Logout
