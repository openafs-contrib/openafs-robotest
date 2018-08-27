

# Setting up a Kerberos Realm on RHEL/CentOS

Install the kerberos server with:

    # yum install krb5-server krb5-workstation krb5-libs

Edit the /etc/krb5.conf and /var/kerberos/krb5kdc/kdc.conf configuration
files to set the realm name and server names.

Create the kerberos database with the kerberos database utility:

    # kdb5_util create -s

Create the first principal.

    # kadmin.local -q 'addprinc <username>/admin'

Start the servers:

    # systemctl start krb5kdc.service
    # systemctl start kadmin.service


