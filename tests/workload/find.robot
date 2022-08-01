*** Settings ***
Documentation       File Hierarchy Traversal Tests

Library             OperatingSystem
Library             String
Library             OpenAFSLibrary

Suite Setup         Login    ${AFS_ADMIN}    keytab=${AFS_ADMIN_KEYTAB}
Suite Teardown      Logout

*** Variables ***
${VOLUME}       test.find
${PARTITION}    a
${SERVER}       ${AFS_FILESERVER_A}
${TESTPATH}     /afs/.${AFS_CELL}/test/${VOLUME}

*** Test Cases ***
| Traverse Simple Tree
|  | [Tags]               | requires-gfind
|  | [Setup]              | Create Tree
|  | File Should Be Found | ${TESTPATH}/v0/v3/file1
|  | File Should Be Found | ${TESTPATH}/v2/file2
|  | [Teardown]           | Remove Tree
|
| Traverse Tree with Two Parents
|  | [Tags]               | bug                          | requires-gfind
|  | [Setup]              | Create Tree With Two Parents
|  | File Should Be Found | ${TESTPATH}/v0/v3/file1
|  | File Should Be Found | ${TESTPATH}/v1/v3a/file1
|  | File Should Be Found | ${TESTPATH}/v2/file2
|  | [Teardown]           | Remove Tree

*** Keywords ***
| Create Tree
|  | [Documentation] | Create a simple file tree hierarchy.
|  | ...             |
|  | Create Volume   | ${VOLUME}                            | server=${SERVER} | part=${PARTITION} | path=${TESTPATH}
|  | Create Volume   | ${VOLUME}.0                          | server=${SERVER} | part=${PARTITION} | path=${TESTPATH}/v0
|  | Create Volume   | ${VOLUME}.1                          | server=${SERVER} | part=${PARTITION} | path=${TESTPATH}/v1
|  | Create Volume   | ${VOLUME}.2                          | server=${SERVER} | part=${PARTITION} | path=${TESTPATH}/v2
|  | Create Volume   | ${VOLUME}.3                          | server=${SERVER} | part=${PARTITION} | path=${TESTPATH}/v0/v3
|  | Create File     | ${TESTPATH}/v0/v3/file1              | hello world\n
|  | Create File     | ${TESTPATH}/v2/file2                 | greetings\n
|
| Create Tree With Two Parents
|  | [Documentation]        | Add a second mount point to volume 3 so it
|  | ...                    | will have two parents in the hierarchy.
|  | Create Tree
|  | Command Should Succeed | ${FS} mkm -dir ${TESTPATH}/v1/v3a -vol ${VOLUME}.3
|
| Remove Tree
|  | Remove File   | ${TESTPATH}/v2/file2
|  | Remove File   | ${TESTPATH}/v0/v3/file1
|  | Remove Volume | ${VOLUME}.3             | path=${TESTPATH}/v0/v3
|  | Remove Volume | ${VOLUME}.2             | path=${TESTPATH}/v2
|  | Remove Volume | ${VOLUME}.1             | path=${TESTPATH}/v1
|  | Remove Volume | ${VOLUME}.0             | path=${TESTPATH}/v0
|  | Remove Volume | ${VOLUME}               | path=${TESTPATH}
|
| File Should Be Found
|  | [Arguments]                 | ${target}
|  | ${rc}                       | ${output} | Run And Return Rc And Output | ${GFIND} ${TESTPATH} -noleaf
|  | Log                         | ${output}
|  | Should Be Equal As Integers | ${rc}     | 0
|  | Should Contain              | ${output} | ${target}
