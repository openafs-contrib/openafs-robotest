.. _`Development`:

Development
===========

This section is a guide for writing new test cases.

General guidelines
------------------

Test names should describe what a test proves (or disproves). Try to use clear
and descriptive language when naming tests and test suites.

Test cases must be independent. Every test case must have it's own setup and
teardown, and tests should not rely on an order of execution.

Test cases should be written in a declarative style, not imperative.
A typical test case is in the style **Given X**, **When Y**, **Then Z**.

Become familiar with the `Robot Framework standard libraries`_ and the OpenAFSLibrary_.

Required reading
~~~~~~~~~~~~~~~~

Read the `Robot Framework User Guide`_.

Read `how to write good test cases`_ for Robot Framework.

Tips
~~~~

* What specifically should this test prove or disprove?
* Keep the test cases independent.
* Test suite and test case names should be short, but as descriptive as possible.
* If a test case exceeds many lines consider creating new keywords.
* When writing tests, pay attention to the number of spaces.

Verifying a new test
--------------------

Once the test is written and saved, there are two ways to test it. The first way
is to run all of the tests. The second way is to only run the test suite that
the new test is in. The first method is best to make sure the tests outside of
the suite remain error free.

Common errors
-------------

* Incorrect spaces between arguments

  The spacing is incorrect. Most often, there are to few spaces between command
  inputs. For instance, the first command below has one space in between the two
  inputs and throws an error. The second command has two spaces between the inputs
  and is accepted by AFS and RoboTest.

.. code-block:: robotframework

    Should Not Contain    ${output}<SPACE>volume
    Should Not Contain    ${output}<SPACE><SPACE>volume

* Incorrect command arguments

  If there are required parts to an OpenAFS specific command missing, or there
  are parts missing for a keyword, Robot Framework will throw an error.


Creating keywords in Python
---------------------------

Consider adding new keywords to the OpenAFSLibrary_. The OpenAFSLibrary is
maintained in a separate git repository from the test cases.


.. _`Robot Framework User Guide`: https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html
.. _`Robot Framework standard libraries`: https://robotframework.org/robotframework/
.. _`how to write good test cases`: https://github.com/robotframework/HowToWriteGoodTestCases/blob/master/HowToWriteGoodTestCases.rst
.. _OpenAFSLibrary: https://robotframework-openafslibrary.readthedocs.io/en/latest/
