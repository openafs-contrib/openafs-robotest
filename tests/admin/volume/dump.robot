# Copyright (c) 2015 Sine Nomine Associates
# See LICENSE

*** Settings ***
Library            OperatingSystem
Library            String
Library            OpenAFSLibrary
Suite Setup        Login  ${AFS_ADMIN}  password=${AFS_ADMIN_PASSWORD}
Suite Teardown     Logout
Test Teardown      Cleanup Test Volumes

*** Variables ***
${VOLUME}      test.dump
${SERVER}      ${AFS_FILESERVERS}[0]
${SERVER2}     ${AFS_FILESERVERS}[1]
${PART}        a
${DUMP}        /tmp/test.dump
${DIR}         /afs/.${AFS_CELL}/test/${VOLUME}

*** Test Cases ***
Dump an Empty Volume
    Create Volume  ${VOLUME}  ${SERVER}  ${PART}  path=${DIR}
    Command Should Succeed  ${VOS} dump -id ${VOLUME} -file ${DUMP}

Dump a Volume
    Create Volume  ${VOLUME}  ${SERVER}  ${PART}  path=${DIR}
    Create Files   ${DIR}   size=512  count=64  depth=2  width=1  fill=random
    Command Should Succeed  ${VOS} dump -id ${VOLUME} -file ${DUMP}

Dump and Restore Data Integrity
    [Tags]    requires-multi-fs
    Create Volume  ${VOLUME}  ${SERVER}  ${PART}  path=${DIR}
    Create Files   ${DIR}   size=512  count=64  depth=2  width=1  fill=random
    Dump Volume
    Restore Volume
    Compare Files

*** Keywords ***
Cleanup Test Volumes
    Remove Volume  ${VOLUME}    path=${DIR}
    Remove Volume  ${VOLUME}.r  path=${DIR}.r
    Remove File    ${DUMP}

Dump Volume
    Command Should Succeed  ${VOS} dump -id ${VOLUME} -file ${DUMP}

Restore Volume
    Command Should Succeed  ${VOS} restore -server ${SERVER2} -part ${PART} -name ${VOLUME}.r -file ${DUMP} -overwrite full
    Command Should Succeed  ${FS} mkmount -dir ${DIR}.r -vol ${VOLUME}.r

Compare Files
    Command Should Succeed  diff --recursive ${DIR} ${DIR}.r
