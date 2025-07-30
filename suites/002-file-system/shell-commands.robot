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

Copy file with cp and check contents copied with cat
    [Documentation]    Copy file with cp and check contents copied with cat
    ...
    ...    Use cp linux command to copy a file from one directory path to another and check if file contents are
    ...    correct with cat command.
    [Tags]    shell-commands
    [Setup]    Setup Test Path

    VAR    ${FILE_COPY_PATH}    ${VOLUME_PATH}/testfs.copy.txt
    VAR    ${FILE_CONTENT}    "Hello world!\nWelcome to OpenAFS!!"

    client1.Create File    path=${FILE_PATH}    content=${FILE_CONTENT}
    client1.File Should Exist    path=${FILE_PATH}

    ${rc}    ${output}=    client1.Run And Return Rc And Output    cp ${FILE_PATH} ${FILE_COPY_PATH}
    Log Many    ${rc}    ${output}
    Should Be Equal As Integers    ${rc}    0
    client1.File Should Exist    path=${FILE_COPY_PATH}

    ${rc}    ${output}=    client1.Run And Return Rc And Output    cat ${FILE_PATH}
    Log Many    ${rc}    ${output}

    Should Be Equal    ${output}    ${FILE_CONTENT}

    [Teardown]    Teardown Test Path

Create a symbolic link using ln
    [Documentation]    Create a symbolic link using ln
    ...
    ...    Create a file, and then create a symbolic link using ln to make sure link is created successfully.
    [Tags]    link
    [Setup]    Setup Test Path

    client1.Create File    path=${FILE_PATH}    content="Hello World!"
    client1.File Should Exist    path=${FILE_PATH}

    ${rc}    ${output}=    client1.Run And Return Rc And Output
    ...    ln --symbolic ${FILE_PATH} ${VOLUME_PATH}/symlink-testfs.txt
    Log Many    ${rc}    ${output}

    client1.Should Be Symlink    ${VOLUME_PATH}/symlink-testfs.txt

    [Teardown]    Teardown Test Path

Create a hard link using ln
    [Documentation]    Create a hard link using ln
    ...
    ...    Create a file, and then create a hard link using ln. Check that the inode of the hard link is the same as the
    ...    inode of the original file.
    [Tags]    link
    [Setup]    Setup Test Path

    client1.Create File    path=${FILE_PATH}    content="Hello World!"
    client1.File Should Exist    path=${FILE_PATH}

    ${rc}    ${output}=    client1.Run And Return Rc And Output    ln ${FILE_PATH} ${VOLUME_PATH}/hardlink-testfs.txt
    Log Many    ${rc}    ${output}
    client1.Should Exist    ${VOLUME_PATH}/hardlink-testfs.txt

    ${inode_file}=    client1.Get Inode    ${FILE_PATH}
    ${inode_hardlink}=    client1.Get Inode    ${VOLUME_PATH}/hardlink-testfs.txt

    Should Be Equal As Integers    ${inode_file}    ${inode_hardlink}

    [Teardown]    Teardown Test Path

Create an archive using tar
    [Documentation]    Create an archive using tar
    ...
    ...    Create a file, and then add the file to an archive file using tar command.
    [Tags]    shell-commands
    [Setup]    Setup Test Path

    client1.Create File    path=${FILE_PATH}    content="Hello World!"
    client1.File Should Exist    path=${FILE_PATH}
    ${rc}    ${output}=    client1.Run And Return Rc And Output
    ...    tar -cvf ${VOLUME_PATH}/testfs.tar ${FILE_PATH}
    Log Many    ${rc}    ${output}
    client1.Should Exist    ${VOLUME_PATH}/testfs.tar

    ${rc}    ${output}=    client1.Run And Return Rc And Output
    ...    file ${VOLUME_PATH}/testfs.tar
    Log Many    ${rc}    ${output}
    Should Contain    ${output}    tar archive

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
