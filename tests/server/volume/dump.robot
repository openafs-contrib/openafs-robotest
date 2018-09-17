# Copyright (c) 2015 Sine Nomine Associates
# See LICENSE

*** Settings ***
Resource           common.robot
Suite Setup        Login  ${AFS_ADMIN}
Suite Teardown     Logout

*** Variables ***
${VOLUME}      test.dump
${SERVER}      @{AFS_FILESERVERS}[0]
${PART}        a
${DUMP}        /tmp/test.dump

*** Test Cases ***
Dump an empty volume
    [Setup]     Create volume   ${VOLUME}  ${SERVER}  ${PART}
    [Teardown]  Remove volume   ${VOLUME}
    Command should succeed  ${VOS} dump -id ${VOLUME} -file ${DUMP}
