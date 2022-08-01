*** Comments ***
# Copyright #(c) 2015 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation       Ptserver tests

Library             OperatingSystem
Library             String
Library             OpenAFSLibrary

Suite Setup         Login    ${AFS_ADMIN}    keytab=${AFS_ADMIN_KEYTAB}
Suite Teardown      Logout

*** Test Cases ***
| Create a User
|  | [Setup]        | Create User
|  | ${output}=     | Run         | ${PTS} listentries
|  | Should Contain | ${output}   | user12
|  | [Teardown]     | Remove User
|
| Create a Group
|  | [Setup]            | Create Group
|  | ${output}=         | Run          | ${PTS} membership group12
|  | Should Not Contain | ${output}    | user12
|  | [Teardown]         | Remove Group
|
| Add a User to a Group
|  | [Setup]                | Create User and Group
|  | Command Should Succeed | ${PTS} adduser user12 group12
|  | ${output}=             | Run                              | ${PTS} membership group12
|  | Should Contain         | ${output}                        | user12
|  | Command Should Succeed | ${PTS} removeuser user12 group12
|  | ${output}=             | Run                              | ${PTS} membership group12
|  | Should Not Contain     | ${output}                        | user12
|  | [Teardown]             | Remove User and Group
|
| Chown a Group
|  | [Setup]                | Create User and Group
|  | Command Should Succeed | ${PTS} chown group12 user12
|  | ${output}=             | Run                         | ${PTS} examine group12
|  | Should Contain         | ${output}                   | owner: user12
|  | [Teardown]             | Remove User and Group
|
| Get User Membership
|  | [Setup]            | Create User
|  | ${output}=         | Run         | ${PTS} membership user12
|  | Should Not Contain | ${output}   | group12
|  | [Teardown]         | Remove User
|
| Get Group Membership
|  | [Setup]            | Create Group
|  | ${output}=         | Run          | ${PTS} membership group12
|  | Should Not Contain | ${output}    | user12
|  | [Teardown]         | Remove Group
|
| Examine a User
|  | [Setup]            | Create User
|  | ${output}=         | Run         | ${PTS} examine user12
|  | Should Not Contain | ${output}   | group12
|  | [Teardown]         | Remove User
|
| Examine a Group
|  | [Setup]            | Create Group
|  | ${output}=         | Run          | ${PTS} examine group12
|  | Should Not Contain | ${output}    | user12
|  | [Teardown]         | Remove Group
|
| Remove a User from a Group
|  | [Setup]                | Create User and Group
|  | Command Should Succeed | ${PTS} adduser user12 group12
|  | ${output}=             | Run                              | ${PTS} membership group12
|  | Should Contain         | ${output}                        | user12
|  | Command Should Succeed | ${PTS} removeuser user12 group12
|  | ${output}=             | Run                              | ${PTS} membership group12
|  | Should Not Contain     | ${output}                        | user12
|  | [Teardown]             | Remove User and Group
|
| List Groups a User Owns
|  | [Setup]            | Create User
|  | ${output}=         | Run         | ${PTS} listowned user12
|  | Should Not Contain | ${output}   | group12
|  | [Teardown]         | Remove User
|
| Set and List Maxuser
|  | ${output}=      | Run       | ${PTS} setmax -group -500 -user 1000
|  | ${output}=      | Run       | ${PTS} listmax
|  | Should Be Equal | ${output} | Max user id is 1000 and max group id is -500.
|
| Set Fields on a User
|  | [Setup]                | Create User
|  | Command Should Succeed | ${PTS} setfields user12 -groupquota 56
|  | ${output}=             | Run                                    | ${PTS} examine user12
|  | Should Contain         | ${output}                              | group quota: 56
|  | [Teardown]             | Remove User
|
| Delete a Group
|  | [Setup]            | Create Group
|  | ${output}=         | Run          | ${PTS} membership group12
|  | Should Not Contain | ${output}    | user12
|  | [Teardown]         | Remove Group
|
| Delete a User
|  | [Setup]            | Create User
|  | ${output}=         | Run         | ${PTS} membership user12
|  | Should Not Contain | ${output}   | group12
|  | [Teardown]         | Remove User

*** Keywords ***
| Teardown Users and Groups
|  | Command Should Succeed | ${PTS} delete user12
|  | Command Should Succeed | ${PTS} delete group12
|
| Create User and Group
|  | ${output}=             | Run                                            | ${PTS} listentries -users -groups
|  | Should Not Contain     | ${output}                                      | user12
|  | Should Not Contain     | ${output}                                      | group12
|  | Command Should Succeed | ${PTS} createuser user12
|  | Command Should Succeed | ${PTS} creategroup group12 -owner ${AFS_ADMIN}
|  | ${output}=             | Run                                            | ${PTS} listentries -users -groups
|
| Remove User and Group
|  | Command Should Succeed | ${PTS} delete group12
|  | Command Should Succeed | ${PTS} delete user12
|  | ${output}=             | Run                   | ${PTS} listentries -users -groups
|  | Should Not Contain     | ${output}             | user12
|  | Should Not Contain     | ${output}             | group12
|
| Create User
|  | ${output}=             | Run                      | ${PTS} listentries
|  | Should Not Contain     | ${output}                | user12
|  | Command Should Succeed | ${PTS} createuser user12
|
| Remove User
|  | Command Should Succeed | ${PTS} delete user12
|  | ${output}=             | Run                  | ${PTS} listentries
|  | Should Not Contain     | ${output}            | user12
|
| Create Group
|  | ${output}=             | Run                        | ${PTS} listentries
|  | Should Not Contain     | ${output}                  | group12
|  | Command Should Succeed | ${PTS} creategroup group12
|
| Remove Group
|  | Command Should Succeed | ${PTS} delete group12
|  | ${output}=             | Run                   | ${PTS} listentries
|  | Should Not Contain     | ${output}             | group12
