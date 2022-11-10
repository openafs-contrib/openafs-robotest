*** Comments ***
# Copyright (c) 2022 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation       Reverse Index tests

Library             OperatingSystem
Library             String
Library             OpenAFSLibrary

Suite Setup          Setup
Suite Teardown       Teardown

*** Variables ***
${VOLUME}       test.ri
${PARTITION}    a
${SERVER}       ${AFS_FILESERVER_A}
${PATH}         /afs/.${AFS_CELL}/test/${VOLUME}
${FILENAME}     hello
${FILEPATH}     ${PATH}/${FILENAME}
${LINKNAME}     link
${LINKPATH}     ${PATH}/${LINKNAME}
${DIR1}         ${PATH}/ParentDir
${DIR2}         ${DIR1}/ChildDir
${FILE1}        ${DIR1}/level1
${FILE2}        ${DIR2}/level2
${DUMPFILE_T}   /home/vikram/TEMP/ridb_dump
${SAMPLEFILE}   /home/vikram/TEMP/sample

*** Test Cases ***
| Name from FID Reverse Index test
|  | [Setup]                    | Create File      | ${FILEPATH}  | Hello world
|  | ${FID}=                    | Get FID          | ${FILEPATH}
|  | ${NAME}                    | Get Name by FID  | ${FID}
|  | Should be equal as strings | ${FILENAME}      | ${NAME}
|  | Remove File      | ${FILEPATH}
|  | Should Not Be in RIDB |  ${FID}
|  | [Teardown]                 | Run Keyword
|  | ...                        | Remove File      | ${FILEPATH}
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
|  | Unlink                | ${LINKPATH}
|  | Should Not Be in RIDB |  ${FID}
|  | [Teardown]            | Run Keywords


| Dump RIDB Test
|  | [Tags]                       | requires-root | requires-local-fileserver
|  | [Setup]                      | Run Keywords
|  | ...                          | Should Not Exist | ${DIR1}  | AND
|  | ...                          | Create Directory | ${DIR1}  | AND
|  | ...                          | Should Not Exist | ${DIR2}  | AND
|  | ...                          | Create Directory | ${DIR2}  | AND
|  | ...                          | Should Not Exist | ${FILE1} | AND
|  | ...                          | Should Not Exist | ${FILE2} | AND
|  | ...                          | Should Not Exist | ${FILEPATH} | AND
|  | ...                          | Create File      | ${FILEPATH}  | Hi | AND
|  | ...                          | Create File      | ${FILE1}  | Heh | AND
|  | ...                          | Create File      | ${FILE2}  | Huh
|  | Should Exist                 | ${DIR1}
|  | Should Exist                 | ${DIR2}
|  | Should Exist                 | ${FILE1}
|  | Should Exist                 | ${FILE2}
|  | Should Exist                 | ${FILEPATH}
|  | Dump RIDB                    | partid=${PARTITION} |  vol=${VOLUME} | fname=${DUMPFILE_T}
|  | Generate Simple RIDB         | fname=${SAMPLEFILE}
|  | ${F1} = | Get File           | ${DUMPFILE_T}
|  | ${F2} = | Get File           | ${SAMPLEFILE}
|  | Should Be Equal As Strings   |    ${F1}         | ${F2}
|  | [Teardown]                   | Run Keywords
|  | ...                          | Remove File      | ${FILE1}  | AND
|  | ...                          | Remove File      | ${FILE2}  | AND
|  | ...                          | Remove Directory | ${DIR2}   | AND
|  | ...                          | Remove Directory | ${DIR1}   | AND
|  | ...                          | Should Not Exist | ${DIR1}   | AND
|  | ...                          | Should Not Exist | ${DIR2}   | AND
|  | ...                          | Remove File      | ${FILEPATH}
| 

*** Keywords ***
| Setup
|  | Login         | ${AFS_ADMIN} | keytab=${AFS_ADMIN_KEYTAB}
|  | Create Volume | ${VOLUME}    | server=${SERVER}           | part=${PARTITION} | path=${PATH} | acl=system:anyuser,read
|
| Teardown
|  | Remove Volume | ${VOLUME} | path=${PATH}
|  | Logout
