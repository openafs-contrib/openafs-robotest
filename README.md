# AFS Robotest

AFS Robotest is a [Robotframework][1] based test suite for OpenAFS. The test
suite will install the OpenAFS binaries, setup a simple test cell, and then run
a series of basic tests.  Optionally, a test feature of OpenAFS is used to
emulate a Kerberos server, allowing the tests to be run without the need to
setup a Kerberos realm and create keytabs.

[1]: http://robotframework.org/

## System Requirements

* Linux or Solaris
* Python 2.6 or 2.7
* Python argparse
* Robotframework 2.7+
* OpenAFS installation packages or binaries built from source

## Installation

This test suite should be run on a dedicated test system.  Typically you will
want to setup several virtual machines.  The  `sudo` command must be available
and configured with the `NOPASSWD` option for the user running the tests.

Clone the OpenAFS Robotest git repository to a directory of your choice.
Install OpenAFS Robotest (and dependencies) with the provided install shell
script.

    $ cd ~
    $ git clone https://github.com/openafs-contrib/openafs-robotest.git
    $ cd openafs-robotest
    $ ./install.sh

## Setup

Run the `afs-robotest config` command to view and set the configuration for
your system.

To show the current configuration:

    $ afs-robotest config list

To install Transarc-style binaries:

    $ afs-robotest config set host:$HOSTNAME installer transarc
    $ afs-robotest config set host:$HOSTNAME dest <path-to-dest-directory>
    $ afs-robotest config set variables afs_dist transarc

To install RPM packages:

    $ afs-robotest config set host:$HOSTNAME installer rpm
    $ afs-robotest config set host:$HOSTNAME rpms <path-to-packages>
    $ afs-robotest config set variables afs_dist rhel6

Where `$HOSTNAME` is your system's hostname.

By default, the configuration is stored in the file
`~/.afsrobotestrc/afs-robotest.conf`. This can be customized by setting the
`AFS_ROBOTEST_CONF` environment variable or specifying the fully qualified path
with the `--config` command line option, which can be useful when testing
various configurations.

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

## Running tests

To install the OpenAFS binaries and create the test cell:

    $ afs-robotest setup

To run the tests:

    $ afs-robotest run

After running the tests, the AFS cell can be removed with the teardown
command:

    $ afs-robotest teardown

## Test results

The setup logs and test results are saved in the `html` directory.  A minimal
web server is provided as a convenience to view the test reports.

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
    nuke = no
    setclock = no

    [host:mytesta]
    use = yes
    installer = transarc
    isfileserver = yes
    isdbserver = no
    isclient = yes
    dest = /usr/local/src/openafs-test/amd64_linux26/dest
    nuke = no
    setclock = yes

    [host:mytestb]
    use = yes
    installer = transarc
    isfileserver = yes
    isdbserver = no
    isclient = no
    dest = /home/mmeffie/src/openafs/amd64_linux26/dest
    nuke = no
    setclock = no

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

## afsutil

This project includes a python package called `afsutil`, which is a collection
of helpers to build and setup OpenAFS.  The `afs-robotest` setup and teardown
commands are implemented with the `afsutil` package.

The `afsutil` package includes commands to build OpenAFS binaries on Linux and
Solaris.

To build a legacy "Transarc style" distribution:

    git clone git://git.openafs.org/openafs.git
    cd openafs
    afsutil build

See `afsutil build -help` for options, including options to give to configure.

To build RPM packages on RHEL/Centos:

    git clone git://git.openafs.org/openafs.git
    cd openafs
    afsutil package

To reload the OpenAFS kernel module after rebuilding it (it should already be
running from a previous `afs-robotest setup` or `afsutil install`):

    afsutil build
    sudo afsutil reload

