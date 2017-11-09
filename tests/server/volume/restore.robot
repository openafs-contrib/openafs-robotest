# Copyright (c) 2015-2017 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation       Tests to verify volume restore operations with the
...                 various of the restore options and to test the volume
...                 server robustness while attempting to restore invalid
...                 volume dump streams.
Resource            openafs.robot
Suite Setup         Login  ${AFS_ADMIN}
Suite Teardown      Logout
Test Teardown       Run keywords
...                 Remove volume   ${volume}   AND
...                 Remove file     ${dump}

*** Variables ***
${volume}           test.restore
${part}             a
${server}           ${HOSTNAME}
${dump}             /tmp/restore.dump

*** Test Cases ***
Restore to a new volume name
    [Setup]     Run keywords
    ...         Create dump  ${dump}            AND
    ...         Volume should not exist  ${volume}
    Command should succeed   ${VOS} restore ${server} ${part} ${volume} -file ${dump} -overwrite full
    Volume should exist      ${volume}
    Volume location matches  ${volume}  ${server}  ${part}  vtype=rw

Restore an empty volume
    [Setup]     Run keywords
    ...         Create empty dump  ${dump}      AND
    ...         Volume should not exist  ${volume}
    Command should succeed   ${VOS} restore ${server} ${part} ${volume} -file ${dump} -overwrite full
    Volume should exist      ${volume}
    Volume location matches  ${volume}  ${server}  ${part}  vtype=rw

*** Keywords ***
Create dump
    [Arguments]  ${dumpfile}
    Command should succeed    ${VOS} dump test -file ${dumpfile}

