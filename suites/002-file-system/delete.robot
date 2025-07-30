*** Comments ***
Copyright (c) 2025 Sine Nomine Associates
See LICENSE


*** Settings ***
Documentation    Tests that focus on deletions of files, directories.

Variables    ../test_env_vars.py
Library    Remote    http://${CLIENT1}.${DOMAIN}:${PORT}    AS   client1
Library    Remote    http://${CLIENT2}.${DOMAIN}:${PORT}    AS   client2


*** Variables ***
${VOLUME_NAME}    test.fs
${VOLUME_PATH}    /afs/.example.com/test/fs
${FILE_PATH}    /afs/.example.com/test/fs/test-delete.txt
${DIR_PATH}    /afs/.example.com/test/fs/test-directory


*** Test Cases ***
Create and delete a file
    [Documentation]
    ...    Create and delete a file
    ...
    ...    Client1 creates an file with 'Hello World' string and client2 deletes
    ...    the file.

    [Setup]    Setup Test Path

    client1.Create File    path=${FILE_PATH}
    client1.Wait Until Created    path=${FILE_PATH}
    client1.Append To File    path=${FILE_PATH}    content=Hello World!

    client1.File Should Exist    path=${FILE_PATH}
    client1.Remove File    path=${FILE_PATH}
    client1.Wait Until Removed    path=${FILE_PATH}

    client1.Should Not Exist    path=${FILE_PATH}
    client2.Should Not Exist    path=${FILE_PATH}

    [Teardown]    Teardown Test Path

Create and delete a directory
    [Documentation]    Create and delete a directory
    ...
    ...    Client1 creates a directory and deletes it.

    [Setup]    Setup Test Path

    client1.Create Directory    path=${DIR_PATH}
    client1.Wait Until Created    path=${DIR_PATH}

    client1.Directory Should Exist    path=${DIR_PATH}
    client1.Remove Directory    path=${DIR_PATH}
    client1.Wait Until Removed    path=${DIR_PATH}

    client1.Should Not Exist    path=${DIR_PATH}
    client2.Should Not Exist    path=${DIR_PATH}

    [Teardown]    Teardown Test Path


*** Keywords ***
Setup Test Path
    [Documentation]
    ...    Setup keyword sets up a test path
    client1.Login    ${AFS_ADMIN}    keytab=${AFS_ADMIN_KEYTAB}
    client1.Volume Should Not Exist    ${VOLUME_NAME}
    client1.Create Volume    ${VOLUME_NAME}
    ...    server=server1.example.com
    ...    part=a
    ...    path=${VOLUME_PATH}
    ...    acl=system:anyuser,read,system:authuser,write
    client1.Volume Should Exist    ${VOLUME_NAME}
    client1.Logout
    client1.Login    ${AFS_USER}    keytab=${AFS_USER_KEYTAB}

Teardown Test Path
    [Documentation]
    ...     Teardown keyword removes test volume and logs out
    client1.Logout
    client1.Login    ${AFS_ADMIN}    keytab=${AFS_ADMIN_KEYTAB}
    client1.Remove Volume    ${VOLUME_NAME}
    ...    path=${VOLUME_PATH}
    ...    server=server1.example.com
    ...    part=a
    client1.Volume Should Not Exist    ${VOLUME_NAME}
    client1.Logout
