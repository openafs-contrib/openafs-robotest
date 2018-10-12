# OpenAFS Robotest

OpenAFS Robotest is a [Robotframework][1] based test suite for OpenAFS.

This is the work-in-progress Ansible integration branch. The following changes
are in progress.

* Provide a way to setup variable files and aguments for robotframwork `robot`.
* Use the robotframework `robot` command to run tests and to invoke cellwide
  setup an teardown.
* Adopt external and local custom ansible playbooks for cell setup and teardown.
* Run tests out of the checked out repo (zero install for tests)
* Convert the library to py 3.0

## System Requirements

* Linux or Solaris
* Python 2.7
* [robotframework-openafslibrary][2]
* [robotframework][1]

## Setup

TODO

* System setup
* Getting OpenAFS packages or building openafs

## Running tests

TODO

## Test results

TODO


[1]: http://robotframework.org/
[2]: https://github.com/openafs-contrib/robotframework-openafslibrary
