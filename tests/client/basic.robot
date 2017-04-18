# Copyright (c) 2014-2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Basic Functional Tests
Resource          openafs.robot
Suite Setup       Setup
Suite Teardown    Teardown

*** Variables ***
${VOLUME}     test.basic
${PARTITION}  a
${SERVER}     ${HOSTNAME}
${TESTPATH}   /afs/.${AFS_CELL}/test/${VOLUME}
${EPERM}      1
${EEXIST}     17
${EXDEV}      18
${DIR2}       ${TESTPATH}/dir2
${DIR}        ${TESTPATH}/dir
${FILE1}      ${TESTPATH}/a
${FILE2}      ${TESTPATH}/b
${FILE3}      ${TESTPATH}/dir/file
${FILE}       ${TESTPATH}/file
${LINK2}      ${TESTPATH}/dir2/link
${LINK}       ${TESTPATH}/link
${NVOLUME}    ${TESTPATH}/xyzzy
${SCRIPT}     ${TESTPATH}/script.sh
${SYMLINK}    ${TESTPATH}/symlink
${TEXT}       hello-world

*** Keywords ***
Setup
    Login  ${AFS_ADMIN}
    Create Volume  ${VOLUME}  server=${SERVER}  part=${PARTITION}  path=${TESTPATH}  acl=system:anyuser,read

Teardown
    Remove Volume  ${VOLUME}  path=${TESTPATH}
    Logout

*** Test Cases ***
Create a File
    [Tags]  #(creat1)
    Should Not Exist        ${FILE}
    Command Should Succeed  touch ${FILE}
    Should Be File          ${FILE}
    Should Not Be Symlink   ${FILE}
    Remove File             ${FILE}
    Should Not Exist        ${FILE}

Create a Directory
    [Tags]  #(mkdir1)
    Should Not Exist  ${DIR}
    Create Directory  ${DIR}
    Should Exist      ${DIR}
    Should Be Dir     ${DIR}
    Should Be Dir     ${DIR}/.
    Should Be Dir     ${DIR}/..
    Remove Directory  ${DIR}
    Should Not Exist  ${DIR}

Create a Symlink
    [Tags]  #(symlink)
    Should Not Exist        ${DIR}
    Should Not Exist        ${SYMLINK}
    Create Directory        ${DIR}
    Symlink                 ${DIR}    ${SYMLINK}
    Should Be Symlink       ${SYMLINK}
    Unlink                  ${SYMLINK}
    Remove Directory        ${DIR}
    Should Not Exist        ${DIR}
    Should Not Exist        ${SYMLINK}

Create a Hard Link within a Directory
    [Tags]  #(hardlink1)
    Should Not Exist        ${FILE}
    Should Not Exist        ${LINK}
    Create File             ${FILE}
    Link Count Should Be    ${FILE}  1
    Link                    ${FILE}  ${LINK}
    Inode Should Be Equal   ${LINK}  ${FILE}
    Link Count Should Be    ${FILE}  2
    Link Count Should Be    ${LINK}  2
    Unlink                  ${LINK}
    Should Not Exist        ${LINK}
    Link Count Should Be    ${FILE}  1
    Remove File             ${FILE}
    Should Not Exist        ${FILE}

Create a Hard Link within a Volume
    [Tags]  #(hardlink4)
    Should Not Exist         ${DIR}
    Should Not Exist         ${DIR2}
    Should Not Exist         ${LINK2}
    Should Not Exist         ${FILE3}
    Create Directory         ${DIR}
    Create Directory         ${DIR2}
    Create File              ${FILE3}
    Link                     ${FILE3}  ${LINK2}  code_should_be=${EXDEV}
    Remove File              ${FILE3}
    Remove File              ${LINK2}
    Remove Directory         ${DIR}
    Remove Directory         ${DIR2}
    Should Not Exist         ${DIR}
    Should Not Exist         ${DIR2}
    Should Not Exist         ${LINK2}
    Should Not Exist         ${FILE3}

Create a Hard Link to a Directory
    [Tags]  #(hardlink2)
    Should Not Exist        ${DIR}
    Should Not Exist        ${LINK}
    Create Directory        ${DIR}
    Should Exist            ${DIR}
    Should Be Dir           ${DIR}
    Link                    ${DIR}  ${LINK}  code_should_be=${EPERM}
    Remove File             ${LINK}
    Remove Directory        ${DIR}
    Should Not Exist        ${DIR}
    Should Not Exist        ${LINK}

Create a Cross-Volume Hard Link
    [Tags]  #(hardlink5)
    Should Not Exist           ${NVOLUME}
    Create Volume  xyzzy  server=${SERVER}  part=${PARTITION}  path=${NVOLUME}  acl=system:anyuser,read
    Link  ${TESTPATH}  ${NVOLUME}  code_should_be=${EEXIST}
    Remove Volume  xyzzy  path=${NVOLUME}
    Remove File                ${NVOLUME}
    Should Not Exist           ${NVOLUME}

Touch a file
    [Tags]  #(touch1)
    Should Not Exist        ${FILE}
    Command Should Succeed  touch ${FILE}
    Should Exist            ${FILE}
    Remove File             ${FILE}
    Should Not Exist        ${FILE}

Write to a File
    [Tags]  #(write1)
    Should Not Exist    ${FILE}
    Create File         ${FILE}  Hello world!\n
    Should Exist        ${FILE}
    ${TEXT}=  Get File  ${FILE}
    Should Be Equal     ${TEXT}  Hello world!\n
    Remove File         ${FILE}
    Should Not Exist    ${FILE}

Rewrite a file
    [Tags]  #(write3)
    Should Not Exist        ${FILE}
    Create File             ${FILE}  Hello world!\n
    Should Exist            ${FILE}
    ${TEXT}=  Get File      ${FILE}
    Command Should Succeed  echo "Hey Cleveland\n" > ${FILE}
    ${text2}=  Get File     ${FILE}
    Should Not Be Equal     ${TEXT}  ${text2}
    Remove File             ${FILE}
    Should Not Exist        ${FILE}

Rename a File
    [Tags]  #(rename1)
    Should Not Exist  ${FILE1}
    Should Not Exist  ${FILE2}
    Create File  ${FILE1}
    ${before}=  Get Inode  ${FILE1}
    Command Should Succeed  mv ${FILE1} ${FILE2}
    ${after}=   Get Inode  ${FILE2}
    Should Be Equal  ${before}  ${after}
    Remove File  ${FILE2}
    Should Not Exist  ${FILE2}

Write and Execute a Script in a Directory
    [Tags]  #(exec)
    Should Not Exist        ${SCRIPT}
    ${code}=  Catenate
    ...  \#!/bin/sh\n
    ...  echo ${TEXT}\n
    Create File                  ${SCRIPT}  ${code}
    Should Exist                 ${SCRIPT}
    Command Should Succeed       chmod +x ${SCRIPT}
    File Should Be Executable    ${SCRIPT}
    ${rc}  ${output}  Run And Return Rc And Output  ${SCRIPT}
    Should Be Equal As Integers  ${rc}  0
    Should Match  ${output}  ${TEXT}

