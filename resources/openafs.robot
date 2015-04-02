# Copyright (c) 2014 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation     Import common keywords and variables for
...               the OpenAFS test suite.
Library           OperatingSystem
Library           String
Library           OpenAFS
Library           Kerberos
Resource          prechecks.robot
Resource          install.robot
Resource          newcell.robot
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

Should Be File
    [Arguments]  ${path}
    Should Exist     ${path}
    Should Be True   os.path.isfile("${path}")
    ...  msg=${path} is not a file.

File Should Be Executable
    [Arguments]  ${file}
    Should Not Be Empty  ${file}
    Should Be File  ${file}
    Should Be True  os.access("${file}", os.X_OK)
    ...  msg=${file} is not executable.

Should Be Symlink
    [Arguments]  ${path}
    Should Exist    ${path}
    Should Be True  os.path.islink("${path}")
    ...  msg=${path} is not a symlink.

Should Not Be Symlink
    [Arguments]  ${path}
    Should Exist        ${path}
    Should Not Be True  os.path.islink("${path}")
    ...  msg=${path} is a symlink.

Should Be Dir
    [Arguments]  ${path}
    Should Exist     ${path}
    Should Be True   os.path.isdir("${path}")
    ...  msg=${path} is not a directory.

Should Not Be Dir
    [Arguments]  ${path}
    Should Exist         ${path}
    Should Not Be True   os.path.isdir("${path}")
    ...  msg=${path} is a directory.

Link Count Should Be
    [Arguments]  ${path}  ${count}
    Should Exist    ${path}
    Should Be True  os.stat("${path}").st_nlink == ${count}
    ...  msg=${path} does not have ${count} links.

Inode Should Be Equal
    [Arguments]  ${a}  ${b}
    Should Exist  ${a}
    Should Exist  ${b}
    Should Be True  os.stat("${a}").st_ino == os.stat("${b}").st_ino
    ...  msg=${a} and ${b} do not have the same inode number.

Get Inode
    [Arguments]  ${path}
    ${inode}=  Evaluate  os.stat("${path}").st_ino  os
    [Return]  ${inode}

Start Service
    [Arguments]  ${name}
    Should Not Be Empty  ${name}
    Sudo  /sbin/service ${name} start

Stop Service
    [Arguments]  ${name}
    Should Not Be Empty  ${name}
    Sudo  /sbin/service ${name} stop

Rx Service Should Be Reachable
    [Arguments]  ${host}  ${port}
    Run Command  ${RXDEBUG} ${host} ${port} -version

Cell Should Be
    [Arguments]  ${cellname}
    ${cmd}=  Set Variable  ${FS} wscell
    ${rc}  ${output}  Run And Return Rc And Output    ${cmd}
    Should Be Equal As Integers  ${rc}  0
    ...  msg=Failed: ${cmd}, rc=${rc}, ${output}
    ...  values=False
    Should Match  ${output}  This workstation belongs to cell '${cellname}'
    ...  msg=Client has the wrong cell name!

Create Volume
    [Arguments]  ${server}  ${part}  ${name}
    Run Command  ${VOS} create -server ${server} -partition ${part} -name ${name} -m 0 -verbose
    # todo: return the volume id!

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
    [Arguments]     ${server}  ${part}  ${volume}
    Run Command     ${VOS} addsite -server ${server} -part ${part} -id ${volume}
    Release Volume  ${volume}
    Run Command     ${FS} checkvolumes

Remove Replica
    [Arguments]  ${server}  ${part}  ${name}
    Run Command  ${VOS} remove -server ${server} -part ${part} -id ${name}.readonly

Release Volume
    [Arguments]    ${volume}
    Run Command    ${VOS} release -id ${volume} -verbose
    Run Command    ${FS} checkvolumes

Create and Mount Volume
    [Documentation]  Helper keyword to create and mount a readable volume.
    [Arguments]  ${server}  ${part}  ${name}  ${dir}
    Run Command        ${VOS} create -server ${server} -partition ${part} -name ${name} -verbose
    Mount Volume       ${dir}  ${name}
    Add Access Rights  ${dir}  system:anyuser  read

