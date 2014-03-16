Cell client setup
-----------------

Create the AFS client setup of a basic cell on a single host. Start
up the client and log in as the admin superuser. Mount the top level
volumes and set the access rights.  After this test suite completes,
the cell has been configured for non-admin users to access the AFS
filespace for this cell.

*** Setting ***
DefaultTags    smoke
Library    OperatingSystem
Resource   keywords/utility.robot
Resource   keywords/admin.robot
Resource   keywords/${ENV_DIST}/init.robot

*** Test Case ***
client configuration
    set client configuration

start client
    given client is not running
    when start client
    then client is running

admin login
    given not logged in as admin
    when log in as admin
    then logged in as admin

mount cell volume
    given client is running
    and logged in as admin
    and directory should exist         /afs/.:mount
    and directory should not exist     /afs/.:mount/${AFS_CELL}:root.afs/${AFS_CELL}
    when cellular mount                /afs/.:mount/${AFS_CELL}:root.afs/${AFS_CELL}     root.cell    ${AFS_CELL}
    and cellular read-write mount      /afs/.:mount/${AFS_CELL}:root.afs/.${AFS_CELL}    root.cell    ${AFS_CELL}
    then directory should exist        /afs/.:mount/${AFS_CELL}:root.afs/${AFS_CELL}
    and directory should exist         /afs/.:mount/${AFS_CELL}:root.afs/.${AFS_CELL}

make root volumes readable
    add access rights    /afs/.:mount/${AFS_CELL}:root.afs/.    system:anyuser    read
    add access rights    /afs/.:mount/${AFS_CELL}:root.cell/.    system:anyuser    read

replicate root volumes
    replicate volume    root.afs
    replicate volume    root.cell

create test volume
    logged in as admin
    create volume    test
    mount volume    /afs/${AFS_CELL}/test    test
    add access rights    /afs/${AFS_CELL}/test    system:anyuser    read
    create file    /afs/${AFS_CELL}/test/hello    Hello world!\n
