# OpenAFS Robotest

OpenAFS Robotest is a [Robot Framework][1] based test suite for OpenAFS.

Documentation: [https://openafs-robotest.readthedocs.io][5]

## Overview

OpenAFS Robotest is a set of [Robot Framework][1] test cases for the [OpenAFS][4]
distributed filesystem.  The test cases cover a basic workload from a single
client and general OpenAFS administration.

An Ansible Molecule scenario is provided to easily deploy a Kerberos test realm
and OpenAFS test cell on virtual machines.

## Quick start

Install these system requirements:

* Vagrant
* Python 3.10 or later

Install the required python packages:

    $ make init

If make is not available, then run the following commands to
create the virtualenv and install the required packages:

    $ /usr/bin/python3.12 -m venv .venv
    $ source .venv/bin/activate
    (.venv) $ pip install -U pip
    (.venv) $ pip install -r requirements.txt
    (.venv) $ patch-molecule-schema

To create a test cell and run the tests:

    $ source .venv/bin/activate
    (.venv) $ cd scenarios
    (.venv) $ molecule create
    (.venv) $ molecule converge
    (.venv) $ molecule verify
    (.venv) $ molecule destroy

The molecule actions may be combined as:

    (.venv) $ molecule test

[1]: http://robotframework.org/
[2]: https://github.com/openafs-contrib/robotframework-openafslibrary
[3]: https://github.com/openafs-contrib/ansible-openafs
[4]: https://www.openafs.org
[5]: https://openafs-robotest.readthedocs.io/
