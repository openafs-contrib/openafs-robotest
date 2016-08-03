# Copyright (c) 2014-2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Basic Functional Tests, part 1
Resource          openafs.robot
Suite Setup       Setup
Suite Teardown    Teardown

*** Variables ***
${VOLUME}      test.basic
${PARTITION}   a
${SERVER}      ${HOSTNAME}
${TESTPATH}    /afs/.${AFS_CELL}/test/${VOLUME}

*** Keywords ***
Setup
    Login  ${AFS_ADMIN}
    Create Volume  ${VOLUME}  server=${SERVER}  part=${PARTITION}  path=${TESTPATH}  acl=system:anyuser,read

Teardown
    Remove Volume  ${VOLUME}  path=${TESTPATH}
    Logout

*** Test Cases ***
Create a File
    [Tags]  arla  #(creat1)
    ${file}=  Set Variable  ${TESTPATH}/file
    Should Not Exist        ${file}
    Command Should Succeed  touch ${file}
    Should Be File          ${file}
    Should Not Be Symlink   ${file}
    Remove File             ${file}
    Should Not Exist        ${file}

Create a Directory
    [Tags]  arla  #(mkdir1)
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
    [Tags]  arla  #(symlink)
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
    [Tags]  arla  #(hardlink1)
    ${file}=  Set Variable  ${TESTPATH}/file
    ${link}=  Set Variable  ${TESTPATH}/link
    Should Not Exist        ${file}
    Should Not Exist        ${link}
    Create File             ${file}
    Link Count Should Be    ${file}  1
    Command Should Succeed  ln ${file} ${link}
    Inode Should Be Equal   ${link}  ${file}
    Link Count Should Be    ${file}  2
    Link Count Should Be    ${link}  2
    Command Should Succeed  rm ${link}
    Should Not Exist        ${link}
    Link Count Should Be    ${file}  1
    Remove File             ${file}
    Should Not Exist        ${file}

Create a Hard Link within a Volume
    [Tags]  todo  arla  #(hardlink4)
    TODO  Should fail with EXDEV

Create a Hard Link to a Directory
    [Tags]  todo  arla  #(hardlink2)
    TODO

Create a Cross-Volume Hard Link
    [Tags]  todo  arla  #(hardlink5)
    TODO

Touch a file
    [Tags]  arla  #(touch1)
    ${file}=  Set Variable  ${TESTPATH}/file
    Should Not Exist        ${file}
    Command Should Succeed  touch ${file}
    Should Exist            ${file}
    Remove File             ${file}
    Should Not Exist        ${file}

Write to a File
    [Tags]  arla  #(write1)
    ${file}=  Set Variable  ${TESTPATH}/file
    Should Not Exist    ${file}
    Create File         ${file}  Hello world!\n
    Should Exist        ${file}
    ${text}=  Get File  ${file}
    Should Be Equal     ${text}  Hello world!\n
    Remove File         ${file}
    Should Not Exist    ${file}

Rewrite a file
    [Tags]  arla  #(write3)
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
    [Tags]  arla  #(rename1)
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

