# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Directory Object tests
Library           OperatingSystem
Library           String
Library           OpenAFSLibrary
Suite Setup       Setup
Suite Teardown    Teardown

*** Variables ***
${VOLUME}      test.basic
${PARTITION}   a
${SERVER}      @{AFS_FILESERVERS}[0]
${TESTPATH}    /afs/.${AFS_CELL}/test/${VOLUME}
${NAME}        \u20ac\u2020\u2021
${FILE}        ${TESTPATH}/${NAME}

*** Keywords ***
Setup
    Login  ${AFS_ADMIN}
    Create Volume  ${VOLUME}  server=${SERVER}  part=${PARTITION}  path=${TESTPATH}  acl=system:anyuser,read

Teardown
    Remove Volume  ${VOLUME}  path=${TESTPATH}
    Logout

*** Test Cases ***
Unicode File Name
    [Setup]  Run Keyword
    ...    Should Not Exist    ${FILE}
    [Teardown]  Run Keywords
    ...    Remove File         ${FILE}  AND
    ...    Should Not Exist    ${FILE}
    Create File                ${FILE}    Hello world!   UTF-8
    Should Exist               ${FILE}

