.. _`Variables`:

Variables
=========

This section describes the Robot Framework variables for the Kerberos realm and
OpenAFS cell under test. The variables referenced by the `OpenAFSLibrary`_ for Robot
Framework are included as well as variables referenced by the test cases.

It is recommended to create a Robot Framework variable file for your test cell.
The variables in the file may be taken with the ``robot --variablefile`` command
line option. (Note: When running the tests with Ansible Molecule, a variable
file is created on the test instance by Ansible. See the
``openafs-robotest.yml.j2`` template file.)

See the `Robot Framework User Guide`_ for more information about variables and
variable files.


AFS_ADMIN
  Administrative username. This user should already exist and should be a
  member of the ``system:administrators`` group.

  Type: string

AFS_AKIMPERSONATE
  Use the ``aklog`` akimpersonate feature to print tokens using the keytab
  file specified by the ``KRB_AFS_KEYTAB`` variable.

  Type: boolean

AFS_CELL
  The OpenAFS cell name of the cell under test.

  Type: string

AFS_FILESERVER_A
  Primary test fileserver hostname. This variable is required for volume tests.

  Type: string

AFS_FILESERVER_B
  Secondary test fileserver hostname. The variable is required when the
  ``require-multi-fs`` tag is included.

  Type: string

AFS_USER
  Test Kerberos principal/OpenAFS username.
  Should not be a member of the ``system:administrators`` group.

  Type: string

AKLOG
  The pathname of the OpenAFS ``aklog`` command.

  Type: path

BOS
  The pathname of the OpenAFS ``bos`` command.

  Type: path

FS
  The pathname of the OpenAFS ``fs`` command.

  Type: path

GFIND
  The pathname of the GNU ``find`` command.  This variable is required
  when the ``requires-gfind`` tag is included.

  Type: path

KDESTROY
  The pathname of the Kerberos ``kdestroy`` command.

  Type: path

KINIT
  The pathname of the Kerberos ``kinit`` command.

  Type: path

KLOG_KRB5
  The pathname of the OpenAFS ``klog.krb5`` command.

  Type: path

KRB_REALM
  The name of the Kerberos realm for the cell under test.

  Type: string

PAG_ONEGROUP
  This options specifies if the OpenAFS PAG is stored by the OpenAFS cache
  manager in one UNIX group id instead of two UNIX group ids.  Note:
  Historically, the OpenAFS clients on Solaris store the PAG in only one group
  id. This option can be used to support those clients.

  Type: boolean

PAGSH
  The pathname of the OpenAFS ``pagsh`` command.

  Type: path

PTS
  The pathname of the OpenAFS ``pts`` command.

  Type: path

PYTHON
  The pathname of the Python command used for tests. This is used for tests
  which run a separate Python instance.

  Type: path

RXDEBUG
  The pathname of the OpenAFS ``rxdebug`` command.

  Type: path

TOKENS
  The pathname of the OpenAFS ``tokens`` command.

  Type: path

UDEBUG
  The pathname of the OpenAFS ``udebug`` command.

  Type: path

UNLOG
  The pathname of the OpenAFS ``unlog`` command.

  Type: string

VOS
  The pathname of the OpenAFS ``vos`` command.

  Type: string

.. _`Robot Framework User Guide`: https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html
.. _`OpenAFSLibrary`: https://github.com/openafs-contrib/robotframework-openafslibrary
