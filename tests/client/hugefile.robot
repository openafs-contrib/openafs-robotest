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

*** Keywords ***
Setup
    Login  ${AFS_ADMIN}
    Create Volume  ${VOLUME}  server=${SERVER}  part=${PARTITION}  path=${TESTPATH}  acl=system:anyuser,read

Teardown
    Remove Volume  ${VOLUME}  path=${TESTPATH}
    Logout

*** Test Cases ***
Create a Larger Than 2gb File
    [Tags]  #(write-large)
    ${file}=  Set Variable         ${TESTPATH}/file
    Create File                    ${file}
    Should Exist                   ${file}
    ${output}=  Run                dd if=/dev/zero of=${file} bs=1024 count=2M
    Remove File                    ${file}
    Should Not Exist               ${file}

Write a File Larger than the Cache
    [Tags]  todo  #(fcachesize-write-file)
    TODO

Read a File Larger than the Cache
    [Tags]  todo  #(fcachesize-read-file)
    TODO

