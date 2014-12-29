# Copyright (c) 2014, Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation     Import common keywords and variables for
...               the OpenAFS test suite.
Library           OperatingSystem
Library           String
Library           OpenAFS
Library           Kerberos
Resource          prechecks.robot
Resource          newcell.robot
Variables         sysinfo.py
Variables         ${AFS_DIST}.py
Resource          ${AFS_DIST}.robot

*** Keywords ***
Run Command
    [arguments]  ${cmd}
    ${rc}  ${output}  Run And Return Rc And Output    ${cmd}
    Should Be Equal As Integers  ${rc}  0

Sudo
    [arguments]  ${cmd}  @{args}
    ${arg}  Catenate  @{args}
    Run Command  sudo -n ${cmd} ${arg}

Program Should Be Running
    [arguments]  ${program}
    ${output}  Run   ps --no-headers -o cmd -e
    Should Contain  ${output}  ${program}

Program Should Not Be Running
    [Arguments]  ${program}
    ${output}  Run  ps --no-headers -o cmd -e
    Should Not Contain  ${output}  ${program}

Rx Service Should Be Reachable
    [Arguments]  ${host}  ${port}
    Run Command  ${RXDEBUG} ${host} ${port} -version

Login
    [Arguments]  ${name}
    Should Not Be Empty  ${name}
    # Convert OpenAFS k4 style names to k5 style principals.
    ${principal}=  Replace String  ${name}  .  /
    ${keytab}=  Set Variable If  "${name}"=="${AFS_USER}"    ${KRB_USER_KEYTAB}
    ${keytab}=  Set Variable If  "${name}"=="${AFS_ADMIN}"   ${KRB_ADMIN_KEYTAB}
    File Should Exist   ${keytab}
    Remove File  site/krb5cc
    Run Command  KRB5CCNAME=site/krb5cc ${KINIT} -5 -k -t ${keytab} ${principal}@${KRB_REALM}
    Run Command  KRB5CCNAME=site/krb5cc ${AKLOG} -d -c ${AFS_CELL} -k ${KRB_REALM}

Create Volume
    [Arguments]  ${server}  ${part}  ${name}
    Run Command  ${VOS} create -server ${server} -partition ${part} -name ${name} -verbose

Remove Volume
    [Arguments]  ${name}
    Run Command  ${VOS} remove -id ${name}

Mount Volume
    [Arguments]  ${dir}  ${vol}  @{options}
    ${opts}  Catenate  @{options}
    Run Command  ${FS} mkmount -dir ${dir} -vol ${vol} ${opts}

Remove Mount Point
    [Arguments]  ${dir}
    Run Command  ${FS} rmmount -dir ${dir}

Add Access Rights
    [Arguments]  ${dir}  ${group}  ${rights}
    Run Command  ${FS} setacl -dir ${dir} -acl ${group} ${rights}

Replicate Volume
    [Arguments]    ${server}  ${part}  ${volume}
    Run Command    ${VOS} addsite -server ${server} -part ${part} -id ${volume}
    Run Command    ${VOS} release -id ${volume} -verbose
