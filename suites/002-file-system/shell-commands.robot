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
${FILE_PATH}    ${VOLUME_PATH}/testfs.txt


*** Test Cases ***
List directory with ls
    [Documentation]    List directory with ls
    ...
    ...    List directory contents using the ls command line utility.

    [Tags]    shell-commands
    [Setup]    Setup Test Path

    client1.Create File    path=${FILE_PATH}
    ${rc}    ${output}=    client1.Run And Return Rc And Output    ls ${FILE_PATH}
    Log Many    ${rc}    ${output}
    Should Contain    ${output}    testfs.txt

    [Teardown]    Teardown Test Path

Change directory with cd
    [Documentation]    Change directory with cd
    ...
    ...    Change to directory using the cd command line utility.

    [Tags]    shell-commands
    [Setup]    Setup Test Path

    client1.Create File    path=${FILE_PATH}
    ${rc}    ${output}=    client1.Run And Return Rc And Output    cd ${VOLUME_PATH}
    Log Many    ${rc}    ${output}
    Should Be Equal As Integers    ${rc}    0

    [Teardown]    Teardown Test Path

Make and remove a new directory with mkdir and rmdir
    [Documentation]    Make and remove a new directory with mkdir and rmdir
    ...
    ...    Use mkdir linux command to create a new directory within a volume.
    ...    Then, use rmdir linux command to delete the newly added directory.

    [Tags]    shell-commands
    [Setup]    Setup Test Path

    VAR    ${DIRECTORY}    test_dir
    ${rc}    ${output}=    client1.Run And Return Rc And Output    mkdir ${VOLUME_PATH}/${DIRECTORY}
    Log Many    ${rc}    ${output}
    Should Be Equal As Integers    ${rc}    0
    client1.Directory Should Exist    ${VOLUME_PATH}/${DIRECTORY}

    ${rc}    ${output}=    client1.Run And Return Rc And Output    rmdir ${VOLUME_PATH}/${DIRECTORY}
    Log Many    ${rc}    ${output}
    Should Be Equal As Integers    ${rc}    0
    client1.Directory Should Not Exist    ${VOLUME_PATH}/${DIRECTORY}

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
