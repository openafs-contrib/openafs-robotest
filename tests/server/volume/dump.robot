# Copyright (c) 2015 Sine Nomine Associates
# See LICENSE

*** Settings ***
Resource           openafs.robot
Suite Setup        Login  ${AFS_ADMIN}
Suite Teardown     Logout

*** Variables ***
${volume}      test.dump
${part}        a
${server}      ${FILESERVER}
${dump}        /tmp/test.dump

*** Test Cases ***
Dump an empty volume
    [Setup]     Create volume   ${volume}
    [Teardown]  Remove volume   ${volume}
    Command should succeed  ${VOS} dump -id ${volume} -file ${dump}
    Dump successful

*** Keywords ***
Dump successful
    Log     todo

