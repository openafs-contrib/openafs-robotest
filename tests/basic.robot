# Copyright (c) 2014, Sine Nomine Associates
# See LICENSE

*** Settings ***
Resource          robotest.robot
Suite Setup       Create a Test Volume
Suite Teardown    Remove the Test Volume


*** Variables ***
${VOLUME}      basic
${PARTITION}   a
${SERVER}      ${HOSTNAME}
${TESTPATH}    /afs/${AFS_CELL}/${VOLUME}

*** Test Cases ***
Touch
    ${file}=  Set Variable  ${TESTPATH}/file
    Should Not Exist       ${file}
    Run Command            touch ${file}
    Should Be File         ${file}
    Should Not Be Symlink  ${file}
    Remove File            ${file}
    Should Not Exist       ${file}

Write
    ${file}=  Set Variable  ${TESTPATH}/file
    Should Not Exist    ${file}
    Create File         ${file}  Hello world!\n
    Should Exist        ${file}
    ${text}=  Get File  ${file}
    Should Be Equal     ${text}  Hello world!\n
    Remove File         ${file}
    Should Not Exist    ${file}

Make Directory
    ${dir}=  Set Variable  ${TESTPATH}/dir
    Should Not Exist  ${dir}
    Create Directory  ${dir}
    Should Exist      ${dir}
    Should Be Dir     ${dir}
    Should Be Dir     ${dir}/.
    Should Be Dir     ${dir}/..
    Remove Directory  ${dir}
    Should Not Exist  ${dir}

Symlink
    ${dir}=      Set Variable  ${TESTPATH}/dir
    ${symlink}=  Set Variable  ${TESTPATH}/symlink
    Should Not Exist   ${dir}
    Should Not Exist   ${symlink}
    Create Directory   ${dir}
    Run Command        ln -s ${dir} ${symlink}
    Should Be Symlink  ${symlink}
    Run Command        rm ${symlink}
    Remove Directory   ${dir}
    Should Not Exist   ${dir}
    Should Not Exist   ${symlink}

Hard Link
    ${file}=  Set Variable  ${TESTPATH}/file
    ${link}=  Set Variable  ${TESTPATH}/link
    Should Not Exist       ${file}
    Should Not Exist       ${link}
    Create File            ${file}
    Link Count Should Be   ${file}  1
    Run Command            ln ${file} ${link}
    Inode Should Be Equal  ${link}  ${file}
    Link Count Should Be   ${file}  2
    Link Count Should Be   ${link}  2
    Run Command            rm ${link}
    Should Not Exist       ${link}
    Link Count Should Be   ${file}  1
    Remove File            ${file}
    Should Not Exist       ${file}

Rename
    ${a}=  Set Variable  ${TESTPATH}/a
    ${b}=  Set Variable  ${TESTPATH}/b
    Should Not Exist  ${a}
    Should Not Exist  ${b}
    Create File  ${a}
    ${inode}=  Evaluate  os.stat("${a}").st_ino  os
    Run Command  mv ${a} ${b}
    Should Be True  os.stat("${b}").st_ino == ${inode}
    Remove File  ${b}
    Should Not Exist  ${b}


*** Keywords ***
Create a Test Volume
    Login  ${AFS_ADMIN}
    Create Volume  ${SERVER}  ${PARTITION}  ${VOLUME}
    Mount Volume  ${TESTPATH}  ${VOLUME}
    Add Access Rights  ${TESTPATH}  system:anyuser  read

Remove the Test Volume
    Remove Mount Point  ${TESTPATH}
    Remove Volume  ${VOLUME}
    Logout

