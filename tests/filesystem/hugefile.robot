*** Comments ***
# Copyright (c) 2015, 2020 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation       Regression

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
${FILE}         ${TESTPATH}/file

*** Test Cases ***
| Create a Larger Than 2gb File
|  | [Tags]       | slow
|  | [Setup]      | Run Keyword
|  | ...          | Create File      | ${FILE}
|  | Should Exist | ${FILE}
|  | ${output}=   | Run              | dd if=/dev/zero of=${FILE} bs=1024 count=2M
|  | [Teardown]   | Run Keywords
|  | ...          | Remove File      | ${FILE}                                     | AND
|  | ...          | Should Not Exist | ${FILE}
|
| Write a File Larger than the Cache
|  | [Tags]       | slow
|  | [Setup]      | Run Keywords
|  | ...          | Should Not Exist | ${FILE}                                            | AND
|  | ...          | Create File      | ${FILE}
|  | ${size}=     | Get Cache Size
|  | Should Exist | ${FILE}
|  | ${output}=   | Run              | dd if=/dev/zero of=${FILE} bs=1024 count=${size+1}
|  | [Teardown]   | Run Keywords
|  | ...          | Remove File      | ${FILE}                                            | AND
|  | ...          | Should Not Exist | ${FILE}
|
| Read a File Larger than the Cache
|  | [Tags]             | slow
|  | [Setup]            | Run Keywords
|  | ...                | Should Not Exist | ${FILE}                                            | AND
|  | ...                | Create File      | ${FILE}
|  | ${size}=           | Get Cache Size
|  | Should Exist       | ${FILE}
|  | ${output}=         | Run              | dd if=/dev/zero of=${FILE} bs=1024 count=${size+1}
|  | Should Not Contain | ${FILE}          | 0
|  | [Teardown]         | Run Keywords
|  | ...                | Remove File      | ${FILE}                                            | AND
|  | ...                | Should Not Exist | ${FILE}
|
| Read Write a File Larger than 4G
|  | [Tags]                 | slow
|  | [Setup]                | Run Keywords
|  | Command Should Succeed | dd if=/dev/urandom of=${FILE} bs=1024 count=5M
|  | Command Should Succeed | dd if=${FILE} of=/dev/null
|  | [Teardown]             | Run Keywords
|  | ...                    | Remove File                                    | ${FILE} | AND
|  | ...                    | Should Not Exist                               | ${FILE}

*** Keywords ***
| Setup
|  | Login         | ${AFS_ADMIN} | keytab=${AFS_ADMIN_KEYTAB}
|  | Create Volume | ${VOLUME}    | server=${SERVER}           | part=${PARTITION} | path=${TESTPATH} | acl=system:anyuser,read
|
| Teardown
|  | Remove Volume | ${VOLUME} | path=${TESTPATH}
|  | Logout
