
====================================
  OpenAFS Robo Test: Example Tests
====================================

.. |copy| unicode:: U+000A9 .. COPYRIGHT SIGN
.. |tm|   unicode:: U+2122  .. TRADEMARK SIGN

:Version: 0.0.1
:Date: May 23, 2013
:Copyright: 2013 |copy| Sine Nomine Associates

.. contents:: Table of Contents

Purpose
=======

This is a basic test to demonstrate how `Robot Framework`_ will be used for
`OpenAFS`_ system testing.  This test will create and mount an AFS volume
in an existing cell. Some files will be created and accessed in the new
volume. Finally, the volume will be unmounted and removed.

This test assumes the kerberos realm and AFS cell already exist and an
admin user account has been already created.  Robot test cases will be
written next to setup an AFS cell.

Test Suite Settings
===================

This test suite requires the standard `Robot Framework`_ operating system
library.  Custom libraries will likely be written when advanced tests
are developed

This initial basic test requires a test cell and to be run with
an admin token.

================= ==================
     Setting          Value
================= ==================
Library           OperatingSystem
Test Precondition Running as Admin
================= ==================


The following data values are used in the tests.

============= ==========
   Variable     Value
============= ==========
${fileserver} wasp
${partition}  a
${cell}       localcell
${volume}     test.11
${testfile}   myfile
============= ==========


Tests
=====

The tests create a volume, mount the volume, do some basic usage of files in
the AFS volume, then clean up.

Make a volume
-------------

The purpose of this test is to illustrate how to use the test framework to
create test volumes.  Steps should be added to verify the volume does not exist
before this test and does exist after this test.

============== ================ ======================================== ==============
   Test Case        Step                   Argument                        Argument
============== ================ ======================================== ==============
Make a Volume  [Documentation]  Test the creation of new volumes.
..             Create Volume    ${volume}
..             Mount Volume     /afs/${cell}/test/${volume}              ${volume}
============== ================ ======================================== ==============

Use the volume
--------------

The purpose of this test is to illustrate how to use the test framework to
create and remove test files in AFS. Steps should be added to verify the file
creation, do write and read tests, and set mode bits and test execution of
files in AFS.

============== ================ ======================================== ==============
   Test Case        Step                   Argument                        Argument
============== ================ ======================================== ==============
Use the Volume [Documentation]  Test creating and deleting files.
..             Create File      /afs/${cell}/test/${volume}/${testfile}
..             Remove File      /afs/${cell}/test/${volume}/${testfile}
============== ================ ======================================== ==============

Cleanup
-------

The purpose of this tet is to illustrate how to use the test framework to
remove the test volume created in the volume creation test.

============== ================ ======================================== ==============
   Test Case        Step                   Argument                        Argument
============== ================ ======================================== ==============
Cleanup        [Documentation]  Test volume removal.
..             Unmount Volume   /afs/${cell}/test/${volume}              ${volume}
..             Remove Volume    ${volume}
============== ================ ======================================== ==============

Keywords
========

This section defines the user keywords used in the test cases.

============== ============================ ========== ============================= =====================================
   Keyword               Action              Argument            Argument                         Argument
============== ============================ ========== ============================= =====================================
Run Command    [Arguments]                  ${cmd}
..             ${rc}                        ${output}  Run and Return RC and Output  ${cmd}
..             Log                          ${output}
..             Should be equal as Integers  ${rc}      0
============== ============================ ========== ============================= =====================================

================= ============================ ========== ============================= ====================================
   Keyword                   Action             Argument         Argument                         Argument
================= ============================ ========== ============================= ====================================
Running as Admin  ${rc}                        ${output}  Run and Return RC and Output  tokens
..                Log                          ${output}
..                Should be equal as Integers  ${rc}      0
..                Should Contain               ${output}  User's (AFS ID 1) tokens
================= ============================ ========== ============================= ====================================


============== ============= ==============================================================  ===================
   Keyword        Action                           Argument                                       Argument
============== ============= ==============================================================  ===================
Create Volume  [Arguments]   ${vol}
..             Run Command   vos create ${fileserver} ${partition} ${vol} -cell ${cell}
..

Remove Volume  [Arguments]   ${vol}
..             Run Command   vos remove ${fileserver} ${partition} -id ${vol} -cell ${cell}
..

Mount Volume   [Arguments]   ${dir}                                                          ${vol}
..             Run Command   fs mkmount ${dir} ${vol}
..

Unmount Volume [Arguments]   ${dir}                                                          ${vol}
..             Run Command   fs rmmount ${dir}
..
============== ============= ==============================================================  ===================



.. Link targets:

.. _OpenAFS: http://openafs.org
.. _Robot Framework: http://code.google.com/p/robotframework/
