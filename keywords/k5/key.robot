*** Setting ***
Library        OperatingSystem
Library        libraries/Kerberos.py
Resource       keywords/utility.robot
Variables      variables/${ENV_DIST}/pathes.py

*** Keywords ***
afs service keytab should exist
    file should exist    ${KRB_RXKAD_KEYTAB}

afs service key should exist
    file should exist    ${AFS_SERVER_ETC_DIR}/rxkad.keytab

afs service key should not exist
    file should not exist    ${AFS_SERVER_ETC_DIR}/rxkad.keytab

import afs service key
    sudo    cp ${KRB_RXKAD_KEYTAB} ${AFS_SERVER_ETC_DIR}/rxkad.keytab
