Cell server setup
-----------------

Create the AFS server setup of a basic cell on a single host.  After this test
suite runs, the server side setup is complete and a client can be started and a
user can log in as the admin user to create volumes and mount volumes.


*** Setting ***
DefaultTags    smoke
Library        OperatingSystem
Library        libraries/Kerberos.py
Resource       keywords/utility.robot
Resource       keywords/admin.robot
Resource       keywords/${ENV_FS}/admin.robot
Resource       keywords/${ENV_DIST}/init.robot
Resource       keywords/kerberos.robot
Resource       keywords/${ENV_KEY}/key.robot

*** Test Case ***
initial server startup
    given servers are not running
    when start the overseer server
    then overseer server is running
    and fileserver is not running
    and volume location server is not running
    and protection server is not running

kerberos realm setup
    set kerberos realm    ${KRB_REALM}

service key import
    given afs service key should not exist
    when import afs service key
    then afs service key should exist

cell naming
    given cell name is    localcell
    when set cell name    ${AFS_CELL}
    then cell name is    ${AFS_CELL}

protection database creation
    given protection server is not running
    when create protection server
    then protection server is running

volume location database creation
    given volume location server is not running
    when create volume location server
    then volume location server is running

admin account creation
    given superuser does not exist    ${AFS_SUPERUSER}
    when create superuser    ${AFS_SUPERUSER}
    then superuser exists    ${AFS_SUPERUSER}

fileserver creation
    given fileserver is not running
    when create fileserver
    then fileserver is running

afs root volume creation
    given volume does not exist    root.afs
    when create volume as root   root.afs
    then volume exists    root.afs

cell root volume creation
    given volume does not exist    root.cell
    when create volume as root    root.cell
    then volume exists    root.cell

