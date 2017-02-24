# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Directory Object tests
Resource          openafs.robot
Suite Setup       Setup
Suite Teardown    Teardown

*** Variables ***
${VOLUME}      test.basic
${PARTITION}   a
${SERVER}      ${HOSTNAME}
${TESTPATH}    /afs/.${AFS_CELL}/test/${VOLUME}

*** Keywords ***
Setup
    Login  ${AFS_ADMIN}
    Create Volume  ${VOLUME}  server=${SERVER}  part=${PARTITION}  path=${TESTPATH}  acl=system:anyuser,read

Teardown
    Remove Volume  ${VOLUME}  path=${TESTPATH}
    Logout

*** Test Cases ***
Unicode File Name
    ${name}=   Set Variable      \u20ac\u2020\u2021
    ${file}=   Set Variable      ${TESTPATH}/${name}
    Should Not Exist             ${file}
    Create File                  ${file}  Hello world!  UTF-8
    Should Exist                 ${file}
    Remove File                  ${file}
    Should Not Exist             ${file}

