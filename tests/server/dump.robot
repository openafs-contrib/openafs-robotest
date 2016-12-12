# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation      Volume dump and restore tests
Resource           openafs.robot
Suite Setup        Login  ${AFS_ADMIN}
Suite Teardown     Logout
Test Setup         Init Crash Check
Test Teardown      Crash Check

*** Variables ***
${VOLUME}      dump.test
${PART}        a
${SERVER}      ${HOSTNAME}
${TESTPATH}    /afs/.${AFS_CELL}/test/${VOLUME}
${DUMP}        /tmp/robotest.dump

*** Test Cases ***
Dump an Empty Volume
    Create Volume  ${VOLUME}  server=${SERVER}  part=${PART}
    Command Should Succeed  ${VOS} dump -id ${VOLUME} -file ${DUMP}
    Should Exist   ${DUMP}
    Should Be a Dump File  ${DUMP}
    Remove Volume  ${VOLUME}
    Remove File    ${DUMP}

Restore a Volume
    Create Volume  ${VOLUME}  server=${SERVER}  part=${PART}  path=${TESTPATH}  acl=system:anyuser,read
    Command Should Succeed  ${VOS} dump -id ${VOLUME} -file ${DUMP}
    Should Exist  ${DUMP}
    Should Be a Dump File  ${DUMP}
    Command Should Succeed  ${VOS} restore ${SERVER} ${PART} ${VOLUME}.restore -file ${DUMP} -overwrite full
    Remove Volume  ${VOLUME}  path=${TESTPATH}
    Remove Volume  ${VOLUME}.restore
    Remove File   ${DUMP}

Restore an Empty Dump
    Create Empty Dump  ${DUMP}
    Command Should Succeed  ${VOS} restore ${SERVER} ${PART} ${VOLUME} -file ${DUMP} -overwrite full
    Remove Volume  ${VOLUME}
    Remove File   ${DUMP}

Restore a Volume Containing a Bogus ACL
    [Tags]  crash
    Create Dump with Bogus ACL  ${DUMP}
    Command Should Fail  ${VOS} restore ${SERVER} ${PART} ${VOLUME} -file ${DUMP} -overwrite full
    Remove Volume  ${VOLUME}
    Remove File   ${DUMP}

