# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Executable tests
Resource          openafs.robot
Suite Setup       Setup
Suite Teardown    Teardown

*** Variables ***
${VOLUME}      test.execute
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
Write and Execute a Script in a Directory
    [Tags]  arla  #(exec)
    ${file}=  Set Variable  ${TESTPATH}/script.sh
    ${text}=  Set Variable  hello world
    #Should Not Exist        ${file}
    ${code}=  Catenate
    ...  \#!/bin/sh\n
    ...  echo -n ${text}\n
    Create File                  ${file}  ${code}
    Should Exist                 ${file}
    Command Should Succeed       chmod +x ${file}
    File Should Be Executable    ${file}
    ${rc}  ${output}  Run And Return Rc And Output  ${file}
    Should Be Equal As Integers  ${rc}  0
    Should Match  ${output}  ${text}

