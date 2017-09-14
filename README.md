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
* Python 2.7
* Python pip
* Python argparse
* Robotframework 2.7+
* OpenAFS installation packages or binaries built from source

## System Setup

Scripts are provided for supported platforms in the `setup` directory to
install the needed software prerequisites and perform any required system
setup.

To setup Debian jessie:

    $ sudo setup/debian8


## Installation

Install the OpenAFS robotest tests, libraries, and utilities with the provided
installation script:

    $ sudo ./install.sh


## Configure

As the regular test user (not-root), run the `afsrobot init` command to create
the initial configuration file.

    $ afsrobot init

To show the current configuration:

    $ afsrobot config list

To install Transarc-style binaries:

    $ afsrobot config set variables afs_dist transarc
    $ afsrobot config set host:$HOSTNAME installer transarc

To install RPM packages:

    $ afsrobot config set variables afs_dist rhel6
    $ afsrobot config set host:$HOSTNAME installer rpm

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

    $ afsrobot config set variables aklog /usr/local/bin/aklog-1.6

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

    $ afsrobot run

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

## Multiple configuration files

It can be useful to have more than one configuration file, instead of changing
values in the default configuration file.

Set the `AFSROBOT_INI` environment variable to specify the fully qualified
file name of the configuration file to be used by `afsrobot`.  This value
is overridden by the `--config` command line option.

## Multiple servers

This test harness supports setting up multiple file and database servers.
Install OpenAFS robotest on each server, as described above.  `sudo` must be
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

    $ afsrobot ssh create
    $ afsrobot ssh dist
    $ afsrobot ssh check

Perform the setup on the primary host. This will take several minutes to
complete the setup of the new AFS cell.

    $ afsrobot setup

