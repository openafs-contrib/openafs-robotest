# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Resource          common.robot
Suite Setup       Login  ${AFS_ADMIN}
Suite Teardown    Logout

*** Variables ***
${SERVER}        @{AFS_FILESERVERS}[0]


*** Test Cases ***
Release a Volume
    [Setup]     Create Volume  xyzzy
    [Teardown]  Remove Volume  xyzzy
    Command Should Succeed    ${VOS} addsite ${SERVER} a xyzzy
    Command Should Succeed    ${VOS} release xyzzy
    Volume Should Exist       xyzzy.readonly
    Volume Location Matches   xyzzy  server=${SERVER}  part=a  vtype=ro
