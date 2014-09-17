*** Setting ***
Resource       keywords/utility.robot
Variables      variables/suse/paths.py

*** Keywords ***
set client configuration
    [documentation]    Copy the cell config from the server directories.
    sudo    cp ${AFS_SERVER_ETC_DIR}/CellServDB ${AFS_CLIENT_ETC_DIR}/CellServDB
    sudo    cp ${AFS_SERVER_ETC_DIR}/ThisCell ${AFS_CLIENT_ETC_DIR}/ThisCell

start the overseer server
    Sudo    /sbin/service openafs-server start

start client
    sudo    /sbin/service openafs-client start

