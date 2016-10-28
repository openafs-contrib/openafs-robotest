# AFS Robotest

AFS Robotest is a [Robotframework][1] based test suite for OpenAFS. This test
suite will install the OpenAFS binaries, setup a simple AFS cell, and run a
series of basic tests, and finally remove the AFS cell.  The tests can be run
with or without an external Kerberos realm.

This test suite should be run on a non-production development or test system.
Typically you will want to setup one or more virtual machines to install
OpenAFS and run the tests.

[1]: http://robotframework.org/

## System Requirements

* Linux or Solaris
* Python 2.6 or 2.7
* Python argparse
* Robotframework 2.7+
* OpenAFS installation packages or binaries built from source

## Installation

### Install

Clone the git repository and install AFS Robotest and dependencies with the
provided install shell script.

    $ cd
    $ git clone https://github.com/openafs-contrib/openafs-robotest.git
    $ cd openafs-robotest
    $ sudo ./install.sh

### Setup sudo

The `sudo` command must be available and configured to run `afsutil` without a
password in order to install and configure OpenAFS. For example, add the
following to your sudoers file with `visudo`:

    %testers ALL=(root) NOPASSWD: /usr/local/bin/afsutil

Then add users which will run `afs-robotest` to the `testers` group.

    $ sudo usermod -a -G testers <username>

Verify sudo can be used with the command:

    $ sudo -n afsutil version

### Check the host file

Modern Linux distributions will add an entry to the `/etc/hosts` file to map a
loopback address to the hostname.  While, this is not strictly wrong, it can
confuse current versions of OpenAFS.

Remove any entries from `/etc/hosts` which map loopback addresses to the
current hostname.  The lookback address should be replaced with the primary
non-loopback address.  Loopback addresses start with `127.`.

## Setup

As the regular test user, run the `init` subcommand to create the initial
configuration file.

    $ afs-robotest init

To show the current configuration:

    $ afs-robotest config list

To install Transarc-style binaries:

    $ afs-robotest config set variables afs_dist transarc
    $ afs-robotest config set host:$HOSTNAME installer transarc

To install RPM packages:

    $ afs-robotest config set variables afs_dist rhel6
    $ afs-robotest config set host:$HOSTNAME installer rpm

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

    $ afs-robotest config set variables aklog /usr/local/bin/aklog-1.6

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

    $ afs-robotest setup

To run the tests:

    $ afs-robotest run

After running the tests, the AFS cell may be removed with:

    $ afs-robotest teardown

## Test results

The setup logs and test results are saved in `$HOME/.afsrobotestrc/` by
default.  A minimal web server is provided as a convenience to view the test
reports.

To start the minimal web server:

    $ afs-robotest web start

To stop the minimal web server:

    $ afs-robotest web stop

## Multiple configuration files

It can be useful to have more than one configuration file, instead of changing
values in the default configuration file.

Set the `AFS_ROBOTEST_CONF` environment variable to specify the fully qualified
file name of the configuration file to be used by `afs-robotest`.  This value
is overridden by the `--config` command line option.

Example:

    $ export AFS_ROBOTEST_CONF=~/.afsrobotestrc/example.conf

## Multiple servers

This test harness supports setting up multiple file and database servers.
Install `openafs-robotest` on each server, as described above.  `sudo` must be
configured with NOPASSWD for the test user account on each host.

A configuration section must be added for each test server. The name of the
test section is `[host:<hostname>]`, in addition to the `[host:myhost]` for
the "primary" server.  For example:

    [host:myhost]
    use = yes
    installer = transarc
    isfileserver = yes
    isdbserver = yes
    isclient = yes
    dest = /usr/local/src/openafs-test/amd64_linux26/dest

    [host:mytesta]
    use = yes
    installer = transarc
    isfileserver = yes
    isdbserver = no
    isclient = yes
    dest = /usr/local/src/openafs-test/amd64_linux26/dest

    [host:mytestb]
    use = yes
    installer = transarc
    isfileserver = yes
    isdbserver = no
    isclient = no
    dest = /home/example/src/openafs/amd64_linux26/dest

The OpenAFS installation and setup is done using ssh with keyfiles. The
`ssh` subcommand is provided to create an ssh key pair and distribute
the public keys to each test server.  Run the following on the primary host to
create and distribute the ssh key.

    $ afs-robotest ssh create
    $ afs-robotest ssh dist
    $ afs-robotest ssh check

Perform the setup on the primary host. This will take several minutes to
complete the setup of the new AFS cell.

    $ afs-robotest setup

