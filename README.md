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
want to setup a virtual machine to install OpenAFS and the test suite.

Install `setuptools` and `pip` if not already present. On Debian this can be
installed with:

    $ sudo apt-get install python-pip

Install Robotframework with the `pip` command:

    $ sudo pip install robotframework

Clone the OpenAFS Robotest to a directory of your choice:

    $ git clone https://github.com/openafs-contrib/openafs-robotest.git
    $ cd openafs-robotest

Install the python packages provided by openafs-robotest:

    $ (cd libraries/afsutil && ./install.sh)
    $ (cd libraries/OpenAFSLibrary && ./install.sh)

## Setup

Run the `afs-robotest` tool to set the configuration before running the setup
and tests.

To show the current configuration:

    $ ./afs-robotest config list

To configure robotest to install Transarc-style binaries:

    $ ./afs-robotest config set setup installer transarc
    $ ./afs-robotest config set paths dest <path-to-dest-directory>

The `config set` command will create a configuration file called
`afs-robotest.conf` in the current directory if it does not already exist. This
is the default name of the configuration file. The `--config` option can be
given to `afs-robotest` to specify a different configuration file, which can be
useful when testing different versions on a single system.

To install the binaries and to create the test cell:

    $ sudo ./afs-robotest setup

## Running tests

To run the tests:

    $ ./afs-robotest run

After running the tests, the AFS cell can be removed with the teardown
command:

    $ sudo ./afs-robotest teardown

The `auto_setup` and `auto_teardown` configuration options can be set to `yes`
to automatically run the setup and teardown.

## Test results

The test results are saved as html files in the `output` directory.  A minimal
web server is provided by `afs-robotest` as a convenience to view the test
report.

To start the minimal web server:

    $ afs-robotest web start

To stop the minimal web server:

    $ afs-robotest web stop

