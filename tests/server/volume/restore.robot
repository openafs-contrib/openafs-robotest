# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation      Volume dump and restore tests
Resource           openafs.robot
Suite Setup        Login  ${AFS_ADMIN}
Suite Teardown     Logout

*** Variables ***
${VOLUME}      dump.test
${PART}        a
${SERVER}      ${HOSTNAME}
${TESTPATH}    /afs/.${AFS_CELL}/test/${VOLUME}
${DUMP}        /tmp/robotest.dump

*** Keywords ***
Remove Dumped Volume
    Remove Volume  ${VOLUME}
    Remove File    ${DUMP}
    Crash Check

Dump Successful
    Should Exist   ${DUMP}
    Should Be a Dump File  ${DUMP}

Remove Restored Volumes
    Remove Volume  ${VOLUME}  path=${TESTPATH}
    Remove Volume  ${VOLUME}.restore
    Remove File   ${DUMP}
    Crash Check

Create and Dump Volume
    Init Crash Check
    Create Volume  ${VOLUME}  server=${SERVER}  part=${PART}  path=${TESTPATH}  acl=system:anyuser,read
    Command Should Succeed  ${VOS} dump -id ${VOLUME} -file ${DUMP}
    Dump Successful

Bogus ACL Dump
    Init Crash Check
    Create Dump with Bogus ACL  ${DUMP}

Create New Volume
    Init Crash Check
    Create Volume  ${VOLUME}  server=${SERVER}  part=${PART}

New Empty Dump
    Init Crash Check
    Create Empty Dump  ${DUMP}

*** Test Cases ***
Dump an Empty Volume
    [Setup]       Create New Volume
    Command Should Succeed  ${VOS} dump -id ${VOLUME} -file ${DUMP}
    Dump Successful
    [Teardown]    Remove Dumped Volume

Restore a Volume
    [Setup]       Create and Dump Volume
    Command Should Succeed  ${VOS} restore ${SERVER} ${PART} ${VOLUME}.restore -file ${DUMP} -overwrite full
    [Teardown]    Remove Restored Volumes

Restore an Empty Dump
    [Setup]       New Empty Dump
    Command Should Succeed  ${VOS} restore ${SERVER} ${PART} ${VOLUME} -file ${DUMP} -overwrite full
    [Teardown]    Remove Dumped Volume

Restore a Volume Containing a Bogus ACL
    [Tags]    bug
    [Setup]       Bogus ACL Dump
    Command Should Fail  ${VOS} restore ${SERVER} ${PART} ${VOLUME} -file ${DUMP} -overwrite full
    [Teardown]    Remove Dumped Volume
