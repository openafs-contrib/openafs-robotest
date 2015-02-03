# Copyright (c) 2015, Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation      Volume dump and restore tests
Resource           robotest.robot
Suite Setup        Login  ${AFS_ADMIN}
Suite Teardown     Logout
Test Setup         Init Crash Check
Test Teardown      Crash Check

*** Variables ***
${VOLUME}      dump.test
${PART}        a
${SERVER}      ${HOSTNAME}
${TESTPATH}    /afs/${AFS_CELL}/${VOLUME}
${DUMP}        /tmp/robotestt.dump

*** Test Cases ***
Dump Empty Volume
    Create Volume  ${SERVER}  ${PART}  ${VOLUME}
    Command Should Succeed  ${VOS} dump -id ${VOLUME} -file ${DUMP}
    Should Exist  ${DUMP}
    Should Be a Dump File  ${DUMP}
    Remove Volume  ${VOLUME}
    Remove File   ${DUMP}

Restore Volume
    Create a Test Volume
    Command Should Succeed  ${VOS} dump -id ${VOLUME} -file ${DUMP}
    Should Exist  ${DUMP}
    Should Be a Dump File  ${DUMP}
    Command Should Succeed  ${VOS} restore ${SERVER} ${PART} ${VOLUME}.restore -file ${DUMP} -overwrite full
    Remove the Test Volume
    Remove Volume  ${VOLUME}.restore
    Remove File   ${DUMP}

Restore Empty Dump
    Create Empty Dump  ${DUMP}
    Command Should Succeed  ${VOS} restore ${SERVER} ${PART} ${VOLUME} -file ${DUMP} -overwrite full
    Remove Volume  ${VOLUME}
    Remove File   ${DUMP}

Restore Bogus ACL
    [Tags]  crash
    Create Dump with Bogus ACL  ${DUMP}
    Command Should Fail  ${VOS} restore ${SERVER} ${PART} ${VOLUME} -file ${DUMP} -overwrite full
    Remove Volume  ${VOLUME}
    Remove File   ${DUMP}


*** Keywords ***
Create a Test Volume
    Create Volume  ${SERVER}  ${PART}  ${VOLUME}
    Mount Volume  ${TESTPATH}  ${VOLUME}
    Add Access Rights  ${TESTPATH}  system:anyuser  read
    Command Should Succeed  mkdir -p ${TESTPATH}/mydir
    Add Access Rights  ${TESTPATH}/mydir  system:authuser  write

Remove the Test Volume
    Remove Mount Point  ${TESTPATH}
    Remove Volume  ${VOLUME}

