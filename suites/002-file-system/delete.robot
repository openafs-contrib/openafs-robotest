*** Comments ***
Copyright (c) 2025 Sine Nomine Associates
See LICENSE


*** Settings ***
Documentation    Read and write files

Variables    ../test_env_vars.py
Library    Remote    http://${CLIENT1}.${DOMAIN}:${PORT}    AS   client1
Library    Remote    http://${CLIENT2}.${DOMAIN}:${PORT}    AS   client2


*** Variables ***
${VOLUME_NAME}    test.fs
${VOLUME_PATH}    /afs/.example.com/test/fs
${FILE_PATH}    /afs/.example.com/test/fs/test-delete.txt


*** Test Cases ***
Create And Delete A File
    [Documentation]
    ...    Create And Delete A File
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
