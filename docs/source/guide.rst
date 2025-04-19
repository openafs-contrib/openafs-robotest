.. _`Quick Start Guide`:

Quick Start Guide
=================

This guide shows how to create a local OpenAFS_ test cell and run `OpenAFS
RoboTest`_ test suite in a test system. It is recommended to run this in a test
virtual machine.

This guide assumes your test system is running Debian. OpenAFS packages are
available on Debian, which makes the initial setup easier.

Note that a container (docker, podman, etc) is not suitable, since we will be
loading the OpenAFS kernel module on the test system.

System setup
------------

Be sure you are able to run programs with ``sudo`` as a regular user. On
Debian, you can do this by adding your username to the ``sudo`` group while
running as root.

.. code-block:: shell

    usermod -a -G sudo <username>

Be sure your system is up to date. This is required in order to build and run
the OpenAFS kernel module.

.. code-block:: shell

    sudo apt update -y && sudo apt upgrade -y && sudo reboot

Install the following packages:

.. code-block:: shell

    sudo apt install ansible git pipx

Run ``pipx ensurepath`` and then re-login to be sure pipx commands are in your
``PATH``.

.. code-block:: shell

    pipx ensurepath

Install Robot Framework and the OpenAFS Library with ``pipx``.

.. code-block:: shell

    pipx install robotframework && pipx inject robotframework robotframework-openafslibrary

Checkout OpenAFS RoboTest
-------------------------

Clone the openafs-robotest project:

.. code-block:: shell

    git clone https://github.com/openafs-contrib/openafs-robotest

This project contains the Robot Framework tests for OpenAFS and a sample
playbook to install a test cell on your local machine.

Install OpenAFS and Kerberos
----------------------------

Change your working directory to the ``setup`` directory. This directory
contains the Ansible playbook to install Kerberos and OpenAFS.

.. code-block:: shell

    cd openafs-robotest/setup

Install the `OpenAFS Ansible Collection`_ with ansible-galaxy:

.. code-block:: shell

    ansible-galaxy collection install -r requirements.yml

Run the playbook to install Kerberos and OpenAFS on your local machine. This
will take some time as the playbook builds the cell and the client kernel
module.

.. code-block:: shell

    ansible-playbook local_openafs_sandbox.yml

If the playbook succeeds, the Kerberos realm and the OpenAFS cell be installed
and running on the local machine and your user will have administrator
credentials.

Change back to the project directory.

.. code-block:: shell

    cd ..

Run the tests
-------------

Run the ``robot`` command to run the tests.

.. code-block:: shell

    robot -A robotrc/smoketest.args tests/

The results are saved in the ``reports`` directory.


.. _Ansible: https://www.ansible.com/
.. _`OpenAFS Ansible Collection`: https://galaxy.ansible.com/openafs_contrib/openafs
.. _OpenAFS: https://www.openafs.org
.. _`OpenAFS RoboTest`: https://github.com/openafs-contrib/openafs-robotest
