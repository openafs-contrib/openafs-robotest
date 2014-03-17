
OpenAFS Robo Test
=================

This is a Robot Framework based test-suite for OpenAFS. This initial version is
a limited, basic smoke test of a single host OpenAFS server and client.  This
test will install the OpenAFS client and server binaries and setup a simple
test cell.  The following files are needed to run the test:

* OpenAFS RPM files
* Kerberos keytab files containing the AFS service key(s) and user keys

The results of the tests are a set of html files indicating pass or fail
status.


System Requirements
===================

* a Kerberos 5 realm
* RHEL/CentOS 6 Linux
* Python 2.6.x
* Robot Framework 2.7+
* Kerberos client utilities (kinit, kdestroy, klist, kvno)
* Clock synchronization (required by Kerberos)


Kerberos Setup
==============

A working Kerberos 5 realm is required. This test harness has been developed
with MIT Kerberos, but other implementations (Active Directory, Heimdal) should
work as well.  If a realm is not available for testing, a test KDC server may
be installed directly on the system under test. See one of the many Kerberos
installation guides available.

A Kerberos administrator must create following keytab files:

 * rxkad.keytab     - AFS service key(s), not DES
 * afs.keytab       - AFS service key, DES (for testing old versions)
 * robotest.keytab  - test user keys

The 'rxkad.keytab' should contain one or more non-DES keys for the service
principal

    afs/<cellname>@<REALM>

where <cellname> is the name of the test cell to be created by the test suite
and <REALM> is the name of the test realm.

The 'afs.keytab' is required to test older OpenAFS versions which only support
DES, otherwise it is not needed. As of OpenAFS 1.6.5 (1.4.15), DES service keys
are deprecated.  The name of the service principal should be,

    afs/<another.cellname>@<REALM>

where <another.cellname> is the name of the test cell to be created by the test
suite, and should be a different name than the <cellname> used for the service
keys in the rxkad.keyfile.  The key should be single DES, with the afs3 salt,
or v4 salt, that is enctype 'des-cbc-crc:afs3'.

The 'robotest.keytab' should contain the keys for an AFS administrative user
and a regular user. The principals should be named:

    robotest/admin@<REALM>
    robotest@<REALM>

Edit the openafs-robotest config.py file if different user names are chosen.


See "Appendix A: Creating Keytabs, MIT Kerberos 5" for commands to create the
principals and keytab files.


RHEL/CentOS Setup
=================

1. Setup the EPEL package repository.

Required python packages are available in the EPEL yum repository. Check
the available repositories with the command:

    $ yum repolist

If the 'epel' repository is not listed, then configure yum to use the EPEL
repository. See http://fedoraproject.org/wiki/EPEL for information about the
EPEL repository.


2. Install and time server to keep the system clock in sync.

An accurate system clock is required for Kerberos operation, as well as
meaningful test result logs. If a mechanism is not already in place to
synchronize the system clock, then install and start the NTP time service.

Run the following commands to install the NTP time service:

     $ sudo yum -y install ntp ntpdate
     $ sudo chkconfig ntpd on
     $ sudo ntpdate pool.ntp.org
     $ sudo service ntpd start


3. Install the Kerberos client programs.

     $ sudo yum -y install krb5-workstation

Configure the /etc/krb5.conf for the test realm to be used.
For example, if DNS records are not used for the test realm:

    [libdefaults]
        default_realm = <REALM>
        dns_lookup_realm = false
        dns_lookup_kdc = false

        # required for OpenAFS, before v1.6.5
        allow_weak_crypto = true

    [realms]
        LOCALREALM = {
            kdc = <hostname>
            admin_server = <hostname>
        }

where <REALM> is the name of the test realm, and <hostname> is
the hostname of the KDC.


4. Install python packages.

Install the python package installer and docutils packages.

     $ sudo yum -y install python-pip python-docutils


5. Install Robot framework (global)

Use the python pip installer to install the Robot Framework. Alternatively, to
avoid a global installation, see "Appendix B: Installing Robot Framework with
virtualenv".

     $ sudo pip install robotframework

     $ pybot --version
     Robot Framework 2.8.1 (Python 2.6.6 on linux2)


6. Setup a regular user to run the tests.

The test suite is designed to be run under a regular user account. This user
should have limited sudo access in order to complete the installation portion
of the test suite.

Any valid username can be used.  In the following example instructions, the
user is called 'robotest'.

    $ sudo useradd --create-home robotest

Add the following to the end of the sudoers file.

    $ sudo visudo

    # OpenAFS test automation
    Cmnd_Alias AFSINSTALL = /bin/rpm, /sbin/service, \
                            /bin/cp * /usr/afs/etc/*, /bin/cp * /usr/vice/etc/*, \
                            /usr/sbin/asetkey
    Cmnd_Alias AFSADMIN = /usr/bin/bos, /usr/sbin/vos, /usr/bin/pts
    robotest ALL = (root) NOPASSWD: AFSINSTALL, AFSADMIN


7. Create a directory to display the test results.

Create a directory to display the test results which is writable by the
robotest user and is readable by a web server.  For example:

    $ sudo mkdir /var/www/html/robotest
    $ sudo chown robotest /var/www/html/robotest

After a test is run, the results should then be available under;

    http://<hostname>/robotest/


8. OpenAFS RPM files.

Create or find a location for the OpenAFS RPM files.  The RPM files can be
located in a local directory, a network directory (but not AFS), or served over
http (or ftp).

9. File server data partition

Create at least one disk partition and mount it as /vicepa for the test fileserver.

Alternatively, create a directory called /vicepa and a file in it called
AlwaysAttach.

    $ sudo mkdir /vicepa
    $ sudo touch /vicepa/AlwaysAttach


Installation
============

This installation is to be performed under the regular user
account which is to run the tests.  Root access is not required.


1. Login as the 'robotest' user.

    $ sudo su - robotest


2. [Optional] Install of Robot Framework (local)

If the Robot Framework has not been globally installed or a local installation
is perferred, see "Appendix B: Installing Robot Framework with virtualenv".


3. Install openafs-robotest.

    $ git clone git://scm.devlab.sinenomine.net/sna-openafs-robotest.git
    $ cd sna-openafs-robotest
    $ git checkout -b smoke-test origin/smoke-test


4. Install the keytab files.

If the keytab files have already been created by the Kerberos administrator,
copy them into the 'keytabs' directory.  Alternatively, if you have a Kerberos
principal with administrative privileges, then run kadmin directly in the
'keytabs' directory.

See "Appendix A: Creating Keytabs, MIT Kerberos 5" for commands to create the
principals and keytab files.


5. [Optional] Configure openafs-robotest.

Copy the example settings file and set specific values for your
site.

    $ cp settings.example settings
    $ settings

The settings file may be used to specify arguments commonly needed for the
run-tests.sh front-end script.  Command line arguments given to run-tests.sh
override the values in the settings file, if present.


Running Tests
=============

1. Login as the 'robotest' user.

    $ sudo su - robotest

2. Change to the openafs-robotest directory.

    $ cd sna-openafs-robotest

3. Run the tests.

    $ ./run-tests.sh <options>

See ./run-tests.sh --help for a list of options.

Example:

    $ ./run-test.sh --afsversion 1.6.5


Appendix A: Creating Keytabs, MIT Kerberos 5
============================================

Use kadmin to create the principals and keytab files.

Example:

    $ kadmin -r <REALM> -p <principal>
    (enter admin's password)

    kadmin: addprinc -randkey robotest
    kadmin: addprinc -randkey robotest/admin
    kadmin: addprinc -randkey afs/robotest
    kadmin: addprinc -randkey afs/robotest.des

    kadmin: ktadd -k robotest.keytab robotest
    kadmin: ktadd -k robotest.keytab robotest/admin
    kadmin: ktadd -k rxkad.keytab -e aes256-cts-hmac-sha1-96:normal afs/robotest
    kadmin: ktadd -k afs.keytab -e des-cbc-crc:afs3 afs/robotest.des

    kadmin: quit

Where <REALM> is the name of the test realm, and <principal> is a principal
with Kerberos admin privileges.


Appendix B: Installing Robot Framework with virtualenv
======================================================

Robot Framework is available as a python package.  The recommended method for
installing python packages is to install the package in a python 'virtualenv'
isolation environment, instead of a global installation. This prevents
conflicts as other packages are installed, upgraded, and removed from the
system.

1. Install the python virtualenv tool. This is available as a yum package
in the EPEL repository.

    $ sudo yum -y install python-virtualenv

2. Login as the robotest user.

    $ sudo su - robotest

3. Create the virtualenv directory for Robot Framework.

Create the virtualenv directory in the robotest user home directory
and install the Robot Framework package.

    $ virtualenv --no-site-packages robotframework
    $ . robotframework/bin/activate
    (robotframework) $ pip install robotframework
    ...
    Successfully installed robotframework

Check Robot Framework is correctly installed by running the pybot command.

    (robotframework) $ pybot --version
    Robot Framework 2.8.1 (Python 2.6.6 on linux2)

    (robotframework) $ which pybot
    ~/robotframework/bin/pybot

Deactivate the virtualenv until the rest of the setup has been completed.

    (robotframework) $ deactivate
    $

Before running the openafs-robotest, activate the virtualenv.

    $ cd ~/sna-openafs-robotest
    $ . ~/robotframework/bin/activate
    (robotframework) $ ./run-test.sh <options>

