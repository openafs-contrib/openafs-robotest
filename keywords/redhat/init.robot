*** Setting ***
Resource       keywords/utility.robot
Variables      variables/redhat/pathes.py

*** Keywords ***
set client configuration
    [documentation]    Copy the cell config from the server directories.
    sudo    cp ${AFS_SERVER_ETC_DIR}/CellServDB ${AFS_CLIENT_ETC_DIR}/CellServDB
    sudo    cp ${AFS_SERVER_ETC_DIR}/ThisCell ${AFS_CLIENT_ETC_DIR}/ThisCell
    sudo    cp ${AFS_SERVER_ETC_DIR}/CellServDB ${AFS_CLIENT_ETC_DIR}/CellServDB.local

start the overseer server
    Sudo    service openafs-server start

start client
    sudo    service openafs-client start

