# Copyright (c) 2015 Sine Nomine Associates
# See LICENSE

*** Settings ***
Resource          common.robot
Suite Setup       Setup Users and Groups
Suite Teardown    Teardown Users and Groups
Test Setup        Setup Test Directory
Test Teardown     Teardown Test Directory

*** Variables ***
${PATH}     /afs/.${AFS_CELL}/test/acltest
${PATH2}    /afs/.${AFS_CELL}/test/acltest2

*** Keywords ***
Setup Users and Groups
    Login  ${AFS_ADMIN}
    Command Should Succeed  ${PTS} createuser ${AFS_USER}
    Command Should Succeed  ${PTS} creategroup group1 -owner ${AFS_ADMIN}
    Command Should Succeed  ${PTS} adduser ${AFS_USER} group1

Teardown Users and Groups
    Command Should Succeed  ${PTS} delete ${AFS_USER}
    Command Should Succeed  ${PTS} delete group1
    Logout

Setup Test Directory
    Create Directory  ${PATH}
    Create Directory  ${PATH2}
    Access Control List Matches      ${PATH}
    ...  system:administrators rlidwka
    ...  system:anyuser rl

Teardown Test Directory
    Access Control List Contains     ${PATH}  system:administrators  rlidwka
    Remove Directory  ${PATH}
    Remove Directory  ${PATH2}

*** Test Cases ***
Add a User to an ACL
    Access Control Should Not Exist  ${PATH}  ${AFS_USER}
    Command Should Succeed           ${FS} setacl ${PATH} ${AFS_USER} rl
    Access Control List Contains     ${PATH}  ${AFS_USER}  rl

Add a Group to an ACL
    Access Control Should Not Exist  ${PATH}  group1
    Command Should Succeed           ${FS} setacl ${PATH} group1 rl
    Access Control List Contains     ${PATH}  group1  rl

Add Negative ACL Rights for a User
    Access Control Should Not Exist  ${PATH}  ${AFS_USER}
    Command Should Succeed           ${FS} setacl ${PATH} ${AFS_USER} rl -negative
    Access Control List Contains     ${PATH}  ${AFS_USER}  -rl

Clear Negative ACL Rights for a User
    Access Control Should Not Exist  ${PATH}  ${AFS_USER}
    Command Should Succeed           ${FS} setacl ${PATH} ${AFS_USER} rlidw
    Command Should Succeed           ${FS} setacl ${PATH} ${AFS_USER} rl -negative
    Access Control List Contains     ${PATH}  ${AFS_USER}   rlidw
    Access Control List Contains     ${PATH}  ${AFS_USER}   -rl
    Command Should Succeed           ${FS} setacl ${PATH} ${AFS_USER} r -negative
    Access Control List Contains     ${PATH}  ${AFS_USER}   rlidw
    Access Control List Contains     ${PATH}  ${AFS_USER}   -r

Remove a User from an ACL
    Access Control Should Not Exist  ${PATH}  ${AFS_USER}
    Command Should Succeed           ${FS} setacl ${PATH} ${AFS_USER} rl
    Access Control List Contains     ${PATH}  ${AFS_USER}  rl
    Command Should Succeed           ${FS} setacl ${PATH} ${AFS_USER} none
    Access Control Should Not Exist  ${PATH}  ${AFS_USER}

Remove a Group from an ACL
    Access Control Should Not Exist  ${PATH}  group1
    Command Should Succeed           ${FS} setacl ${PATH} group1 rl
    Access Control List Contains     ${PATH}  group1  rl
    Command Should Succeed           ${FS} setacl ${PATH} group1 none
    Access Control Should Not Exist  ${PATH}  group1

Copy an ACL
    Command Should Succeed           ${FS} setacl ${PATH} ${AFS_USER} rlidw
    Command Should Succeed           ${FS} setacl ${PATH} ${AFS_USER} rl -negative
    Command Should Succeed           ${FS} setacl ${PATH} group1 rl
    Command Should Succeed           ${FS} copyacl ${PATH} ${PATH2}
    Access Control List Matches      ${PATH2}
    ...  system:administrators rlidwka
    ...  system:anyuser rl
    ...  ${AFS_USER} rlidw
    ...  ${AFS_USER} -rl
    ...  group1 rl

Remove Obsolete ACL Entries
    Command Should Succeed           ${FS} setacl ${PATH2} ${AFS_USER} rlidw
    ${output}=  Run                  ${FS} cleanacl -path ${PATH2}
    Should Contain                   ${output}  fine

Show User's Directory Access
    Command Should Succeed           ${FS} setacl ${PATH2} ${AFS_USER} rlidw
    ${output}=  Run                  ${FS} gca ${PATH2}
    Should Contain                   ${output}  rlidw
