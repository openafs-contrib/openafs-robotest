.. include:: <isonum.txt>

====================================
  OpenAFS Robo Test
====================================

:Version: 0.0.3
:Date: July 22, 2013
:Copyright: 2013 |copy| Sine Nomine Associates

.. contents:: Table of Contents

Introduction
============

This is a basic test to demonstrate how `Robot Framework`_ will be used for
`OpenAFS`_ system testing.  This test will install the AFS binaries and
then create the AFS cell on a single host.


System Requirements
-------------------

The following prequiestists are required:

  * RHEL/CentOS (for this first version)
  * `Robot Framework`_
  * a Kerberos 5 realm
  * 3 keytab files for the AFS cell to be created

Only standard `Robot Framework`_ libaries are required.

Test Suites
===========

.. include:: test_suites.rst

Keywords
========

TODO: Document custom keywords.

Libraries
=========

TODO: Document custom libraries keywords.


.. Link targets:

.. _OpenAFS: http://openafs.org
.. _Robot Framework: http://code.google.com/p/robotframework/
