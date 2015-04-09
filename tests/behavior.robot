# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     AFS behavior tests
Resource          openafs.robot
Suite Setup       Setup Test Suite
Suite Teardown    Teardown Test Suite

*** Variables ***
${VOLUME}      test.behavior
${PARTITION}   a
${SERVER}      ${HOSTNAME}
${RWPATH}      /afs/.${AFS_CELL}/test/behavior
${ROPATH}      /afs/${AFS_CELL}/test/behavior
${PARENT}      test

*** Keywords ***
Setup Test Suite
    Login              ${AFS_ADMIN}
    Create Volume      ${SERVER}  ${PARTITION}  ${VOLUME}
    Mount Volume       ${RWPATH}  ${VOLUME}
    Add Access Rights  ${RWPATH}  system:anyuser  read
    Replicate Volume   ${SERVER}  ${PARTITION}  ${VOLUME}
    Release Volume     ${PARENT}

Teardown Test Suite
    Remove Mount Point  ${RWPATH}
    Remove Replica      ${SERVER}  ${PARTITION}  ${VOLUME}
    Remove Volume       ${VOLUME}
    Logout

*** Test Cases ***
Write a File in a Read-only Volume
    [Tags]  arla  #(write-ro)
    Run Keyword And Expect Error
    ...  IOError: [Errno 30] Read-only file system:*
    ...  Create File  ${ROPATH}/should-be-read-only

Create a Large Number of Entries in a Directory
    [Tags]  slow  arla  #(too-many-files)
    Create Files  ${RWPATH}  31707  0

Test setpag
    [Tags]  todo  arla  #(setpag)
    TODO

Test setgroups
    [Tags]  todo  arla  #(setgroups)
    TODO

