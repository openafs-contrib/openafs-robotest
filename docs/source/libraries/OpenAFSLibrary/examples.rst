Examples
========

The following example demonstrates a test of a basic OpenAFS volume release.

.. code-block:: robotframework

   | *** Settings ***   |
   | Library            | OpenAFSLibrary |

   | *** Test Cases *** |
   | Volume Release     |
   |                    | [Documentation]         | Example test.                   |
   |                    | Login                   | admin    | keytab=admin.keytab  |
   |                    | Create Volume           | testvol  | afs01 | a            |
   |                    | Command Should Succeed  | ${VOS} addsite afs01 a testvol  |
   |                    | Release Volume          | testvol  |
   |                    | Volume Should Exist     | testvol.readonly                |
   |                    | Volume Location Matches | testvol  | server=afs01 | part=a | vtype=ro |
   |                    | Remove Volume           | testvol                         |
   |                    | Logout                  |
