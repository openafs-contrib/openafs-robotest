*** Setting ***
Library        OperatingSystem
Library        libraries/Kerberos.py
Resource       keywords/utility.robot

*** Keywords ***
afs service keytab should exist
    file should exist    ${KRB_AFS_KEYTAB}

afs service key should exist
    file should exist    /usr/afs/etc/KeyFile

afs service key should not exist
    file should not exist    /usr/afs/etc/KeyFile

import afs service key
    ${kvno}    read des kvno    ${KRB_AFS_KEYTAB}    ${AFS_CELL}    ${KRB_REALM}
    sleep    2s    so cell configuration reloads when asetkey touches CellServDB
    sudo    ${AFS_ASETKEY} add ${kvno} ${KRB_AFS_KEYTAB} afs/${AFS_CELL}@${KRB_REALM}

