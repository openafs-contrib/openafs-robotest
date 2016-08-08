# Copyright #(c) 2015 Sine Nomine Associates
# Copyright #(c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Ptserver tests
Resource          openafs.robot

*** Keywords ***
Teardown Users and Groups
    Command Should Succeed  ${PTS} delete user12
    Command Should Succeed  ${PTS} delete group12

*** Test Cases ***
Create a User
    [Tags]  arla  #(ptscreateuser)
    Login  ${AFS_ADMIN}
    ${output}=  Run         ${PTS} listentries 
    Should Not Contain      ${output}  user12
    Command Should Succeed  ${PTS} createuser user12
    ${output}=  Run         ${PTS} listentries
    Should Contain          ${output}  user12
    Command Should Succeed  ${PTS} delete user12
    ${output}=  Run         ${PTS} listentries
    Should Not Contain      ${output}  user12

Create a Group
    [Tags]  arla  #(ptscreategroup)
    ${output}=  Run         ${PTS} listentries -groups
    Should Not Contain      ${output}  group12
    Command Should Succeed  ${PTS} creategroup group12 -owner ${AFS_ADMIN}
    ${output}=  Run         ${PTS} membership group12
    Should Not Contain      ${output}  user12
    Command Should Succeed  ${PTS} delete group12
    ${output}=  Run         ${PTS} listentries -groups
    Should Not Contain      ${output}  group12

Add a User to a Group
    [Tags]  arla  #(ptsadduser)
    ${output}=  Run         ${PTS} listentries -users -groups
    Should Not Contain      ${output}  user12
    Should Not Contain      ${output}  group12
    Command Should Succeed  ${PTS} createuser user12
    Command Should Succeed  ${PTS} creategroup group12 -owner ${AFS_ADMIN}
    ${output}=  Run         ${PTS} listentries -users -groups
    Should Contain          ${output}  user12
    Should Contain          ${output}  group12
    Command Should Succeed  ${PTS} adduser user12 group12
    ${output}=  Run         ${PTS} membership group12
    Should Contain          ${output}  user12
    Command Should Succeed  ${PTS} removeuser user12 group12
    ${output}=  Run         ${PTS} membership group12
    Should Not Contain      ${output}  user12
    Command Should Succeed  ${PTS} delete group12
    Command Should Succeed  ${PTS} delete user12
    ${output}=  Run         ${PTS} listentries -users -groups
    Should Not Contain      ${output}  user12
    Should Not Contain      ${output}  group12

Chown a Group
    [Tags]  todo  arla  #(ptschown)
    TODO

Get User Membership
    [Tags]  arla  #(ptsmembersuser)
    ${output}=  Run         ${PTS} listentries
    Should Not Contain      ${output}  user12
    Command Should Succeed  ${PTS} createuser user12
    ${output}=  Run         ${PTS} membership user12
    Should Not Contain      ${output}  group12
    Command Should Succeed  ${PTS} delete user12
    ${output}=  Run         ${PTS} listentries
    Should Not Contain      ${output}  user12

Get Group Membership
    [Tags]  arla  #(ptsmembersgroup)
    ${output}=  Run         ${PTS} listentries -groups
    Should Not Contain      ${output}  group12
    Command Should Succeed  ${PTS} creategroup group12 -owner ${AFS_ADMIN}
    ${output}=  Run         ${PTS} membership group12
    Should Not Contain      ${output}  user12
    Command Should Succeed  ${PTS} delete group12
    ${output}=  Run         ${PTS} listentries -groups
    Should Not Contain      ${output}  user12

Examine a User
    [Tags]  arla  #(ptsexamineuser)
    ${output}=  Run         ${PTS} listentries
    Should Not Contain      ${output}  user12
    Command Should Succeed  ${PTS} createuser user12
    ${output}=  Run         ${PTS} examine user12
    Should Not Contain      ${output}  group12
    Command Should Succeed  ${PTS} delete user12
    ${output}=  Run         ${PTS} listentries
    Should Not Contain      ${output}  user12

Examine a Group
    [Tags]  arla  #(ptsexaminegroup)
    ${output}=  Run         ${PTS} listentries -groups
    Should Not Contain      ${output}  group12
    Command Should Succeed  ${PTS} creategroup group12 -owner ${AFS_ADMIN}
    ${output}=  Run         ${PTS} examine group12
    Should Not Contain      ${output}  user12
    Command Should Succeed  ${PTS} delete group12
    ${output}=  Run         ${PTS} listentries -groups
    Should Not Contain      ${output}  group12

Remove a User from a Group
    [Tags]  arla  #(ptsremove)
    ${output}=  Run         ${PTS} listentries -users -groups
    Should Not Contain      ${output}  user12
    Should Not Contain      ${output}  group12
    Command Should Succeed  ${PTS} createuser user12
    Command Should Succeed  ${PTS} creategroup group12 -owner ${AFS_ADMIN}
    ${output}=  Run         ${PTS} listentries -users -groups
    Should Contain          ${output}  user12
    Should Contain          ${output}  group12
    Command Should Succeed  ${PTS} adduser user12 group12
    ${output}=  Run         ${PTS} membership group12
    Should Contain          ${output}  user12
    Command Should Succeed  ${PTS} removeuser user12 group12
    ${output}=  Run         ${PTS} membership group12
    Should Not Contain      ${output}  user12
    Command Should Succeed  ${PTS} delete group12
    Command Should Succeed  ${PTS} delete user12
    ${output}=  Run         ${PTS} listentries -users -groups
    Should Not Contain      ${output}  group12
    Should Not Contain      ${output}  user12

List Groups a User Owns
    [Tags]  arla  #(ptslistown)
    ${output}=  Run         ${PTS} listentries -groups
    Should Not Contain      ${output}  groups12
    Command Should Succeed  ${PTS} createuser user12
    ${output}=  Run         ${PTS} listowned user12
    Should Not Contain      ${output}  group12
    Command Should Succeed  ${PTS} delete user12
    ${output}=  Run         ${PTS} listentries -groups
    Should Not Contain      ${output}  group12

Set Maxuser
    [Tags]  arla  #(ptssetmax)
    ${output}  Run          ${PTS} setmax -group -500 -user 1000
    ${output}  Run          ${PTS} listmax
    Should Be Equal         ${output}  Max user id is 1000 and max group id is -500.

List Maxuser
    [Tags]  arla  #(ptslistmax)
    ${output}  Run          ${PTS} setmax -group -520 -user 1200
    ${output}  Run          ${PTS} listmax
    Should Be Equal         ${output}  Max user id is 1200 and max group id is -520.

Set Fields on a User
    [Tags]  arla  #(ptssetf)
    ${output}=  Run         ${PTS} listentries
    Should Not Contain      ${output}  user12
    Command Should Succeed  ${PTS} createuser user12
    ${output}=  Run         ${PTS} listentries
    Should Contain          ${output}  user12
    Command Should Succeed  ${PTS} setfields user12 -groupquota 56
    ${output}=  Run         ${PTS} examine user12
    Should Contain          ${output}  group quota: 56
    Command Should Succeed  ${PTS} delete user12
    ${output}=  Run         ${PTS} listentries
    Should Not Contain      ${output}  user12

Delete a Group
    [Tags]  arla  #(ptsdeletegroup)
    ${output}=  Run         ${PTS} listentries -groups
    Should Not Contain      ${output}  group12
    Command Should Succeed  ${PTS} creategroup group12 -owner ${AFS_ADMIN}
    ${output}=  Run         ${PTS} membership group12
    Should Not Contain      ${output}  user12
    Command Should Succeed  ${PTS} delete group12
    ${output}=  Run         ${PTS} listentries -groups
    Should Not Contain      ${output}  group12

Delete a User
    [Tags]  arla  #(ptsdeleteuser)
    ${output}=  Run         ${PTS} listentries
    Should Not Contain      ${output}  user12
    Command Should Succeed  ${PTS} createuser user12
    ${output}=  Run         ${PTS} listentries
    Should Contain          ${output}  user12
    Command Should Succeed  ${PTS} delete user12
    ${output}=  Run         ${PTS} listentries
    Should Not Contain      ${output}  user12
    Logout
