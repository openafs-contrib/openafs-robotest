*** Setting ***
Library        OperatingSystem
Library        libraries/Kerberos.py
Resource       keywords/utility.robot

*** Keywords ***
afs service keytab should exist
    file should exist    ${KRB_RXKAD_KEYTAB}

afs service key should exist
    file should exist    /usr/afs/etc/rxkad.keytab

afs service key should not exist
    file should not exist    /usr/afs/etc/rxkad.keytab

import afs service key
    sudo    cp ${KRB_RXKAD_KEYTAB} /usr/afs/etc/rxkad.keytab
