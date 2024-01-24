.. _`Quick Start Guide`:

Quick Start Guide
=================

This guide shows how to easily create an OpenAFS_ test cell and then run
`OpenAFS Robotest`_ test suite.

Prerequisites
-------------

Packages
~~~~~~~~

Install git, Python 3.10 (or later), and Python3 virtualenv on your local system.

MacOS:

.. code-block:: console

    $ brew install git python3 virtualenv

Debian/Ubuntu:

.. code-block:: console

    $ sudo apt-get install git python3 python3-venv

Fedora:

.. code-block:: console

    $ sudo dnf install git python3 python3-venv

Verify the Python version with:

.. code-block:: console

    $ python3 -V

Vagrant
~~~~~~~

The provided scenarios are configured to use Vagrant_ to manage your test
virtual machines.

Follow the installation instructions on the HashiCorp_ site when installing
Vagrant.  It is recommended to download Vagrant from the HashiCorp site
instead of installing it from your system's package manager.

You will need to install one the supported virtualization providers (such as
VirtualBox, or libvirt) and then install Vagrant.

Set the ``VAGRANT_DEFAULT_PROVIDER`` environment variable to select your
virtualization provider.  For example, if using the kvm virtualization provider
on linux:

.. code-block:: console

    $ export VAGRANT_DEFAULT_PROVIDER=libvirt

After installing Vagrant, be sure you are able to create an instance of the
``generic/alma9`` box, since we will be using that in this guide to create our
test cell.

See "Customization" if you already have existing physical or virtual
machines you wish to use for development and testing.  In this case, vagrant is
not required.

Setup
~~~~~

Clone the ``openafs-robotest`` project in a directory of your choice:

.. code-block:: console

    $ git clone https://github.com/openafs-contrib/openafs-robotest

If ``make`` is available, run ``make init`` to create the local virtualenv
and install the required Python packages.

.. code-block:: console

    $ make init
    $ source .venv/bin/activate

If ``make`` is not available, you can create the local virtualenv manually:

.. code-block:: console

    $ python3 -m venv .venv
    $ source .venv/bin/activate
    (.venv) $ pip install -U pip
    (.venv) $ pip install -r requirements.txt
    (.venv) $ patch-molecule-schema


Run the tests
-------------

Run ``molecule`` to create Kerberos realm, the OpenAFS cell, and then run the
`OpenAFS Robotest`_ test suite.  The test report and logs will be saved in the
``reports`` directory.

.. code-block:: console

    $ source .venv/bin/activate
    (.venv) cd scenarios
    (.venv) $ molecule create    # To create and prepare the test instance.
    (.venv) $ molecule converge  # To create the realm and cell.
    (.venv) $ molecule verify    # To run the test suite.
    (.venv) $ molecule login     # To ssh to the test instance.
    (.venv) $ molecule destroy   # To destroy the test instance.

The actions can be consolidated by running the ``test`` action:

.. code-block:: console

    (.venv) $ molecule test  # Run create, converge, verify, destroy


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
.. _Hashicorp: https://developer.hashicorp.com/vagrant/docs
