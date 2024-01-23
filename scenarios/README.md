
This directory contains Ansible Molecule scenarios to create one or more
virtual machines, install a keberos realm and an OpenAFS cell, then run the
test suite.

Scenarios
=========

* default - Install the OpenAFS client and server on a single virtual machine
* cluster - Install the OpenAFS clients and servers on separate virtual machines

The OpenAFS clients and servers are installed from source code in these
scenarios.  The molecule may be changed (or new ones created) to install from
pre-built packages.  See the "OpenAFS Ansible Collection" for more information.

Usage
=====

Setup the virtualenv in the parent directory and activate it:

    $ cd ..
    $ make init
    $ . .ven/bin/activate
    (.venv) $ cd scenarios

Run molecule:

    $ molecule create [-s <scenario>]
    $ molecule converge [-s <scenario>]
    $ molecule verify [-s <scenario>]
    $ molecule destroy [-s <scenario>]

Or to combine the stages:

    $ molecule test [-s <scenario>]

The `molecule login` command can be used to ssh to running instances.  This can
be use for troubleshooting or development on running instances.


Environment Variables
=====================

Several environment variables may be used to parameterize the scenarios.

* `AFS_BOX`: Name of the vagrant box to be created. default: "generic/alma9"
* `AFS_GIT_REPO`:  URL of the OpenAFS git repository. default: "https://github.com/openafs/openafs.git"
* `AFS_GIT_VERSION`: Branch or tag name to checkout. default: "master"
