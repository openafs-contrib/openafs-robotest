# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Regression
Resource          openafs.robot
Suite Setup       Setup
Suite Teardown    Teardown

*** Variables ***
${VOLUME}      test.basic
${PARTITION}   a
${SERVER}      ${HOSTNAME}
${TESTPATH}    /afs/.${AFS_CELL}/test/${VOLUME}
${FILE}        ${TESTPATH}/file

*** Keywords ***
Setup
    Login  ${AFS_ADMIN}
    Create Volume  ${VOLUME}  server=${SERVER}  part=${PARTITION}  path=${TESTPATH}  acl=system:anyuser,read

Teardown
    Remove Volume  ${VOLUME}  path=${TESTPATH}
    Logout

*** Test Cases ***
Create a Larger Than 2gb File
    [Tags]  slow
    [Setup]  Run Keyword
    ...    Create File                    ${FILE}
    Should Exist                   ${FILE}
    ${output}=  Run                dd if=/dev/zero of=${FILE} bs=1024 count=2M
    [Teardown]  Run Keywords
    ...    Remove File                    ${FILE}  AND
    ...    Should Not Exist               ${FILE}

Write a File Larger than the Cache
    [Tags]  slow
    [Setup]  Run Keywords
    ...    ${size}=  Get Cache Size   AND
    ...    Should Not Exist               ${FILE}  AND
    ...    Create File                    ${FILE}
    Should Exist                   ${FILE}
    ${output}=  Run                dd if=/dev/zero of=${FILE} bs=1024 count=${size+1}
    [Teardown]  Run Keywords
    ...    Remove File                    ${FILE}  AND
    ...    Should Not Exist               ${FILE}

Read a File Larger than the Cache
    [Tags]  slow
    [Setup]  Run Keywords
    ...    ${size}=  Get Cache Size   AND
    ...    Should Not Exist               ${FILE}  AND
    ...    Create File                    ${FILE}
    Should Exist                   ${FILE}
    ${output}=  Run                dd if=/dev/zero of=${FILE} bs=1024 count=${size+1}
    Should Not Contain             ${FILE}  0
    [Teardown]  Run Keywords
    ...    Remove File                    ${FILE}  AND
    ...    Should Not Exist               ${FILE}
