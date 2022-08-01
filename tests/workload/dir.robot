*** Comments ***
# Copyright (c) 2015 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation       Directory Object tests

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
${NAME}         \u20ac\u2020\u2021
${FILE}         ${TESTPATH}/${NAME}

*** Test Cases ***
| Unicode File Name
|  | [Setup]      | Run Keyword
|  | ...          | Should Not Exist | ${FILE}
|  | Create File  | ${FILE}          | Hello world! | UTF-8
|  | Should Exist | ${FILE}
|  | [Teardown]   | Run Keywords
|  | ...          | Remove File      | ${FILE}      | AND
|  | ...          | Should Not Exist | ${FILE}

*** Keywords ***
| Setup
|  | Login         | ${AFS_ADMIN} | keytab=${AFS_ADMIN_KEYTAB}
|  | Create Volume | ${VOLUME}    | server=${SERVER}           | part=${PARTITION} | path=${TESTPATH} | acl=system:anyuser,read
|
| Teardown
|  | Remove Volume | ${VOLUME} | path=${TESTPATH}
|  | Logout
