*** Settings ***
Documentation     Read-only tests
Library           OperatingSystem
Library           String
Library           OpenAFSLibrary
Suite Setup       Setup Test Suite
Suite Teardown    Teardown Test Suite

*** Variables ***
${VOLUME}      test.ro
${PARTITION}   a
${SERVER}      ${AFS_FILESERVERS}[0]
${RWPATH}      /afs/.${AFS_CELL}/test/readonly
${ROPATH}      /afs/${AFS_CELL}/test/readonly

*** Keywords ***
Setup Test Suite
    Login  ${AFS_ADMIN}  password=${AFS_ADMIN_PASSWORD}
    Create Volume   ${VOLUME}  server=${SERVER}  part=${PARTITION}  path=${RWPATH}  ro=True  acl=system:anyuser,read

Teardown Test Suite
    Remove Volume   ${VOLUME}  path=${RWPATH}
    Logout

*** Test Cases ***
Write a File in a Read-only Volume
    [Tags]    requires-multi-fs
    Run Keyword And Expect Error
    ...  *Read-only file system*
    ...  Create File  ${ROPATH}/should-be-read-only
