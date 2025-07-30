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
${FILE_PATH}    /afs/.example.com/test/fs/testfs.txt


*** Test Cases ***
Create and remove an empty file
    [Documentation]    Create And Remove An Empty File
    ...
    ...    Client1 creates an empty file and both client1 and client2 check
    ...    for its existence. Client1 removes the file and both clients check
    ...    that it does not exist anymore.

    [Tags]    distributed
    [Setup]    Setup Test Path

    client1.Create File    path=${FILE_PATH}
    client1.Wait Until Created    path=${FILE_PATH}

    client1.File Should Exist    path=${FILE_PATH}
    client2.File Should Exist    path=${FILE_PATH}

    client1.Remove File    path=${FILE_PATH}

    client1.Should Not Exist    path=${FILE_PATH}
    client2.Should Not Exist    path=${FILE_PATH}

    [Teardown]    Teardown Test Path

One client writes a file and another can read it
    [Documentation]    One client writes a file and another can read it
    ...
    ...    Client1 creates a file and writes `Hello World!` in it and client2
    ...    is able to read its contents successfully.

    [Setup]    Setup Test Path

    client1.Create File    path=${FILE_PATH}
    client1.Wait Until Created    path=${FILE_PATH}
    client1.Append To File    path=${FILE_PATH}    content=Hello World!

    client1.File Should Exist    path=${FILE_PATH}
    client2.File Should Exist    path=${FILE_PATH}

    ${rc}    ${output}=    client2.Run And Return Rc And Output    cat ${FILE_PATH}
    Log Many    ${rc}    ${output}

    Should Match Regexp    ${output}    Hello World!

    [Teardown]    Teardown Test Path

One client writes a file and unauthorized user cannot append the file
    [Documentation]    One client writes a file and unauthorized user cannot append the file
    ...
    ...    Client1 creates a file and writes `Hello World!` in it and client2
    ...    is unable to read its contents successfully because it is not logged in.

    [Setup]    Setup Test Path

    client1.Create File    path=${FILE_PATH}
    client1.Wait Until Created    path=${FILE_PATH}
    client1.Append To File    path=${FILE_PATH}    content=Hello World!

    client1.File Should Exist    path=${FILE_PATH}
    client2.File Should Exist    path=${FILE_PATH}

    ${msg}=    Run Keyword And Expect Error    PermissionError*
    ...    client2.Append To File    path=${FILE_PATH}    content=OpenAFS
    Log    ${msg}

    [Teardown]    Teardown Test Path

One client writes a file and authorized user can append the file
    [Documentation]    One client writes a file and authorized user can append the file
    ...
    ...    Client1 creates a file and writes `Hello World!` in it and client2
    ...    is able to read its contents successfully because it is logged in.

    [Setup]    Setup Test Path

    client1.Create File    path=${FILE_PATH}
    client1.Wait Until Created    path=${FILE_PATH}
    client1.Append To File    path=${FILE_PATH}    content=Hello World!

    client1.File Should Exist    path=${FILE_PATH}
    client2.File Should Exist    path=${FILE_PATH}

    client2.Login    ${AFS_USER}    keytab=${AFS_USER_KEYTAB}

    client2.Append To File    path=${FILE_PATH}    content=OpenAFS

    client2.Logout
    ${rc}    ${output}=    client1.Run And Return Rc And Output    cat ${FILE_PATH}
    Log Many    ${rc}    ${output}

    Should Match Regexp    ${output}    Hello World!
    Should Match Regexp    ${output}    OpenAFS

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
