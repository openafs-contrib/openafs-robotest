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
${PARTITION}   a
${SERVER}      ${HOSTNAME}
${TESTPATH}    /afs/${AFS_CELL}/${VOLUME}

*** Test Cases ***
Dump Empty Volume
    ${dump}=  Set Variable  /tmp/${VOLUME}.dump
    Create Volume  ${SERVER}  ${PARTITION}  ${VOLUME}
    Command Should Succeed  ${VOS} dump -id ${VOLUME} -file ${dump}
    Should Exist  ${dump}
    Should Be a Dump File  ${dump}
    Remove File   ${dump}
    Remove Volume  ${VOLUME}

Restore Volume
    ${dump}=  Set Variable  /tmp/${VOLUME}.dump
    Create a Test Volume
    Command Should Succeed  ${VOS} dump -id ${VOLUME} -file ${dump}
    Remove the Test Volume
    Should Exist  ${dump}
    Should Be a Dump File  ${dump}
    Command Should Succeed  ${VOS} restore ${SERVER} ${PARTITION} restore.test -file ${dump} -overwrite full
    Remove Volume  restore.test

Restore Bad Dump
    ${dump}=  Set Variable  /tmp/bad.dump
    Create Bad Dump  ${dump}
    Command Should Fail  ${VOS} restore ${SERVER} ${PARTITION} bad.test -file ${dump} -overwrite full


*** Keywords ***

Create a Test Volume
    Create Volume  ${SERVER}  ${PARTITION}  ${VOLUME}
    Mount Volume  ${TESTPATH}  ${VOLUME}
    Add Access Rights  ${TESTPATH}  system:anyuser  read
    Command Should Succeed  mkdir -p ${TESTPATH}/mydir
    Add Access Rights  ${TESTPATH}/mydir  system:authuser  write

Remove the Test Volume
    Remove Mount Point  ${TESTPATH}
    Remove Volume  ${VOLUME}

