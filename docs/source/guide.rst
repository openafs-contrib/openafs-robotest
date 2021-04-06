Quick Start Guide
=================

Create a new **test workspace**.

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

Initalize the **test workspace**.

.. code-block:: console

    $ cd myworkspace
    $ make init
    ...
    $ . .venv/bin/activate

Create a test cell **scenario**.

.. code-block:: console

    (.venv) $ make testcell-scenario
    scenario_name [myscenario]: <enter>
    molecule_driver_name [vagrant]: <enter>
    image_name [generic/centos8]: <enter>
    Select configuration:
    1 - single
    2 - cluster
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
