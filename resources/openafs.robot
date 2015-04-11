# Copyright (c) 2014 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation     Common keywords and variables for the OpenAFS test suite.
Library           OperatingSystem
Library           String
Library           OpenAFSLibrary
Variables         dist/${AFS_DIST}.py

*** Keywords ***
TODO
    [Arguments]  ${msg}=Not implemented
    Fail  TODO: ${msg}

#
# XXX: Move all the keywords which "run" a program to the python library.
#      Should have a common routine there which uses subprocess
#      and has consistent logging.
#

Command Should Succeed
    [Arguments]  ${cmd}  ${msg}=None
    ${rc}  ${output}  Run And Return Rc And Output  ${cmd}
    Should Be Equal As Integers  ${rc}  0
    ...  msg=${msg}: ${cmd}, rc=${rc}, ${output}
    ...  values=False

Command Should Fail
    [Arguments]  ${cmd}
    ${rc}  ${output}  Run And Return Rc And Output  ${cmd}
    Should Not Be Equal As Integers  ${rc}  0
    ...  msg=Should have failed: ${cmd}
    ...  values=False

Run Command
    [Arguments]  ${cmd}
    ${rc}  ${output}  Run And Return Rc And Output    ${cmd}
    Should Be Equal As Integers  ${rc}  0
    ...  msg=Failed: ${cmd}, rc=${rc}, ${output}
    ...  values=False

Cell Should Be
    [Arguments]  ${cellname}
    ${cmd}=  Set Variable  ${FS} wscell
    ${rc}  ${output}  Run And Return Rc And Output    ${cmd}
    Should Be Equal As Integers  ${rc}  0
    ...  msg=Failed: ${cmd}, rc=${rc}, ${output}
    ...  values=False
    Should Match  ${output}  This workstation belongs to cell '${cellname}'
    ...  msg=Client has the wrong cell name!


