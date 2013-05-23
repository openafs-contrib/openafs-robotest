*** Setting ***
Library        OperatingSystem
Library        String
Library        libraries/Kerberos.py
Resource       keywords/utility.robot
Variables      variables/${ENV_DIST}/commands.py

*** Keywords ***
fileserver is running
    program is running    dafileserver
    program is running    davolserver
    program is running    salvageserver
    server is alive    7000
    server is alive    7003

fileserver is not running
    program is not running    dafileserver
    program is not running    davolserver
    program is not running    salvageserver

create fileserver
    ${fs}    set variable    -cmd "/usr/afs/bin/dafileserver"
    ${vs}    set variable    -cmd "/usr/afs/bin/davolserver"
    ${ss}    set variable    -cmd "/usr/afs/bin/salvageserver"
    ${s}     set variable    -cmd "/usr/afs/bin/salvager"
    sudo    ${AFS_BOS} create ${AFS_HOST} dafs dafs ${fs} ${vs} ${ss} ${s} -localauth
    wait until keyword succeeds    1 min    5 sec    fileserver is running

