# OpenAFS Robotest

OpenAFS Robotest is a [Robot Framework][1] based test suite for OpenAFS.

Documentation: [https://openafs-robotest.readthedocs.io][5]

## System Requirements

* Kerberos realm
* OpenAFS cell
* Python 3.5 or later
* [robotframework][1]
* [robotframework-openafslibrary][2]

## Overview

OpenAFS Robotest is a set of [Robot Framework][1] test cases for the [OpenAFS][4]
distributed filesystem.  The test cases cover a basic workload from a single
client and general OpenAFS administration.

An Ansible Molecule template and with Ansible playbooks are provided to quickly
deploy a Kerberos test realm and OpenAFS test cell on virtual machines.

[1]: http://robotframework.org/
[2]: https://github.com/openafs-contrib/robotframework-openafslibrary
[3]: https://github.com/openafs-contrib/ansible-openafs
[4]: https://www.openafs.org
[5]: https://openafs-robotest.readthedocs.io/
