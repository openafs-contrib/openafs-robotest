# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Client stess tests
Library           OperatingSystem
Library           String
Library           OpenAFSLibrary

*** Variables ***
${VOLUME}      test.stress
${PARTITION}   a
${SERVER}      @{AFS_FILESERVERS}[0]
${RWPATH}      /afs/.${AFS_CELL}/test/stress

*** Keywords ***
Create Stress Test Volume
    Login  ${AFS_ADMIN}  password=${AFS_ADMIN_LOGIN}
    Create Volume   ${VOLUME}  server=${SERVER}  part=${PARTITION}  path=${RWPATH}  ro=True  acl=system:anyuser,read

Remove Stress Test Volume
    Remove Volume   ${VOLUME}  path=${RWPATH}
    Logout

*** Test Cases ***
Create a Large Number of Entries in a Directory
    [Tags]  slow
    [Setup]       Create Stress Test Volume
    [Teardown]    Remove Stress Test Volume
    Create Files  ${RWPATH}  31707  0
