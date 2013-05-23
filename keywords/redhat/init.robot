*** Setting ***
Resource       keywords/utility.robot

*** Keywords ***
set client configuration
    [documentation]    Copy the cell config from the server directories.
    sudo    cp /usr/afs/etc/CellServDB /usr/vice/etc/CellServDB
    sudo    cp /usr/afs/etc/ThisCell /usr/vice/etc/ThisCell
    sudo    cp /usr/afs/etc/CellServDB /usr/vice/etc/CellServDB.local

start the overseer server
    Sudo    service openafs-server start

start client
    sudo    service openafs-client start

