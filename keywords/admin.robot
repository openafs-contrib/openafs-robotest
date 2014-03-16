*** Setting ***
Library        OperatingSystem
Library        String
Library        libraries/Kerberos.py
Resource       keywords/utility.robot
Variables      variables/${ENV_DIST}/commands.py

*** Keywords ***
server is alive
    [arguments]    ${port}
    run command    ${AFS_RXDEBUG} ${AFS_HOST} ${port} -version

servers are not running
    overseer server is not running
    fileserver is not running
    volume location server is not running
    protection server is not running

overseer server is running
    wait until keyword succeeds    1 min    1 sec    program is running    bosserver
    wait until keyword succeeds    1 min    1 sec    server is alive    7007

overseer server is not running
    program is not running    bosserver

volume location server is running
    wait until keyword succeeds    1 min    1 sec    program is running    vlserver
    wait until keyword succeeds    1 min    1 sec    server is alive    7003

volume location server is not running
    program is not running    vlserver

protection server is running
    wait until keyword succeeds    1 min    1 sec    program is running    ptserver
    wait until keyword succeeds    1 min    1 sec    server is alive    7002

protection server is not running
    program is not running    ptserver

cell name is
    [arguments]    ${cellname}
    ${output}    run    ${AFS_BOS} listhosts -server ${AFS_HOST} -noauth
    should contain    ${output}    Cell name is ${cellname}

set cell name
    [arguments]    ${cellname}
    sudo    ${AFS_BOS} setcell -server ${AFS_HOST} -name ${cellname} -localauth

create protection server
    sudo    ${AFS_BOS} create ${AFS_HOST} ptserver simple /usr/afs/bin/ptserver -localauth
    wait until keyword succeeds    1 min    1 sec    server is alive    7002
    wait until keyword succeeds    1 min    1 sec    database has quorum    7002

create volume location server
    sudo    ${AFS_BOS} create ${AFS_HOST} vlserver simple /usr/afs/bin/vlserver -localauth
    wait until keyword succeeds    1 min    1 sec    server is alive    7003
    wait until keyword succeeds    1 min    1 sec    database has quorum    7003

database has quorum
    [arguments]    ${port}
    ${output}    run    ${AFS_UDEBUG} localhost ${port}
    should contain    ${output}    Recovery state 1f

superuser exists
    [arguments]    ${superuser}
    ${rc}    ${output}    run and return rc and output    sudo -n ${AFS_PTS} examine ${superuser} -localauth
    should be equal as integers    ${rc}    0
    should contain    ${output}    Name: ${superuser}

superuser does not exist
    [arguments]    ${superuser}
    ${rc}    ${output}    run and return rc and output    sudo -n ${AFS_PTS} examine ${superuser} -localauth
    should be equal as integers    ${rc}    1
    should contain    ${output}    pts: User or group doesn't exist

create superuser
    [arguments]    ${superuser}
    sudo    ${AFS_PTS} createuser ${superuser} -localauth
    sudo    ${AFS_PTS} adduser ${superuser} system:administrators -localauth
    sudo    ${AFS_BOS} adduser ${AFS_HOST} ${superuser} -localauth

volume does not exist
    [arguments]    ${volume}
    ${rc}    ${output}    run and return rc and output    ${AFS_VOS} listvldb -name ${volume}
    should be equal as integers    ${rc}    1
    should contain    ${output}    VLDB: no such entry

volume exists
    [arguments]    ${volume}
    ${rc}    ${output}    run and return rc and output    ${AFS_VOS} listvldb -name ${volume}
    should be equal as integers    ${rc}    0
    should not contain    ${output}    VLDB: no such entry
    should contain    ${output}    ${volume}

create volume as root
    [arguments]    ${volume}
    sudo    ${AFS_VOS} create ${AFS_HOST} a ${volume} -verbose -localauth

create volume
    [arguments]    ${volume}
    Run command    ${AFS_VOS} create ${AFS_HOST} a ${volume} -verbose

mount volume
    [arguments]  ${dir}  ${vol}
    run command    ${AFS_FS} mkmount -dir ${dir} -vol ${vol}

mount read-write volume
    [arguments]  ${dir}  ${vol}
    run command    ${AFS_FS} mkmount -dir ${dir} -vol ${vol} -rw

cellular mount
    [arguments]  ${dir}  ${vol}  ${cell}
    run command    ${AFS_FS} mkmount -dir ${dir} -vol ${vol} -cell ${cell}

cellular read-write mount
    [arguments]  ${dir}  ${vol}  ${cell}
    run command    ${AFS_FS} mkmount -dir ${dir} -vol ${vol} -cell ${cell} -rw

unmount volume
    [arguments]  ${dir}  ${vol}
    run command    ${AFS_FS} rmmount -dir ${dir}

clear access rights
    [arguments]  ${dir}
    run command    ${AFS_FS} setacl -dir ${dir} -acl system:anyuser none -clear

add access rights
    [arguments]  ${dir}    ${group}    ${rights}
    run command    ${AFS_FS} setacl -dir ${dir} -acl ${group} ${rights}

replicate volume
    [arguments]    ${volume}
    run command    ${AFS_VOS} addsite ${AFS_HOST} a ${volume}
    run command    ${AFS_VOS} release ${volume} -verbose

client is running
    run command    mount
    should exist   /afs/${AFS_CELL}
    server is alive    7001

client is not running
    run command    mount
    should not exist   /afs/${AFS_CELL}

not logged in as admin
    ${rc}    ${output}    run and return rc and output  ${AFS_TOKENS}
    log  ${output}
    should be equal as integers  ${rc}  0
    should not contain    ${output}    User's (AFS ID 1)

log in as admin
    ${name}=    replace string    ${AFS_SUPERUSER}    .    /
    run command    kinit -k -t ${KRB_USER_KEYTAB} ${name}@${KRB_REALM}
    run command    ${AFS_AKLOG} -d -c ${AFS_CELL} -k ${KRB_REALM}

logged in as admin
    ${rc}  ${output}  run and return rc and output  ${AFS_TOKENS}
    log  ${output}
    should be equal as integers  ${rc}  0
    should contain  ${output}  User's (AFS ID 1)

