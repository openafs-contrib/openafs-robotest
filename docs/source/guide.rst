Quick Start Guide
=================

This guide shows how to create a new testing workspace to create test virtual
machines, create a Kerberos realm and OpenAFS cell, and run the test suite.

This guide assume you will be using **vagrant** to manage your test instances,
however any provisioner supported by Ansible Moleucle can be used. See XXX to
read more about how to setup and use other provisioners.

Vagrant
-------

Be sure vagrant_ is installed and working.

The default provider for vagrant is **VirtualBox**. If you installed an
alternate `provider plugin`_, then be sure to set the ``VAGRANT_DEFAULT_PROVIDER``
environment variable to the provider you wish to be the default.

The default vagrant box in the test scenarios is **generic/centos8**. Be sure
you can start instances of that box name with **vagrant**.

.. _vagrant: https://www.vagrantup.com/
.. _`provider plugin`: https://www.vagrantup.com/docs/providers/default

Cookiecutter
------------

Install cookiecutter_

.. _cookiecutter: https://cookiecutter.readthedocs.io/


Test workspace
--------------

In a directory of your choice, create a test workspace with `cookiecutter`.

.. code-block:: console

    $ cd <project-directory>
    $ cookiecutter --directory cookiecutter/workspace https://github.com/openafs-contrib/openafs-robotest
    workspace_name [myworkspace]: <enter>
    Select install_molecule_plugin_vagrant:
    1 - yes
    2 - no
    Choose from 1, 2 [1]: <enter>
    Select install_molecule_plugin_virtup:
    1 - yes
    2 - no
    Choose from 1, 2 [1]: <enter>

Initalize the **test workspace** to install Ansible, Molecule, and the OpenAFS
Ansible roles.

.. code-block:: console

    $ cd myworkspace
    $ make init
    ...
    $ . .venv/bin/activate
    (.venv) $ make install-collection
    ...

Create a test cell **scenario**.

.. code-block:: console

    (.venv) $ make testcell-scenario
    scenario_name [myscenario]: <enter>
    molecule_driver_name [vagrant]: <enter>
    image_name [generic/centos8]: <enter>
    Select configuration:
    1 - class a: single host
    2 - class b: cluster 1 db, 2 fs, 3 cl
    3 - class c: cluster 3 db, 3 fs, 3 cl
    Choose from 1, 2 [1]: <enter>
    Select install_method:
    1 - managed
    2 - packages
    3 - bdist
    4 - sdist
    5 - scm
    Choose from 1, 2, 3, 4, 5 [1]: <enter>
    Select module_install_method:
    1 - dkms
    2 - kmod
    Choose from 1, 2 [1]: 2 <enter>

Create a test cell and run the Robot Framework tests.

.. code-block:: console

    (.venv) $ cd scenarios/testcell/myscenario
    (.venv) $ molecule test
