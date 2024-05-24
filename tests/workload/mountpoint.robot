*** Comments ***
# Copyright (c) 2015 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation       Mountpoint tests

Library             OperatingSystem
Library             String
Library             OpenAFSLibrary

Suite Setup         Setup
Suite Teardown      Teardown

*** Variables ***
${MTPT}         /afs/.${AFS_CELL}/test/mtpt
${MTPT2}        /afs/.${AFS_CELL}/mtpt2
${MTPT3}        /afs/.${AFS_CELL}/mtpt3
${MTPT4}        /afs/.${AFS_CELL}/mtpt4
${VOLUME}       test.mtpt
${VOLUME2}      test2.mtpt
${PARTITION}    a
${SERVER}       ${AFS_FILESERVER_A}
${TESTPATH}     /afs/.${AFS_CELL}/test/${VOLUME}
${TESTPATH2}    /afs/.${AFS_CELL}/${VOLUME2}

*** Test Cases ***
| Make and Remove a Mountpoint
|  | [Setup]                | Run Keyword
|  | ...                    | Command Should Succeed     | ${FS} mkmount -dir ${MTPT} -vol ${VOLUME}
|  | Directory Should Exist | ${MTPT}
|  | [Teardown]             | Run Keywords
|  | ...                    | Command Should Succeed     | ${FS} rmmount -dir ${MTPT}                | AND
|  | ...                    | Directory Should Not Exist | ${MTPT}
|
| Make and Remove a Mountpoint with Command Aliases
|  | [Setup]                | Run Keyword
|  | ...                    | Command Should Succeed     | ${FS} mkm ${MTPT} root.cell
|  | Directory Should Exist | ${MTPT}
|  | [Teardown]             | Run Keywords
|  | ...                    | Command Should Succeed     | ${FS} rmm ${MTPT}           | AND
|  | ...                    | Directory Should Not Exist | ${MTPT}
|
| Create a Mountpoint to a Nonexistent Volume
|  | [Documentation]              | The fs command permits the creation of dangling mountpoints.
|  | ...                          | A directory entry is created, but the directory is not usable.
|  | [Setup]                      | Run Keyword
|  | ...                          | Command Should Succeed                                         | ${FS} mkm ${MTPT} no-such-volume
|  | Directory Entry Should Exist | ${MTPT}
|  | Command Should Fail          | test -d ${MTPT}
|  | Command Should Fail          | touch ${MTPT}/foo
|  | [Teardown]                   | Run Keyword
|  | ...                          | Command Should Succeed                                         | ${FS} rmm ${MTPT}
|
| Make and Remove a Mountpoint in root.cell volume
|  | [Tags]                 | bug-1.6.x
|  | [Documentation]        | Creating/removing a mountpoint in a root directory.
|  | ...                    | In releases prior to 1.8.x of AFS there was a bug in the
|  | ...                    | cachemanager when removing a mountpoint that is in the root of a volume.
|  | [Setup]                | Run Keyword
|  | ...                    | Command Should Succeed                                                   | ${FS} mkmount -dir ${MTPT2} -vol ${VOLUME2}
|  | Directory Should Exist | ${MTPT2}
|  | [Teardown]             | Run Keywords
|  | ...                    | Command Should Succeed                                                   | ${FS} rmmount -dir ${MTPT2}                 | AND
|  | ...                    | Directory Should Not Exist                                               | ${MTPT2}
|
| Create a Mountpoint to a Nonexistent Volume in root.cell volume
|  | [Documentation]              | The fs command permits the creation of dangling mountpoints.
|  | ...                          | A directory entry is created, but the directory is not usable.
|  | ...                          | Repeating this test in root.cell volume as well.
|  | [Setup]                      | Run Keyword
|  | ...                          | Command Should Succeed                                         | ${FS} mkmount -dir ${MTPT4} -vol no-such-volume
|  | Directory Entry Should Exist | ${MTPT4}
|  | Command Should Fail          | test -d ${MTPT4}
|  | Command Should Fail          | touch ${MTPT4}/foo
|  | [Teardown]                   | Run Keywords
|  | ...                          | Command Should Succeed                                         | ${FS} rmmount -dir ${MTPT4}                     | AND
|  | ...                          | Directory Should Not Exist                                     | ${MTPT4}

*** Keywords ***
| Setup
|  | Login                        | ${AFS_ADMIN}                                    | keytab=${AFS_ADMIN_KEYTAB}
|  | Command Should Succeed       | ${VOS} create ${SERVER} ${PARTITION} ${VOLUME}
|  | Command Should Succeed       | ${VOS} create ${SERVER} ${PARTITION} ${VOLUME2}
|  | Add Access Rights            | /afs/.${AFS_CELL}                               | system:authuser            | rlidwk
|  | Access Control List Contains | /afs/.${AFS_CELL}                               | system:authuser            | rlidwk
|
| Teardown
|  | Remove Volume | ${VOLUME}
|  | Remove Volume | ${VOLUME2}
|  | Logout
