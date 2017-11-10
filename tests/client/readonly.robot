*** Settings ***
Documentation     Read-only tests
Resource          openafs.robot
Suite Setup       Setup Test Suite
Suite Teardown    Teardown Test Suite

*** Variables ***
${VOLUME}      test.ro
${PARTITION}   a
${SERVER}      ${FILESERVER}
${RWPATH}      /afs/.${AFS_CELL}/test/readonly
${ROPATH}      /afs/${AFS_CELL}/test/readonly

*** Keywords ***
Setup Test Suite
    Login           ${AFS_ADMIN}
    Create Volume   ${VOLUME}  server=${SERVER}  part=${PARTITION}  path=${RWPATH}  ro=True  acl=system:anyuser,read

Teardown Test Suite
    Remove Volume   ${VOLUME}  path=${RWPATH}
    Logout

*** Test Cases ***
Write a File in a Read-only Volume
    [Tags]  #(write-ro)
    Run Keyword And Expect Error
    ...  *Read-only file system*
    ...  Create File  ${ROPATH}/should-be-read-only

