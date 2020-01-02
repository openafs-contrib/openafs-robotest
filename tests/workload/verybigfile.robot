# Copyright (c) 2020 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation     Regression
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
${FILE}        ${TESTPATH}/file

*** Keywords ***
Setup
    Login  ${AFS_ADMIN}  password=${AFS_ADMIN_PASSWORD}
    Create Volume  ${VOLUME}  server=${SERVER}  part=${PARTITION}  path=${TESTPATH}  acl=system:anyuser,read

Teardown
    Remove Volume  ${VOLUME}  path=${TESTPATH}
    Logout

*** Test Cases ***
Read Write a File Larger than 4G
    [Tags]  slow
    [Setup]  Run Keywords
    Command Should Succeed  dd if=/dev/urandom of=${FILE} bs=1024 count=5M
    Command Should Succeed  dd if=${FILE} of=/dev/null
    [Teardown]  Run Keywords
    ...    Remove File                    ${FILE}  AND
    ...    Should Not Exist               ${FILE}
