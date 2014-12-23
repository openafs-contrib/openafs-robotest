# Copyright (c) 2014, Sine Nomine Associates
# See LICENSE

*** Settings ***
Resource          robotest.robot

*** Test Cases ***
Create a Test Volume
    Login  ${AFS_ADMIN}
    Create Volume  ${OS_NODE}  a  test
    Mount Volume  /afs/${AFS_CELL}/test  test
    Add Access Rights  /afs/${AFS_CELL}/test  system:anyuser  read
    Create File    /afs/${AFS_CELL}/test/hello    Hello world!\n
    ${text}=  Get File  /afs/${AFS_CELL}/test/hello

Remove Test Volume
    Login  ${AFS_ADMIN}
    Remove Mount Point  /afs/${AFS_CELL}/test
    Remove Volume  test

