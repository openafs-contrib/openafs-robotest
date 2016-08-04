# Copyright #(c) 2015 Sine Nomine Associates
# Copyright #(c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Ptserver tests
Resource          openafs.robot

*** Test Cases ***
Create a User
    [Tags]  arla  #(ptscreateuser)
    Login  ${AFS_ADMIN}
    Command Should Succeed  ${PTS} createuser userA

Create a Group
    [Tags]  arla  #(ptscreategroup)
    Command Should Succeed  ${PTS} creategroup groupA -owner ${AFS_ADMIN}

Add a User to a Group
    [Tags]  arla  #(ptsadduser)
    Command Should Succeed  ${PTS} adduser userA groupA

Chown a Group
    [Tags]  todo  arla  #(ptschown)
    TODO

Get User Membership
    [Tags]  arla  #(ptsmembersuser)
    Command Should Succeed  ${PTS} membership userA

Get Group Membership
    [Tags]  arla  #(ptsmembersgroup)
    Command Should Succeed  ${PTS} membership groupA

Examine a User
    [Tags]  arla  #(ptsexamineuser)
    Command Should Succeed  ${PTS} examine userA

Examine a Group
    [Tags]  arla  #(ptsexaminegroup)
    Command Should Succeed  ${PTS} examine groupA

Remove a User from a Group
    [Tags]  arla  #(ptsremove)
    Command Should Succeed  ${PTS} removeuser userA groupA

List Groups a User Owns
    [Tags]  arla  #(ptslistown)
    Command Should Succeed  ${PTS} listowned userA

Set Maxuser
    [Tags]  arla  #(ptssetmax)
    Command Should Succeed  ${PTS} setmax -user 1000

List Maxuser
    [Tags]  arla  #(ptslistmax)
    Command Should Succeed  ${PTS} listmax 

Set Fields on a User
    [Tags]  todo  arla  #(ptssetf)
    TODO

Delete a Group
    [Tags]  arla  #(ptsdeletegroup)
    Command Should Succeed  ${PTS} delete groupA

Delete a User
    [Tags]  arla  #(ptsdeleteuser)
    Command Should Succeed  ${PTS} delete userA
    Logout


