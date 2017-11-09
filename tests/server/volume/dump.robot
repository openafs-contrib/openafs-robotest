# Copyright (c) 2015 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation      Volume restore tests
Resource           openafs.robot
Suite Setup        Login  ${AFS_ADMIN}
Suite Teardown     Logout

*** Variables ***
${VOLUME}      test.dump
${PART}        a
${SERVER}      ${HOSTNAME}
${TESTPATH}    /afs/.${AFS_CELL}/test/${VOLUME}
${DUMP}        /tmp/robotest.dump


*** Test Cases ***
Dump an empty volume
    Command should succeed  ${VOS} dump -id ${VOLUME} -file ${DUMP}
    Dump successful

