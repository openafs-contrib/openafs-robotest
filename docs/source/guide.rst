.. _`Quick Start Guide`:

Quick Start Guide
=================

This guide shows how to quickly create an OpenAFS_ test cell with Vagrant_ and
Ansible_ and run `OpenAFS Robotest`_ suite on the ephemeral test cell. Ansible
Molecule_ is used to run Vagrant, Ansible and execute the tests.

The `OpenAFS Robotest`_ provides a `Cookiecutter`_ template so you can quickly
create your initial Molecule configuration files.  The Molecule_ files may be
customized to support different test configurations.

The `OpenAFS Ansible Collection`_ is automatically installed by Molecule to make
it easy to setup the test realm and cell.

Prerequisites
-------------

Python and git
~~~~~~~~~~~~~~

Ensure the following packages are installed on your system.

* git
* Python 3.6 (or better)
* Python3 virtualenv
* Python3 pip

MacOS:

Python can be installed on MacOS with homebrew_:

.. code-block:: console

    $ brew install git
    $ brew install python3
    $ pip3 install virtualenv

Debian and Ubuntu:

.. code-block:: console

    $ sudo apt-get install git python3 python3-venv python3-pip

Fedora:

.. code-block:: console

    $ sudo dnf install git python3 python3-venv python3-pip

Cookiecutter
~~~~~~~~~~~~

The OpenAFS Robotest repository includes a Cookiecutter_ template to help get
started quickly. You can run the ``cookiecutter`` command to start a new test
scenario.  ``cookiecutter`` may be installed with Python3 ``pip``.

.. code-block:: console

   $ pip3 install --user cookiecutter


Vagrant
~~~~~~~

Install Vagrant_ and a supported `virtualization provider`_ (e.g. VirtualBox,
VMWare, Libvirt/KVM) on your system. The default virtualization provider is
VirtualBox_.

Ensure you are able to create an instance of the ``generic/centos8`` box
with Vagrant_.


Creating a test scenario
------------------------

In a directory of your choice, create a test scenario with `Cookiecutter`_.
You will be prompted for various options.

.. code-block:: console

    $ cookiecutter \
      --directory cookiecutter/testcell-scenario \
      https://github.com/openafs-contrib/openafs-robotest

    scenario_name [Untitled]: my-first-scenario
    instance_prefix [m-]:
    Select collection_repo:
    1 - galaxy
    2 - github
    3 - local
    Choose from 1, 2, 3 [1]:
    collections_paths [.]:
    cell [example.com]:
    realm [EXAMPLE.COM]:
    Select platform:
    1 - centos8
    2 - centos7
    3 - debian11
    4 - debian10
    5 - fedora34
    6 - solaris114
    Choose from 1, 2, 3, 4, 5, 6 [1]:
    image_name [generic/debian11]:
    Select install_method:
    1 - managed
    2 - packages
    3 - bdist
    4 - sdist
    5 - source
    Choose from 1, 2, 3, 4, 5 [1]:
    Select enable_dkms:
    1 - yes
    2 - no
    Choose from 1, 2 [1]:
    Select enable_builds:
    1 - yes
    2 - no
    Choose from 1, 2 [1]:

This should create a molecule scenario directory containing a `molecule.yml`
file and a set of Ansible playbooks.

Initialize the local repo
~~~~~~~~~~~~~~~~~~~~~~~~~

Create a local git repository in the test scenario.

.. code-block:: console

    $ cd my-first-scenario
    $ git init
    $ git add .
    $ git commit -m Initial

Installing Molecule
~~~~~~~~~~~~~~~~~~~

Install `Ansible`_, `Molecule`_, and `Molecule Robot Framework plugin`_. A
Python virtualenv style installation in your scenario directory is recommended
for these packages.

.. code-block:: console

    $ cd my-first-scenario
    $ python3 -m venv venv
    $ . venv/bin/activate
    (venv) $ pip3 install -r requirements.txt

Molecule Driver Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Molecule driver settings are specified in a base configuration file located in
``<scenario-name>/.config/molecule/config.yml``.

See the Molecule_ documentation for more information about drivers and driver
options.  See the prepare playbook under ``<scenario-name>/molecule/playbooks``
for information about the ``prepare`` options.

.. code-block:: console

    $ cat my-first-scenario/.config/molecule/config.yml
    ---
    driver:
      name: vagrant
      provider:
        # Choose one of the providers below
        name: virtualbox
        # name: vmware_desktop
        # name: libvirt
      prepare:
        bootstrap_python: yes
        allow_reboot: yes
        selinux_mode: permissive
        rewrite_hosts_file: yes

Running the tests
-----------------

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

    (venv) $ molecule test -s SCENARIODIRECTORY

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
