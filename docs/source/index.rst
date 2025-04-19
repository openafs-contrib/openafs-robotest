OpenAFS RoboTest
================

OpenAFS RoboTest is a set of `Robot Framework`_ test cases for the OpenAFS_
distributed filesystem.  The test cases cover basic usage on a single client
and general OpenAFS administration.

An Ansible playbook is provided to deploy a basic Kerberos realm and OpenAFS
cell for testing on a single machine.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   guide
   running
   tests
   tags
   vars
   libraries/OpenAFSLibrary/index
   libs
   devel
   license

.. _`Robot Framework`: https://robotframework.org/
.. _OpenAFS: https://www.openafs.org
