# AFS Robotest

AFS Robotest is a [Robotframework][1] based test suite for OpenAFS. The test
suite will install the OpenAFS binaries, setup a simple test cell, and then run
a series of basic tests.  Optionally, a test feature of OpenAFS is used to
emulate a Kerberos server, allowing the tests to be run without the need to
setup a Kerberos realm and create keytabs.

[1]: http://robotframework.org/

## System Requirements

* Linux or Solaris
* Python 2.6, 2.7
* Robot Framework 2.7+
* OpenAFS installation packages or binaries built from source

## Installation

This test suite should be run on a dedicated test system.  Typically, you will
want to setup one or more virtual machines to install OpenAFS and the test
suite.  If `afs-robotest` is used to install OpenAFS then sudo should be
configured on the test machine. The NOPASSWD sudo option must be set to allow
the command `afsutil` to be run with sudo without a password.

Python 2.6 or 2.7 must be present. Install the `python-pip` package using your
system's package manager. On Debian based systems, this is done with the
command:

    $ sudo apt-get install python-pip

On Centos, `pip` may be installed from the `python-pip` package in the EPEL
repo:

    $ sudo yum install python-pip

Install the `Robotframework` and `argparse` Python packages using the `pip'
command:

    $ sudo pip install robotframework argparse

Clone the OpenAFS Robotest project to a directory of your choice:

    $ cd ${projects}
    $ git clone https://github.com/openafs-contrib/openafs-robotest.git
    $ cd openafs-robotest

Install the custom python packages and scripts provided by openafs-robotest:

    $ ./install.sh

## Setup

Run the `afs-robotest` tool to set the configuration before running the setup
and tests.  The default configuration file name is `afs-robotest.conf`.

First, set the following environment variable in your shell profile:

    AFS_ROBOTEST_PROFILE=${HOME}/afs-robotest.conf
    export AFS_ROBOTEST_PROFILE

This environment variable sets the default path to the configuration file,
making it easier to run `afs-robotest` from any directory.

To show the current configuration:

    $ afs-robotest config list

To configure robotest to install Transarc-style binaries:

    $ afs-robotest config set host:localhost installer transarc
    $ afs-robotest config set host:localhost dest <path-to-dest-directory>

The `akimpersonate` feature of `aklog` is used to create AFS tokens by
accessing the service keytab directly, without the need for a Kerberos realm.
This is configured by setting `akimpersonate` to `yes` in the `kerberos`
section of the configuration.

Note: Unfortunately, the `akimpersonate` feature may not be functional in
developement releases of OpenAFS (the master branch).  For testing development
releases, either use a Kerberos realm or provide a 1.6.x version of `aklog`.
Set the `aklog` option in the `variables` section of the configuration file to
specify which `aklog` program is to be used during the tests. For example:

    $ afs-robotest config set variables aklog /usr/local/bin/aklog-1.6

Note: Unfortunately, the OpenAFS client init script still uses the deprecated
`ifconfig` command, which is no longer installed by default on RHEL 7 (and
Centos 7). Be sure to install the net-tools package until this is fixed.

    $ sudo yum install net-tools


## Running tests

To install the OpenAFS binaries and create the test cell:

    $ afs-robotest setup

To run the tests:

    $ afs-robotest run

After running the tests, the AFS cell can be removed with the teardown
command:

    $ afs-robotest teardown

The `auto_setup` and `auto_teardown` configuration options can be set to `yes`
to automatically run the setup and teardown.

## Test results

The setup logs and test results are saved in the `html` directory.  A minimal
web server is provided as a convenience to view the test reports.

To start the minimal web server:

    $ afs-robotest web start

To stop the minimal web server:

    $ afs-robotest web stop

## Multiple Servers

This test harness supports setting up multiple file and database servers.
Install `openafs-robotest` on each server, as described above.  `sudo` must be
configured with NOPASSWD for the test user account on each host.

A configuration section must be added for each test server. The name of the
test section is `[host:<hostname>]`, in addition to the `[host:localhost]` for
the "primary" server.  For example:

    [host:localhost]
    installer = transarc
    isfileserver = yes
    isdbserver = yes
    isclient = yes
    dest = /usr/local/src/openafs-test/amd64_linux26/dest
    nuke = no
    setclock = no

    [host:mytesta]
    installer = transarc
    isfileserver = yes
    isdbserver = no
    isclient = yes
    dest = /usr/local/src/openafs-test/amd64_linux26/dest
    nuke = no
    setclock = yes

    [host:mytestb]
    installer = transarc
    isfileserver = yes
    isdbserver = no
    isclient = no
    dest = /home/mmeffie/src/openafs/amd64_linux26/dest
    nuke = no
    setclock = no

The OpenAFS installation and setup is done using ssh with keyfiles. The
`sshkeys` helper command is provided to create an ssh key pair and distribute
the public keys to each test servers.  Run the following on the primary host to
create and distribute the ssh keys.

    $ afs-robotest sshkeys create
    $ afs-robotest sshkeys dist
    $ afs-robotest sshkeys check

Perform the setup on the primary host. This will take serveral minutes to
complete the setup of the new AFS cell.

    $ afs-robotest setup

Check the `setup.log` to diagnose errors.

