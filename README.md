# AFS Robotest

AFS Robotest is a [Robot Framework][1] based test suite and test library for
OpenAFS. This initial version is a limited test suite for an OpenAFS server and
client on a single test system.  Robotest will install the OpenAFS binaries,
setup a simple test cell, then run a series of basic tests.  A test feature of
OpenAFS is used to mimic a Kerberos server, allowing the tests to be run
without the need to setup a Kerberos realm and create keytabs.

[1]: http://robotframework.org/

*Requirements*

* Linux or Solaris
* Python 2.6.x
* Robot Framework 2.7 or better
* OpenAFS installation packages or binaries built from source

## Installation

This test harness is designed to be run on a dedicated test system.  Typically
you will want to setup a virtual machine to run the tests.

Robot Framework can be installed using the Python `pip` command.  (See
http://robotframework.org/ for more details.)

    $ sudo pip install robotframework

Clone OpenAFS RoboTest to a directory of your choice:

    $ git clone https://github.com/openafs-contrib/openafs-robotest.git
    $ cd openafs-robotest

The test harness should be run as a normal user, however the installation and
removal of OpenAFS requires root access.


## Running Tests

To run the tests:

    $ afs-robotest run


## Viewing the test results

The test results are saved in the `output` directory by default.  Set up a
webserver to serve the files in the `output` directory or use the built-in
server provided by afs-robotest to view the test report and log.

    $ afs-robotest web start

The results are then available under http://localhost:8000/

