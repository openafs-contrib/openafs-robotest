OpenAFS RoboTest
================

OpenAFS RoboTest is a [Robot Framework][1] based test suite for OpenAFS. This
initial version is a limited test suite for an OpenAFS server and client on a
single test system.  RoboTest will install the OpenAFS binaries, setup a simple
test cell, then run a series of basic tests.  A test feature of OpenAFS is used
to mimic a Kerberos server, allowing the tests to be run without the need to
setup a Kerberos realm and create keytabs.

[1]: http://robotframework.org/

Requirements
============

* Linux or Solaris
* Python 2.6.x
* Robot Framework 2.7 or better
* OpenAFS installation packages or binaries built from source


Installation
============

This test harness is designed to be run on a dedicated test system.
Typically you will want to setup a virtual machine to run the
tests.

1. Install Robot Framework

Robot Framework can be installed using the Python `pip` command:

    $ sudo pip install robotframework

See http://robotframework.org/ for more details.

2. Install OpenAFS RoboTest.

Clone to a directory of your choice.

    $ git clone https://github.com/openafs-contrib/openafs-robotest.git
    $ cd openafs-robotest

3. Setup sudo.

The tests are designed to be run by a non-root user, however RoboTest
will install OpenAFS and setup a test cell, which requires root access.
The commands which require root-access are run as sudo with the NOPASSWD
option. Setup the sudo to allow NOPASSWD for the user which runs the
tests.


Setup
=====

A console based setup tool is provided to assist in setting up the
test harness.

    $ ./run.py setup
    OpenAFS RoboTest Setup
    Type help for information.
    
    (setup) help
    Commands. Type help <command> for syntax
    ============================================================
    call      Execute commands in a file.
    genkey    Add a kerberos principal then write the keys to a keytab file.
    gensudo   Generate the sudo permissions check script.
    getrpms   Download RPM files.
    help      Display command help.
    list      List setting names and values.
    makepart  Create a fake fileserver partition.
    quit      Quit this program.
    reset     Reset all settings to default values.
    set       Assign a setting value.
    shell     Run a command using the shell.

The `makepart` command will create "pseudo" partitions for the file server
(that is, directories in the root filesystem, with the "AlwaysAttach" file
present.)

    (setup) makepart a

Set the `AFS_DIST` variable to select the distribution type to be tested.  The
distribution types currently supported are:

* `rhel6`    -- RHEL6/Centos6 rpm installation
* `suse`     -- OpenSUSE rpm installation
* `transarc` -- legacy mode installation

Set the `AFS_DIST` variable using the set subcommand:

    (setup) set AFS_DIST <type>

For the `rhel6` or `suse` types, use the `genrpms` command to download rpm
files from OpenAFS.org, or set the following variables to specify the packages
to be installed when the test harness runs:

    (setup) set RPM_PACKAGE_DIR  <path-to-rpm-files>
    (setup) set RPM_AFSRELEASE   <rpm-release>
    (setup) set RPM_AFSVERSION   <open-afs-version>

To configure RoboTest to use traditional Transarc-style binaries, set
`AFS_DIST` to `transarc` and then set the path to the Transarc-style `dist`
directory.

    (setup) set TRANSARC_DEST  <path-to-dest-directory>


Sudo Setup
==========

The test harness should be run as a normal user, but the installation and
removal of OpenAFS requires root access. All commands within the test harness
which require root access use sudo to invoke a script. This script permits only
commands needed for OpenAFS installation and and removal.

First, run the `gensudo` setup command to generate the commands permitted
based on the current settings.

    $ ./run.py setup
    (setup) gensudo
    (setup) quit

This will generate a script in the `tools` directory called `afs-robotest-sudo`.
Copy this generated file to `/usr/sbin/afs-robotest-sudo`.

    sudo cp tools/afs-robotest-sudo /usr/sbin/

Next, add the following line to your sudoers configuration, using `sudo visudo`:

    ALL ALL = (root) NOPASSWD: /usr/sbin/afs-robotest-sudo


Running Tests
=============

To run the tests, change to the openafs-robotest top level directory, and run the
the run.py command:

    $ cd openafs-robotest
    $ ./run.py tests


Publishing Results
==================

The test results are saved in the `output` directory by default. (See the
RF_OUTPUT setting.)

To view the test report and log, setup a webserver to serve the files in the
`output` directory, or use the built-in webserver tool provided by RoboTest.

    $ ./run.py webserver

The results are then available under http://<hostname>:8000

