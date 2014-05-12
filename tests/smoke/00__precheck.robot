Precheck
--------

Verify AFS is currently not installed and the system is ready to begin the
smoke test.  This test suite does not make changes to the system.

*** Setting ***
DefaultTags    precheck
Library    OperatingSystem
Library    libraries/Kerberos.py
Resource     keywords/utility.robot
Resource     keywords/kerberos.robot
Resource     keywords/${ENV_KEY}/key.robot

*** Test Case ***
afs should not be mounted
    ${mount}              Run         mount
    should not contain    ${mount}    AFS on /afs

afs kernel module should not be loaded
    ${modules}    get file    /proc/modules
    should not contain    ${modules}    openafs
    should not contain    ${modules}    libafs

afs directories should not exist
    directory should not exist    /afs
    directory should not exist    /usr/afs
    directory should not exist    /usr/vice/etc

empty afs vice partition should exist
    directory should exist    /vicepa
    directory should not exist    /vicepa/AFSIDat
    file should exist    /vicepa/AlwaysAttach

afs sysconfig should not exist
    file should not exist    /etc/sysconfig/openafs

kerberos keytab check
    file should exist    ${KRB_USER_KEYTAB}
    afs service keytab should exist

kerberos ticket check
    should not have kerberos tickets
    run command    kinit -k -t ${KRB_USER_KEYTAB} ${AFS_TESTUSER}@${KRB_REALM}
    should have kerberos tickets
    run command    kdestroy
    should not have kerberos tickets


