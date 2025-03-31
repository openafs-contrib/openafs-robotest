# OpenAFS Robotest

OpenAFS Robotest is a [Robot Framework][1] based test suite for OpenAFS.

Documentation: [https://openafs-robotest.readthedocs.io][5]

## Overview

OpenAFS Robotest is a set of [Robot Framework][1] test cases for the [OpenAFS][4]
distributed filesystem.  The test cases cover a basic workload from a single
client and general OpenAFS administration.

The tests are executed on a machine running the OpenAFS client, which requires
the kernel module to be loaded before starting the tests.  The OpenAFS servers
may be running on separate machines.

An Ansible playbook is provided to easily deploy a Kerberos realm and OpenAFS cell
on in the local machine.  See the [Quick Start Guide](docs/source/guide.rst)
in the doc folder for more information.

## System Requirements

* Python 3
* [Robot Framework][1]
* [Robot Framework OpenAFS Library][2]

In order to run the tests, you will need:

* A Kerberos test realm, which may be on a separate machine.
* A OpenAFS test cell, which may be running on one or more separate machines.
* OpenAFS client on the machine running Robot Framework
* Kerberos keytabs for the admin and regular user on the test machine

## Installation

Install the `robotframework` and `robotframework-openafslibrary` packages from
the Python Packaging Index (PyPI) with `pipx`.

    $ pipx install robotframework
    $ pipx inject robotframework-openafslibrary

(If `pipx` is not available, you can manually create a virtualenv and install
the packages with with `pip`.)

Checkout the openafs-robotest project to a directory of your choice.

Create a variable file with the settings for your cell.  This file contains the
site specific settings for your test cell.  See the `setup/templates` directory
for examples.

## Running the tests

Run the test cases using the `robot` command. See the Robot Framework
documentation for details.


[1]: http://robotframework.org/
[2]: https://github.com/openafs-contrib/robotframework-openafslibrary
[4]: https://www.openafs.org
[5]: https://openafs-robotest.readthedocs.io/
