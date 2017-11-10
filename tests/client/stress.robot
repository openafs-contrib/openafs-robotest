# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Client stess tests
Resource          openafs.robot

*** Variables ***
${VOLUME}      test.stress
${PARTITION}   a
${SERVER}      ${FILESERVER}
${RWPATH}      /afs/.${AFS_CELL}/test/stress

*** Keywords ***
Create Stress Test Volume
    Login           ${AFS_ADMIN}
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

Write a File, Read, Rewrite and Reread a File with the Same Open Descriptor
    [Tags]  todo  #(read-write)
    TODO

Populate and Clean up a Directory Tree
    [Tags]  todo  #(create-remove-files)
    TODO

FSX File System Stresser
    [Tags]  todo  #(fsx)
    TODO

Create and Remove a Single File in Parallel
    [Tags]  todo  #(parallel1)
    TODO

