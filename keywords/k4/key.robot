*** Setting ***
Library        OperatingSystem
Library        libraries/Kerberos.py
Resource       keywords/utility.robot
Variables      variables/${ENV_DIST}/pathes.py

*** Keywords ***
afs service keytab should exist
    file should exist    ${KRB_AFS_KEYTAB}

afs service key should exist
    file should exist    ${AFS_SERVER_ETC_DIR}/KeyFile

afs service key should not exist
    file should not exist    ${AFS_SERVER_ETC_DIR}/KeyFile

import afs service key
    ${kvno}    read des kvno    ${KRB_AFS_KEYTAB}    ${AFS_CELL}    ${KRB_REALM}
    sleep    2s    so cell configuration reloads when asetkey touches CellServDB
    sudo    ${AFS_ASETKEY} add ${kvno} ${KRB_AFS_KEYTAB} afs/${AFS_CELL}@${KRB_REALM}

