Customization
-------------


Unmanaged Instances
===================

You can also run Molecule to create an OpenAFS cell on existing virtual or
physical machines.  This is a common use case when setting up an environment
for development.  You will need to have ssh and sudo access to the existing
machines.

Molecule calls these **unmanaged instances**.  In this case, you will be
running ``molecule`` on your local machine and Ansible will connect to your
existing machines to install and configure Kerberos and OpenAFS.

You are responsible configuring your ``.ssh/config`` file on your local machine
to allow Molecule to connect to the machines to be configured.  The ``Host``
names in your ``.ssh/config`` file must match the instance names in the
``molecule.yml`` file.

Example:

.. code-block:: console

    $ cat ~/.ssh/config
    ...
    Host m-afs-client
        HostName 192.168.1.200
        User tycobb
        IdentityFile ~/.ssh/tycobb

    Host m-afs-server
        HostName 192.168.1.201
        User tycobb
        IdentityFile ~/.ssh/tycobb


The Ansible playbooks run by ``molecule`` require password-less ``sudo``.
Please set the ``NOPASSWD`` option in your ``sudoers`` files on the target
virtual machines to allow the user to run commands with ``sudo`` without a
password.  The ``NOPASSWD`` option may be removed after the ``molecule``
commands are run.


Scenarios
=========

The ``molecule.yml`` file can be customized to support different testing
scenarios, and new scenarios can be created by creating new scenario directories
under the ``molecule`` subdirectory.
A specific scenario can then be selected.

.. code-block:: console

    (venv) $ molecule test -s SCENARIO_DIRECTORY

Customization possibilities include:

* Different test instance operating systems
* Number of test instances and whether an instance is a client or server.
* OpenAFS installation installation method
* OpenAFS build options
* Test cases to run and Robot Framework ``robot`` options
