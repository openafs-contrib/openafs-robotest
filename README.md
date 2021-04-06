# OpenAFS Robotest

OpenAFS Robotest is a [Robot Framework][1] based test suite for OpenAFS.

Documentation: [https://openafs-robotest.readthedocs.io][5]

## System Requirements

* Kerberos Realm
* OpenAFS cell
* Python 2.7 or 3.6
* [robotframework][1]
* [robotframework-openafslibrary][2]

## Overview

This is a basic set of tests for the [OpenAFS][4] distributed filesystem.  The
test cases cover basic workload from a single client (at this time) and general
OpenAFS administration.

Please see the [Ansible roles for OpenAFS][3] playbooks to deploy a Kerberos
realm and OpenAFS cell in order to run the tests.


[1]: http://robotframework.org/
[2]: https://github.com/openafs-contrib/robotframework-openafslibrary
[3]: https://github.com/openafs-contrib/ansible-openafs
[4]: https://www.openafs.org
[5]: https://openafs-robotest.readthedocs.io/
