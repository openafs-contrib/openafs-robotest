*** Setting ***
Library    OperatingSystem


*** Keywords ***
set kerberos realm
    [arguments]    ${realm}
    file should not exist    /usr/afs/etc/krb.conf
    create file    /tmp/krb.conf    ${realm}
    sudo    cp /tmp/krb.conf /usr/afs/etc/krb.conf
    run    rm /tmp/krb.conf

should not have kerberos tickets
    ${rc}    ${output}    run and return rc and output    klist
    log    ${output}
    should be equal as integers  ${rc}  1

Should have kerberos tickets
    ${rc}    ${output}    run and return rc and output    klist
    log    ${output}
    should be equal as integers  ${rc}  0

