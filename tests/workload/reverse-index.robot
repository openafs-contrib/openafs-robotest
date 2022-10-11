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
${FILENAME}     hello
${FILEPATH}     ${PATH}/${FILENAME}
${LINKNAME}     link
${LINKPATH}     ${PATH}/${LINKNAME}

*** Test Cases ***
| Name from FID Reverse Index test
|  | [Setup]                    | Create File      | ${FILEPATH}  | Hello world
|  | ${FID}=                    | Get FID          | ${FILEPATH}
|  | ${NAME}                    | Get Name by FID  | ${FID}
|  | Should be equal as strings | ${FILENAME}      | ${NAME}
|  | [Teardown]                 | Remove File      | ${FILEPATH}
| File with Hard Link Reverse Index test
|  | [Setup]               | Run Keywords
|  | ...                   | Should Not Exist | ${FILEPATH} | AND
|  | ...                   | Should Not Exist | ${LINKPATH} | AND
|  | ...                   | Create File      | ${FILEPATH} | Hello world
|  | Link Count Should Be  | ${FILEPATH}      | 1
|  | Link                  | ${FILEPATH}      | ${LINKPATH}
|  | Inode Should Be Equal | ${LINKPATH}      | ${FILEPATH}
|  | Link Count Should Be  | ${FILEPATH}      | 2
|  | Link Count Should Be  | ${LINKPATH}      | 2
|  | ${FID}=                    | Get FID          | ${FILEPATH}
|  | ${NAME}                    | Get Name by FID  | ${FID}
|  | Should be equal as strings | ${FILENAME}      | ${NAME} | OR
|  | ...                        | ${LINKNAME}      | ${NAME}   
|  | Unlink                | ${FILEPATH}
|  | Should Not Exist      | ${FILEPATH}
|  | Link Count Should Be  | ${LINKPATH}          | 1
|  | ${NAME}               | Get Name by FID      | ${FID}
|  | Should be equal as strings | ${LINKNAME}     | ${NAME} 
|  | [Teardown]            | Run Keyword
|  | ...                   | Remove File          | ${LINKPATH}


*** Keywords ***
| Setup
|  | Login         | ${AFS_ADMIN} | keytab=${AFS_ADMIN_KEYTAB}
|  | Create Volume | ${VOLUME}    | server=${SERVER}           | part=${PARTITION} | path=${PATH} | acl=system:anyuser,read
|
| Teardown
|  | Remove Volume | ${VOLUME} | path=${PATH}
|  | Logout
