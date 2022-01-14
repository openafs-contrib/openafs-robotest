.. _`Tags`:

Tags
====

Test cases tags are metadata used to organize tests and can be used to specify
which tests are executed or skipped.

bug
  Indicates this test was written to verify a bug fix.

requires-gfind
  This test requires the GNU ``find`` command.

requires-multi-fs
  This test requires multiple fileservers. For example a test that moves
  a volume from one fileserver to another fileserver in the cell.

rogue-avoidance
  This test is related to the rogue volume avoidance tests.

slow
  Indicates this test may incur a long test execution time.  Typically, this
  type of test is used for stress test cases.
