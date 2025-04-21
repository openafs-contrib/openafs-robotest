*** Comments ***
# Copyright (c) 2014-2015 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation       Basic Functional Tests

Library             OperatingSystem
Library             String
Library             OpenAFSLibrary

Suite Setup         Setup
Suite Teardown      Teardown

*** Variables ***
${VOLUME}       test.basic
${PARTITION}    a
${SERVER}       ${AFS_FILESERVER_A}
${TESTPATH}     /afs/.${AFS_CELL}/test/${VOLUME}
${DIR2}         ${TESTPATH}/dir2
${DIR}          ${TESTPATH}/dir
${FILE1}        ${TESTPATH}/a
${FILE2}        ${TESTPATH}/b
${FILE3}        ${TESTPATH}/dir/file
${FILE}         ${TESTPATH}/file
${LINK2}        ${TESTPATH}/dir2/link
${LINK}         ${TESTPATH}/link
${NVOLUME}      ${TESTPATH}/xyzzy
${SCRIPT}       ${TESTPATH}/script.sh
${SYMLINK}      ${TESTPATH}/symlink
${TEXT}         hello-world

*** Test Cases ***
| Create a File
|  | [Setup]                | Run Keyword
|  | ...                    | Should Not Exist | ${FILE}
|  | Command Should Succeed | touch ${FILE}
|  | Should Be File         | ${FILE}
|  | Should Not Be Symlink  | ${FILE}
|  | [Teardown]             | Run Keywords
|  | ...                    | Remove File      | ${FILE} | AND
|  | ...                    | Should Not Exist | ${FILE}
|
| Create a Directory
|  | [Setup]          | Run Keyword
|  | ...              | Should Not Exist | ${DIR}
|  | Create Directory | ${DIR}
|  | Should Exist     | ${DIR}
|  | Should Be Dir    | ${DIR}
|  | Should Be Dir    | ${DIR}/.
|  | Should Be Dir    | ${DIR}/..
|  | [Teardown]       | Run Keywords
|  | ...              | Remove Directory | ${DIR} | AND
|  | ...              | Should Not Exist | ${DIR}
|
| Create a Symlink
|  | [Setup]           | Run Keywords
|  | ...               | Should Not Exist | ${DIR}     | AND
|  | ...               | Should Not Exist | ${SYMLINK} | AND
|  | ...               | Create Directory | ${DIR}
|  | Symlink           | ${DIR}           | ${SYMLINK}
|  | Should Be Symlink | ${SYMLINK}
|  | [Teardown]        | Run Keywords
|  | ...               | Unlink           | ${SYMLINK} | AND
|  | ...               | Remove Directory | ${DIR}     | AND
|  | ...               | Should Not Exist | ${DIR}     | AND
|  | ...               | Should Not Exist | ${SYMLINK}
|
| Create a Hard Link within a Directory
|  | [Tags]                | hardlink
|  | [Setup]               | Run Keywords
|  | ...                   | Should Not Exist | ${FILE} | AND
|  | ...                   | Should Not Exist | ${LINK} | AND
|  | ...                   | Create File      | ${FILE}
|  | Link Count Should Be  | ${FILE}          | 1
|  | Link                  | ${FILE}          | ${LINK}
|  | Inode Should Be Equal | ${LINK}          | ${FILE}
|  | Link Count Should Be  | ${FILE}          | 2
|  | Link Count Should Be  | ${LINK}          | 2
|  | Unlink                | ${LINK}
|  | Should Not Exist      | ${LINK}
|  | Link Count Should Be  | ${FILE}          | 1
|  | [Teardown]            | Run Keyword
|  | ...                   | Remove File      | ${FILE}
|
| Create a Hard Link within a Volume
|  | [Tags]     | hardlink
|  | [Setup]    | Run Keywords
|  | ...        | Should Not Exist | ${DIR}   | AND
|  | ...        | Should Not Exist | ${DIR2}  | AND
|  | ...        | Should Not Exist | ${LINK2} | AND
|  | ...        | Should Not Exist | ${FILE3} | AND
|  | ...        | Create Directory | ${DIR}   | AND
|  | ...        | Create Directory | ${DIR2}  | AND
|  | ...        | Create File      | ${FILE3}
|  | Link       | ${FILE3}         | ${LINK2} | code_should_be=EXDEV
|  | [Teardown] | Run Keywords
|  | ...        | Remove File      | ${FILE3} | AND
|  | ...        | Remove File      | ${LINK2} | AND
|  | ...        | Remove Directory | ${DIR}   | AND
|  | ...        | Remove Directory | ${DIR2}  | AND
|  | ...        | Should Not Exist | ${DIR}   | AND
|  | ...        | Should Not Exist | ${DIR2}  | AND
|  | ...        | Should Not Exist | ${LINK2} | AND
|  | ...        | Should Not Exist | ${FILE3}
|
| Create a Hard Link to a Directory
|  | [Tags]                       | hardlink
|  | [Setup]                      | Run Keywords
|  | ...                          | Should Not Exist | ${DIR}  | AND
|  | ...                          | Should Not Exist | ${LINK} | AND
|  | ...                          | Create Directory | ${DIR}
|  | Should Exist                 | ${DIR}
|  | Should Be Dir                | ${DIR}
|  | Run Keyword and Expect Error | *
|  | ...                          | Link             | ${DIR}  | ${LINK}
|  | [Teardown]                   | Run Keywords
|  | ...                          | Remove File      | ${LINK} | AND
|  | ...                          | Remove Directory | ${DIR}  | AND
|  | ...                          | Should Not Exist | ${DIR}  | AND
|  | ...                          | Should Not Exist | ${LINK}
|
| Create a Cross-Volume Hard Link
|  | [Tags]                       | hardlink
|  | [Setup]                      | Run Keywords
|  | ...                          | Should Not Exist | ${NVOLUME}  | AND
|  | ...                          | Create Volume    | xyzzy       | server=${SERVER} | part=${PARTITION} | path=${NVOLUME} | acl=system:anyuser,read
|  | Run Keyword and Expect Error | *
|  | ...                          | Link             | ${TESTPATH} | ${NVOLUME}
|  | [Teardown]                   | Run Keywords
|  | ...                          | Remove Volume    | xyzzy       | path=${NVOLUME}  | AND
|  | ...                          | Remove File      | ${NVOLUME}  | AND
|  | ...                          | Should Not Exist | ${NVOLUME}
|
| Touch a file
|  | [Setup]                | Run Keyword
|  | ...                    | Should Not Exist | ${FILE}
|  | Command Should Succeed | touch ${FILE}
|  | Should Exist           | ${FILE}
|  | [Teardown]             | Run Keywords
|  | ...                    | Remove File      | ${FILE} | AND
|  | ...                    | Should Not Exist | ${FILE}
|
| Timestamp rollover after 2147483647 (January 19, 2038 03:14:07 UTC)
|  | [Setup]                | Run Keyword
|  | ...                    | Should Not Exist  | ${FILE}
|  | Command Should Succeed | touch ${FILE}
|  | Should Exist           | ${FILE}
|  | Set Modified Time      | ${FILE}           | 2147483647
|  | ${secs}=               | Get Modified Time | ${FILE}        | epoch
|  | Should Be Equal        | ${secs}           | ${2147483647}
|  | Set Modified Time      | ${FILE}           | 2147483648
|  | ${secs}=               | Get Modified Time | ${FILE}        | epoch
|  | Should Not Be Equal    | ${secs}           | ${2147483648}
|  | Should Be Equal        | ${secs}           | ${-2147483648}
|  | [Teardown]             | Run Keywords
|  | ...                    | Remove File       | ${FILE}        | AND
|  | ...                    | Should Not Exist  | ${FILE}
|
| Write to a File
|  | [Setup]         | Run Keywords
|  | ...             | Should Not Exist | ${FILE}        | AND
|  | ...             | Create File      | ${FILE}        | Hello world!\n
|  | Should Exist    | ${FILE}
|  | ${TEXT}=        | Get File         | ${FILE}
|  | Should Be Equal | ${TEXT}          | Hello world!\n
|  | [Teardown]      | Run Keywords
|  | ...             | Remove File      | ${FILE}        | AND
|  | ...             | Should Not Exist | ${FILE}
|
| Rewrite a file
|  | [Setup]                | Run Keywords
|  | ...                    | Should Not Exist                 | ${FILE}  | AND
|  | ...                    | Create File                      | ${FILE}  | Hello world!\n
|  | Should Exist           | ${FILE}
|  | ${TEXT}=               | Get File                         | ${FILE}
|  | Command Should Succeed | echo "Hey Cleveland\n" > ${FILE}
|  | ${text2}=              | Get File                         | ${FILE}
|  | Should Not Be Equal    | ${TEXT}                          | ${text2}
|  | [Teardown]             | Run Keywords
|  | ...                    | Remove File                      | ${FILE}  | AND
|  | ...                    | Should Not Exist                 | ${FILE}
|
| Rename a File
|  | [Setup]                | Run Keywords
|  | ...                    | Should Not Exist     | ${FILE1} | AND
|  | ...                    | Should Not Exist     | ${FILE2} | AND
|  | ...                    | Create File          | ${FILE1}
|  | ${before}=             | Get Inode            | ${FILE1}
|  | Command Should Succeed | mv ${FILE1} ${FILE2}
|  | ${after}=              | Get Inode            | ${FILE2}
|  | Should Be Equal        | ${before}            | ${after}
|  | [Teardown]             | Run Keywords
|  | ...                    | Remove File          | ${FILE2} | AND
|  | ...                    | Should Not Exist     | ${FILE2}
|
| Write and Execute a Script in a Directory
|  | [Setup]                     | Run Keyword
|  | ...                         | Should Not Exist   | ${SCRIPT}
|  | ${code}=                    | Catenate
|  | ...                         | \#!/bin/sh\n
|  | ...                         | echo ${TEXT}\n
|  | Create File                 | ${SCRIPT}          | ${code}
|  | Should Exist                | ${SCRIPT}
|  | Command Should Succeed      | chmod +x ${SCRIPT}
|  | File Should Be Executable   | ${SCRIPT}
|  | ${rc}                       | ${output}=         | Run And Return Rc And Output | ${SCRIPT}
|  | Should Be Equal As Integers | ${rc}              | 0
|  | Should Match                | ${output}          | ${TEXT}
|  | [Teardown]                  | Run Keyword
|  | ...                         | Remove File        | ${SCRIPT}

*** Keywords ***
| Setup
|  | Login         | ${AFS_ADMIN} | keytab=${AFS_ADMIN_KEYTAB}
|  | Create Volume | ${VOLUME}    | server=${SERVER}           | part=${PARTITION} | path=${TESTPATH} | acl=system:anyuser,read
|
| Teardown
|  | Remove Volume | ${VOLUME} | path=${TESTPATH}
|  | Logout
