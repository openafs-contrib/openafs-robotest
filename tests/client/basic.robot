# Copyright (c) 2014-2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Basic Functional Tests
Resource          openafs.robot
Suite Setup       Setup
Suite Teardown    Teardown

*** Variables ***
${VOLUME}      test.basic
${PARTITION}   a
${SERVER}      ${HOSTNAME}
${TESTPATH}    /afs/.${AFS_CELL}/test/${VOLUME}
${EPERM}       1
${EEXIST}      17
${EXDEV}       18

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
    ${file}=  Set Variable  ${TESTPATH}/file
    Should Not Exist        ${file}
    Command Should Succeed  touch ${file}
    Should Be File          ${file}
    Should Not Be Symlink   ${file}
    Remove File             ${file}
    Should Not Exist        ${file}

Create a Directory
    [Tags]  #(mkdir1)
    ${dir}=  Set Variable  ${TESTPATH}/dir
    Should Not Exist  ${dir}
    Create Directory  ${dir}
    Should Exist      ${dir}
    Should Be Dir     ${dir}
    Should Be Dir     ${dir}/.
    Should Be Dir     ${dir}/..
    Remove Directory  ${dir}
    Should Not Exist  ${dir}

Create a Symlink
    [Tags]  #(symlink)
    ${dir}=      Set Variable  ${TESTPATH}/dir
    ${symlink}=  Set Variable  ${TESTPATH}/symlink
    Should Not Exist        ${dir}
    Should Not Exist        ${symlink}
    Create Directory        ${dir}
    Command Should Succeed  ln -s ${dir} ${symlink}
    Should Be Symlink       ${symlink}
    Command Should Succeed  rm ${symlink}
    Remove Directory        ${dir}
    Should Not Exist        ${dir}
    Should Not Exist        ${symlink}

Create a Hard Link within a Directory
    [Tags]  #(hardlink1)
    ${file}=  Set Variable  ${TESTPATH}/file
    ${link}=  Set Variable  ${TESTPATH}/link
    Should Not Exist        ${file}
    Should Not Exist        ${link}
    Create File             ${file}
    Link Count Should Be    ${file}  1
    Link                    ${file}  ${link}
    Inode Should Be Equal   ${link}  ${file}
    Link Count Should Be    ${file}  2
    Link Count Should Be    ${link}  2
    Command Should Succeed  rm ${link}
    Should Not Exist        ${link}
    Link Count Should Be    ${file}  1
    Remove File             ${file}
    Should Not Exist        ${file}

Create a Hard Link within a Volume
    [Tags]  #(hardlink4)
    ${dir}=    Set Variable  ${TESTPATH}/dir
    ${dir2}=   Set Variable  ${TESTPATH}/dir2
    ${file}=   Set Variable  ${dir}/file
    ${link}=   Set Variable  ${dir2}/link
    Should Not Exist         ${dir}
    Should Not Exist         ${dir2}
    Should Not Exist         ${link}
    Should Not Exist         ${file}
    Create Directory         ${dir}
    Create Directory         ${dir2}
    Create File              ${file}
    Link                     ${file}  ${link}  code_should_be=${EXDEV}
    Remove File              ${file}
    Remove File              ${link}
    Remove Directory         ${dir}
    Remove Directory         ${dir2}
    Should Not Exist         ${dir}
    Should Not Exist         ${dir2}
    Should Not Exist         ${link}
    Should Not Exist         ${file}

Create a Hard Link to a Directory
    [Tags]  #(hardlink2)
    ${dir}=  Set Variable   ${TESTPATH}/dir
    ${link}=  Set Variable  ${TESTPATH}/link
    Should Not Exist        ${dir}
    Should Not Exist        ${link}
    Create Directory        ${dir}
    Should Exist            ${dir}
    Should Be Dir           ${dir}
    Link                    ${dir}  ${link}  code_should_be=${EPERM}
    Remove File             ${link}
    Remove Directory        ${dir}
    Should Not Exist        ${dir}
    Should Not Exist        ${link}

Create a Cross-Volume Hard Link
    [Tags]  #(hardlink5)
    ${nvolume}=  Set Variable  ${TESTPATH}/xyzzy
    Should Not Exist           ${nvolume}
    Create Volume  xyzzy  server=${SERVER}  part=${PARTITION}  path=${nvolume}  acl=system:anyuser,read
    Link  ${TESTPATH}  ${nvolume}  code_should_be=${EEXIST}
    Remove Volume  xyzzy  path=${nvolume}
    Remove File                ${nvolume}
    Should Not Exist           ${nvolume}

Touch a file
    [Tags]  #(touch1)
    ${file}=  Set Variable  ${TESTPATH}/file
    Should Not Exist        ${file}
    Command Should Succeed  touch ${file}
    Should Exist            ${file}
    Remove File             ${file}
    Should Not Exist        ${file}

Write to a File
    [Tags]  #(write1)
    ${file}=  Set Variable  ${TESTPATH}/file
    Should Not Exist    ${file}
    Create File         ${file}  Hello world!\n
    Should Exist        ${file}
    ${text}=  Get File  ${file}
    Should Be Equal     ${text}  Hello world!\n
    Remove File         ${file}
    Should Not Exist    ${file}

Rewrite a file
    [Tags]  #(write3)
    ${file}=  Set Variable  ${TESTPATH}/file
    Should Not Exist        ${file}
    Create File             ${file}  Hello world!\n
    Should Exist            ${file}
    ${text}=  Get File      ${file}
    Command Should Succeed  echo "Hey Cleveland\n" > ${file}
    ${text2}=  Get File     ${file}
    Should Not Be Equal     ${text}  ${text2}
    Remove File             ${file}
    Should Not Exist        ${file}

Rename a File
    [Tags]  #(rename1)
    ${a}=  Set Variable  ${TESTPATH}/a
    ${b}=  Set Variable  ${TESTPATH}/b
    Should Not Exist  ${a}
    Should Not Exist  ${b}
    Create File  ${a}
    ${before}=  Get Inode  ${a}
    Command Should Succeed  mv ${a} ${b}
    ${after}=   Get Inode  ${b}
    Should Be Equal  ${before}  ${after}
    Remove File  ${b}
    Should Not Exist  ${b}

Write and Execute a Script in a Directory
    [Tags]  #(exec)
    ${file}=  Set Variable  ${TESTPATH}/script.sh
    ${text}=  Set Variable  hello world
    #Should Not Exist        ${file}
    ${code}=  Catenate
    ...  \#!/bin/sh\n
    ...  echo ${text}\n
    Create File                  ${file}  ${code}
    Should Exist                 ${file}
    Command Should Succeed       chmod +x ${file}
    File Should Be Executable    ${file}
    ${rc}  ${output}  Run And Return Rc And Output  ${file}
    Should Be Equal As Integers  ${rc}  0
    Should Match  ${output}  ${text}

