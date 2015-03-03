# Copyright (c) 2014, Sine Nomine Associates
# See LICENSE

*** Settings ***
Resource          openafs.robot
Suite Setup       Setup
Suite Teardown    Teardown

*** Variables ***
${VOLUME}      test.basic
${PARTITION}   a
${SERVER}      ${HOSTNAME}
${TESTPATH}    /afs/${AFS_CELL}/test/${VOLUME}

*** Keywords ***
Setup
    Login  ${AFS_ADMIN}
    Create and Mount Volume  ${SERVER}  ${PARTITION}  ${VOLUME}  ${TESTPATH}

Teardown
    Remove Mount Point  ${TESTPATH}
    Remove Volume  ${VOLUME}
    Logout

*** Test Cases ***
Create a File
    ${file}=  Set Variable  ${TESTPATH}/file
    Should Not Exist        ${file}
    Command Should Succeed  touch ${file}
    Should Be File          ${file}
    Should Not Be Symlink   ${file}
    Remove File             ${file}
    Should Not Exist        ${file}

Create a Directory
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

# Create a Hard Link within a Volume
# TODO: Should fail with EXDEV

# Create a Hard Link to a Directory
# TODO

# Create a Cross-Volume Hard Link
# TODO

# Touch a file (touch1)

Write to a File
    ${file}=  Set Variable  ${TESTPATH}/file
    Should Not Exist    ${file}
    Create File         ${file}  Hello world!\n
    Should Exist        ${file}
    ${text}=  Get File  ${file}
    Should Be Equal     ${text}  Hello world!\n
    Remove File         ${file}
    Should Not Exist    ${file}

# Rewrite a file (write3)

Rename a File
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

# TODO
# 10) Stat multiple hardlinked files. (hardlink3)
# 20) Write, truncate, rewrite a file. (write2)
# 30) Append to a file. (append1)
# 40) Rename a file over another file. (rename2)
# 50) Rename a file into a same-volume directory. (rename4)
# 60) Rename a file into another-volume directory. (rename6)
# 70) Rename an open directory. (rename-under-feet)
# 80) Create a file with a large filename. (large-filename)
# 90) Chmod a file by descriptor. (fchmod)
# 100) Utimes a file. (utime-file)
# 110) Utimes a directory. (utime-dir)
# 120) Test directory "link count" increasing/decreasing appropriately. (mkdir3)


