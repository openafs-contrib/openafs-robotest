*** Setting ***
Library        OperatingSystem
Library        String
Library        libraries/Kerberos.py
Resource       keywords/utility.robot
Variables      variables/${ENV_DIST}/commands.py

*** Keywords ***
fileserver is running
    program is running    fileserver
    program is running    volserver
    server is alive    7000
    server is alive    7003

fileserver is not running
    program is not running    fileserver
    program is not running    volserver

create fileserver
    sudo    ${AFS_BOS} create ${AFS_HOST} fs fs /usr/afs/bin/fileserver /usr/afs/bin/volserver /usr/afs/bin/salvager -localauth
    wait until keyword succeeds    1 min    5 sec    fileserver is running

