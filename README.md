# OpenAFS robotest

OpenAFS robotest is a [Robotframework][1] based test suite for OpenAFS. This test
suite will install the OpenAFS binaries, setup a simple AFS cell on one or more
systems, run a series of basic tests, and finally remove the AFS cell.  The
tests can be run with or without an external Kerberos realm.

This test suite should be run on a non-production development or test system.
Typically you will want to setup one or more virtual machines to install
OpenAFS and run the tests.

[1]: http://robotframework.org/

## System Requirements

* Linux or Solaris
* OpenAFS installation packages or binaries built from source
* Python 2.7
  * argparse
  * Robotframework 2.7+
  * afsutil
  * robotframework-openafslibrary

## Installation

The following setup instructions assume your system has Python `pip` and
`setuptools` installed.  Older systems may not have those tools installed by
default. (TODO: Provide info on how to install without `pip` in another
document.)

## Prerequisites

### Linux

Install the `afsutil` Python package on **each** host in the test cell.
`afsutil` is a command line tool to install and setup of OpenAFS for testing.
This package should be installed globally since it will need to be run as root
for the OpenAFS setup. `afsutil` does not have any non-standard Python library
dependencies.

    # pip install afsutil

Create a group and a user account on *each* test system in the cell.

    # groupadd testers
    # useradd -G testers afsrobot
    # passwd afsrobot

Configure `sudoers` on *each* test system to allow the members of the group
created above to run `afsutil` with `sudo` without a password. This can be done
on modern systems by adding a file in `/etc/sudoers.d` and making that file
read-only.

    # echo '%testers ALL=(root) NOPASSWD: /usr/bin/afsutil' > /etc/sudoers.d/afsrobot
    # chmod 440 /etc/sudoers.d/afsrobot

Verify you are able to login as the `afsrobot` user and are able to run
`afsutil` on *each* test system.

    # sudo -i -u afsrobot
    $ afsutil version
    afsutil <version-number>
    $ sudo -n afsutil version
    afsutil <version-number>

### Solaris

TODO: commands variants for solaris

### afsrobot

Install the OpenAFS Robotest files on the *primary* test system, as a user
in the `testers` group.

    $ su - afsrobot
    $ whoami
    afsrobot

    $ git clone https://github.com/openafs-contrib/openafs-robotest.git
    $ cd openafs-robotest
    $ make install

Install frontend `afsrobot` tool and the OpenAFS Robotframework library,
without sudo.

    $ cd src/afsrobot
    $ make install-user

Create the `afsrobot` configuration file.

    $ afsrobot init


TODO: Configuration file stuff....

### akimpersonate notes

The `akimpersonate` feature of `aklog` is used to create AFS tokens by
accessing the service keytab directly, without the need for a Kerberos realm.
This is configured by setting `akimpersonate` to `yes` in the `kerberos`
section of the configuration.

Unfortunately, the `akimpersonate` feature may not be functional in
development releases of OpenAFS, a.k.a, the master branch.  For testing
development releases, either use a Kerberos realm or provide a 1.6.10 (or
better) version of `aklog`.  Build a recent version of 1.6.x, and copy the
`aklog` binary to a local path, then set the `aklog` option in the `variables`
section of the configuration file to specify which `aklog` program is to be
used during the setup and tests. For example:

    $ afsrobot config set test aklog /usr/local/bin/aklog-1.6

## Building OpenAFS

This project includes a python package called `afsutil`, which is a collection
of helpers to build and setup OpenAFS.  The `afsutil` package includes commands
to build OpenAFS binaries on Linux and Solaris.

To build a legacy "Transarc-style" distribution binaries:

    $ cd
    $ git clone git://git.openafs.org/openafs.git
    $ cd openafs
    $ sudo afsutil getdeps
    $ afsutil build

To build RPM packages on RHEL/Centos:

    $ cd
    $ git clone git://git.openafs.org/openafs.git
    $ cd openafs
    $ git checkout openafs-stable-<version>   # e.g. openafs-stable-1_6_18
    $ sudo afsutil getdeps
    $ afsutil package

## Running tests

To install the OpenAFS binaries and create the test cell:

    $ afsrobot setup

To run the tests:

    $ afsrobot test

After running the tests, the AFS cell may be removed with:

    $ afsrobot teardown

## Test results

The setup logs and test results are saved in `$HOME/afsrobot/` by
default.  A minimal web server is provided as a convenience to view the test
reports.

To start the minimal web server:

    $ afsrobot web start

To stop the minimal web server:

    $ afsrobot web stop

## Multiple servers

This test harness supports setting up multiple file and database servers.
Install OpenAFS robotest on each server, as described above.  `sudo` must be
configured with NOPASSWD for the test user account on each host.

A configuration section must be added for each test server.

    [cell]
    db = afs1,afs2,afs3
    fs = afs3
    cm = afs2

    [host.0]
    name = afs1
    installer = transarc
    dest = /usr/local/src/openafs-test/amd64_linux26/dest

    [host.1]
    name = afs2
    installer = transarc
    dest = /usr/local/src/openafs-test/amd64_linux26/dest

    [host.2]
    name = afs3
    installer = transarc
    dest = /home/example/src/openafs/amd64_linux26/dest

The OpenAFS installation and setup is done using ssh with keyfiles. The
`ssh` subcommand is provided to create an ssh key pair and distribute
the public keys to each test server.  Run the following on the primary host to
create and distribute the ssh key.

    $ afsrobot ssh create
    $ afsrobot ssh dist
    $ afsrobot ssh check

Perform the setup on the primary host. This will take several minutes to
complete the setup of the new AFS cell.

    $ afsrobot setup

