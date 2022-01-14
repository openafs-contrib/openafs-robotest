.. _`Running Tests`:

Running Tests
=============

Requirements
------------

Before running the tests, OpenAFS must be installed on one or more systems and
the test cell be created.  Tests are executed on a system with running OpenAFS
cache manager for the test cell.

See the :ref:`Quick Start Guide` for information on how to use Ansible to create a
test cell on one or more virtual machines.

General test cell requirements:

* Kerberos KDC installed and running
* OpenAFS databases and fileservers installed and running
* OpenAFS top level volumes created, and mounted, and access rights configured
* Admin user created with system:administrators membership and Superuser rights
* Admin user keytab file created

Test system requirements:

* OpenAFS cache manager installed and running
* OpenAFS client commands (``bos``, ``vos``, ``pts``, ``fs``, etc)

Test software requirements:

* Python
* Python libyaml package (recommended)
* Robot Framework
* OpenAFSLibrary for Robot Framework
* The OpenAFS Robotest test files (``*.robot`` files)
* The admin user keytab
* A **variable file** with values setup for the cell under test. See :ref:`Variables`.


Executing tests
---------------

robot
~~~~~

The test cases are executed with the Robot Framework ``robot`` command line
program.  The complete set of tests may be executed or some subset may be
excuted with the ``robot`` command.

See the `Robot Framework User Guide`_ for information about executing test
cases.

Example:

.. code-block:: console

  $ robot \
    --exclude bug \
    --exclude slow \
    --exclude rogue-avoidance \
    --exclude requires-multi-fs \
    --loglevel INFO \
    --debugfile debug.log \
    --runemptysuite \
    --variablefile openafs-robotest.yml \
    openafs-robotest/tests

Ansible Molecule
~~~~~~~~~~~~~~~~

As described in the :ref:`Quick Start Guide`, Ansible Molecule may be used to create a
test cell and execute the tests on one or more virtual machines.  When running
the tests in this mode, the `Molecule Robot Framework plugin`_ will run ``robot``
on the test virtual machines over an ``ssh`` connection.

Before running the ``robot`` command, the plugin installs Robot Framework, the
OpenAFSLibrary, the test files (``*.robot`` files), and create the variable
file. After running the ``robot`` command, the plugin downloads the ``robot``
output files (logs and report) to your local machine.

You may customize the ``verifier`` section of the scenario ``molecule.yml``
file to change ``robot`` command line options, including tag and tests names.

Example verifier options:

.. code-block:: yaml

  verifier:
    name: robotframework
    enabled: true
    group: afs_test
    libraries:
      - robotframework-openafslibrary
    test_repos:
      - name: openafs-robotest
        repo: https://github.com/openafs-contrib/openafs-robotest
        version: master
    resources:
      - ${MOLECULE_SCENARIO_DIRECTORY}/../templates/openafs-robotest.yml.j2
    data_sources:
      - openafs-robotest/tests
    dest_dir: ${MOLECULE_PROJECT_DIRECTORY}/reports/${MOLECULE_SCENARIO_NAME}
    options:
      exclude:
        - bug
        - slow
        - rogue-avoidance
        - requires-multi-fs
      loglevel: INFO
      debugfile: debug.log
      runemptysuite: true
      variablefile: openafs-robotest.yml

.. _`Robot Framework User Guide`: https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html
.. _`Molecule Robot Framework plugin`: https://pypi.org/project/molecule-robotframework/
