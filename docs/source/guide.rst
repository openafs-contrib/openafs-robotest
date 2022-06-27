.. _`Quick Start Guide`:

Quick Start Guide
=================

This guide shows how to quickly create an OpenAFS_ test cell with Vagrant_ and
Ansible_, and run `OpenAFS Robotest`_ suite on the test cell. Ansible
Molecule_ is used to run Vagrant, Ansible, and then execute the tests.

You can also run Molecule_ to create an OpenAFS cell on existing virtual or
physical machines.  This is a common use case when setting up an enviroment for
development.  You will need to have ssh and sudo access to the existing
machines.

The `OpenAFS Robotest`_ provides a `Cookiecutter`_ template so you can quickly
create your initial Molecule configuration files.  The Molecule_ files may be
customized to support different test configurations.

The `OpenAFS Ansible Collection`_ is automatically installed by Molecule to make
it easy to setup the test realm and cell.

Prerequisites
-------------

Python
~~~~~~

Install Python3 and the `pip`, `virtualenv`, and `cookiecutter` Python3
packages on your local system.

MacOS:

Python3 can be installed on MacOS with homebrew_:

.. code-block:: console

    $ brew install git
    $ brew install python3
    $ pip3 install virtualenv cookiecutter

Debian and Ubuntu:

.. code-block:: console

    $ sudo apt-get install git python3 python3-venv python3-pip
    $ python3 -m pip install --user cookiecutter

Fedora:

.. code-block:: console

    $ sudo dnf install git python3 python3-venv python3-pip
    $ python3 -m pip install --user cookiecutter

Vagrant
~~~~~~~

This guide assumes you will be using Vagrant_ to manage your test virtual
machines.  If you already have existing physical or virtual machines you wish to
use for development and testing, do not install Vagrant_, instead see
`Unmanaged Instances`_.

Vagrant_ can be used to create and manage virtual machines for development
and testing.  To use Vagrant_ you will need to install one the supported
`virtualization providers`_ and then install Vagrant_.

The default virtualization provider is VirtualBox_.  Be sure to follow the
installation instructions on the HashiCorp site when installing Vagrant_. It is
recommended to download Vagrant_ from the HashiCorp site, instead of installing
from your system's package manager.

After installing Vagrant, be sure you are able to create an instance of the
``generic/alma8`` box, since we will be using that in this guide to create
our first test cell.

Unmanaged Instances
~~~~~~~~~~~~~~~~~~~

You can also use Molecule to configure existing physical or virtual machines.
Molecule calls these **unmanaged instances**.

You are resposible for creating the machines and configuring your
``.ssh/config`` file to allow Molecule to connect to your machines.  The
``Host`` names in your ``.ssh/config`` file must match the instance names in the
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


Create a Scenario
-----------------

The OpenAFS Robotest repository includes a Cookiecutter_ template to help get
started quickly. You can run the ``cookiecutter`` command to start a new test
scenario.

In a directory of your choice, create a test scenario with `Cookiecutter`_.
You will be prompted for various options.

.. code-block:: console

    $ cookiecutter \
        --directory cookiecutter/testcell-scenario \
        https://github.com/openafs-contrib/openafs-robotest

    testcell_name [untitled]: my-first-scenario
    Select driver:
    1 - vagrant/virtualbox
    2 - vagrant/libvirt
    3 - vagrant/vmware_desktop
    4 - proxmox
    5 - unmanaged
    Choose from 1, 2, 3, 4, 5 [1]: 2
    Select platform:
    1 - alma8
    2 - debian11
    3 - fedora36
    4 - solaris114
    Choose from 1, 2, 3, 4 [1]: 1
    image [generic/alma8]:
    instance_name [m-afs]:
    Select cluster:
    1 - one instance
    2 - one client instance, one server instance
    3 - three client instances, three database instances, three fileserver instances
    Choose from 1, 2, 3 [1]:
    Select install_method:
    1 - managed
    2 - packages
    3 - bdist
    4 - sdist
    5 - source
    Choose from 1, 2, 3, 4, 5 [1]:
    Select install_with_dkms:
    1 - yes
    2 - no
    Choose from 1, 2 [1]:
    Select build_packages:
    1 - yes
    2 - no
    Choose from 1, 2 [1]:
    realm [EXAMPLE.COM]:
    cell [example.com]:
    user [tester]:
    admin [admin]:


This will create a molecule scenario directory containing a molecule directory
with a `molecule.yml` file and a set of Ansible playbooks.

Install Molecule
~~~~~~~~~~~~~~~~

Install `Ansible`_, `Molecule`_, and `Molecule Robot Framework plugin`_ with
`pip`.

.. code-block:: console

    $ cd my-first-scenario
    $ python3 -m venv venv
    $ . venv/bin/activate
    (venv) $ pip3 install -r requirements.txt

Run the tests
-------------

Run ``molecule`` to run the Ansible playbooks to create Kerberos realm, the
OpenAFS cell and then install and run the `OpenAFS Robotest`_ test suite. The
test report and logs are saved in the ``reports/<scenario-name>`` directory.

.. code-block:: console

    (venv) $ molecule test

Individual Molecule commands may be used to run the scenario in steps. This
can be helpful when troubleshooting.

.. code-block:: console

    (venv) $ molecule create    # To create and prepare the test instance.
    (venv) $ molecule converge  # To create the realm and cell.
    (venv) $ molecule verify    # To run the test suite.
    (venv) $ molecule login     # To ssh to the test instance.
    (venv) $ molecule destroy   # To destroy the test instance.



Customization
-------------

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


.. _Ansible: https://www.ansible.com/
.. _Cookiecutter: https://cookiecutter.readthedocs.io/
.. _homebrew: https://brew.sh
.. _Molecule: https://molecule.readthedocs.io/en/latest/
.. _`Molecule Robot Framework plugin`: https://pypi.org/project/molecule-robotframework/
.. _`OpenAFS Ansible Collection`: https://galaxy.ansible.com/openafs_contrib/openafs
.. _OpenAFS: https://www.openafs.org
.. _`OpenAFS Robotest`: https://github.com/openafs-contrib/openafs-robotest
.. _Vagrant: https://www.vagrantup.com/
.. _VirtualBox: https://www.virtualbox.org/
.. _`virtualization provider`: https://www.vagrantup.com/docs/providers
