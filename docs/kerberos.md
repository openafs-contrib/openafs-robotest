
# Set up a Kerberos Realm on RHEL/CentOS

Install the kerberos server with:

    # yum install krb5-server krb5-workstation krb5-libs

Edit the /etc/krb5.conf and /var/kerberos/krb5kdc/kdc.conf configuration
files to set the realm name and server names.

Create the kerberos database with the kerberos database utility:

    # kdb5_util create -s

Create the admin user:

    # kadmin.local -q 'addprinc <username>/admin'

Start the servers:

    # systemctl start krb5kdc.service
    # systemctl start kadmin.service

Verify the KDC can issue tickets for the admin user:

    $ kinit <username>/admin
    $ klist
    $ kdestroy

# Create the test cell keys

Create the directory for the keytabs:

    $ mkdir -p ~/afsrobot/keytabs
    $ cd ~/afsrobot/keytabs

Start the kadmin client as a kerberos administrator:

    $ kinit afsrobot/admin@EXAMPLE.COM
    $ kadmin

Create the service key for the test cell:

    kadmin: addprinc -randkey afs/example.com
    kadmin: ktadd -k afs.keytab -e aes256-cts-hmac-sha1-96:normal afs/example.com

Create the user principals for the test cell:

    kadmin: addprinc -randkey afsrobot
    kadmin: addprinc -randkey afsrobot/admin
    kadmin: ktadd -k user.keytab afsrobot
    kadmin: ktadd -k user.keytab afsrobot/admin
    kadmin: quit
    $ kdestroy
