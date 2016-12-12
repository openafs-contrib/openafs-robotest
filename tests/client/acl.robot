# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Resource          openafs.robot
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
    Command Should Succeed  ${PTS} createuser user1
    Command Should Succeed  ${PTS} createuser user2
    Command Should Succeed  ${PTS} creategroup group1 -owner ${AFS_ADMIN}
    Command Should Succeed  ${PTS} adduser user1 group1
    Command Should Succeed  ${PTS} adduser user2 group1

Teardown Users and Groups
    Command Should Succeed  ${PTS} delete user1
    Command Should Succeed  ${PTS} delete user2
    Command Should Succeed  ${PTS} delete group1
    Logout

Setup Test Directory
    Create Directory  ${PATH}
    Access Control List Matches      ${PATH}
    ...  system:administrators rlidwka
    ...  system:anyuser rl

Teardown Test Directory
    Access Control List Contains     ${PATH}  system:administrators  rlidwka
    Remove Directory  ${PATH}

*** Test Cases ***
Add a User to an ACL
    Access Control Should Not Exist  ${PATH}  user1
    Command Should Succeed           ${FS} setacl ${PATH} user1 rl
    Access Control List Contains     ${PATH}  user1  rl

Add a Group to an ACL
    Access Control Should Not Exist  ${PATH}  group1
    Command Should Succeed           ${FS} setacl ${PATH} group1 rl
    Access Control List Contains     ${PATH}  group1  rl

Add Negative ACL Rights for a User
    Access Control Should Not Exist  ${PATH}  user1
    Command Should Succeed           ${FS} setacl ${PATH} user1 rl -negative
    Access Control List Contains     ${PATH}  user1  -rl

Clear Negative ACL Rights for a User
    Access Control Should Not Exist  ${PATH}  user1
    Command Should Succeed           ${FS} setacl ${PATH} user1 rlidw
    Command Should Succeed           ${FS} setacl ${PATH} user1 rl -negative
    Access Control List Contains     ${PATH}  user1   rlidw
    Access Control List Contains     ${PATH}  user1   -rl
    Command Should Succeed           ${FS} setacl ${PATH} user1 r -negative
    Access Control List Contains     ${PATH}  user1   rlidw
    Access Control List Contains     ${PATH}  user1   -r

Remove a User from an ACL
    Access Control Should Not Exist  ${PATH}  user1
    Command Should Succeed           ${FS} setacl ${PATH} user1 rl
    Access Control List Contains     ${PATH}  user1  rl
    Command Should Succeed           ${FS} setacl ${PATH} user1 none
    Access Control Should Not Exist  ${PATH}  user1

Remove a Group from an ACL
    Access Control Should Not Exist  ${PATH}  group1
    Command Should Succeed           ${FS} setacl ${PATH} group1 rl
    Access Control List Contains     ${PATH}  group1  rl
    Command Should Succeed           ${FS} setacl ${PATH} group1 none
    Access Control Should Not Exist  ${PATH}  group1

Copy an ACL
    Create Directory                 ${PATH2}
    Command Should Succeed           ${FS} setacl ${PATH} user1 rlidw
    Command Should Succeed           ${FS} setacl ${PATH} user1 rl -negative
    Command Should Succeed           ${FS} setacl ${PATH} group1 rl
    Command Should Succeed           ${FS} copyacl ${PATH} ${PATH2}
    Access Control List Matches      ${PATH2}
    ...  system:administrators rlidwka
    ...  system:anyuser rl
    ...  user1 rlidw
    ...  user1 -rl
    ...  group1 rl
    Remove Directory                 ${PATH2}

Remove Obsolete ACL Entries
    Create Directory                 ${PATH2}
    Command Should Succeed           ${FS} setacl ${PATH2} user1 rlidw
    ${output}=  Run                  ${FS} cleanacl -path ${PATH2}
    Should Contain                   ${output}  fine
    Remove Directory                 ${PATH2}

Show User's Directory Access
    Create Directory                 ${PATH2}
    Command Should Succeed           ${FS} setacl ${PATH2} user1 rlidw
    ${output}=  Run                  ${FS} gca ${PATH2}
    Should Contain                   ${output}  rlidw
    Remove Directory                 ${PATH2}
