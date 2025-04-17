Keywords
========

Version: 0.7.2

Access Control List Contains
----------------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required
   * - name
     - 
     - required
   * - rights
     - 
     - required

**Documentation**

Fails if an ACL does not contain the given rights.

Access Control List Matches
---------------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required
   * - acls
     - 
     - 

**Documentation**

Fails if an ACL does not match the given ACL.

Access Control Should Exist
---------------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required
   * - name
     - 
     - required

**Documentation**

Fails if the access control does not exist for the the given user or group name.

Access Control Should Not Exist
-------------------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required
   * - name
     - 
     - required

**Documentation**

Fails if the access control exists for the the given user or group name.

Add Access Rights
-----------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required
   * - name
     - 
     - required
   * - rights
     - 
     - required

**Documentation**

Add access rights to a path.

Command Should Fail
-------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - cmd
     - 
     - required

**Documentation**

Fails if command exits with a zero status code.

Command Should Succeed
----------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - cmd
     - 
     - required
   * - msg
     - None
     - 

**Documentation**

Fails if command does not exit with a zero status code.

Create Dump
-----------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - filename
     - 
     - required
   * - size
     - small
     - 
   * - contains
     - 
     - 

**Documentation**

Generate a volume dump file.

Create Files
------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required
   * - count
     - 1
     - 
   * - size
     - 0
     - 
   * - depth
     - 0
     - 
   * - width
     - 0
     - 
   * - fill
     - zero
     - 

**Documentation**

Create a directory tree of test files.

path
  destination path
count
  number of files to create in each directory
size
  size of each file
depth
  sub-directory depth
width
  number of sub-directories in each directory
fill
  test files data pattern

Valid fill values:

* zero - fill with zero bits
* one  - fill with one bits
* random - fill with pseudo random bits
* fixed  - fill with repetitions of fixed bits

Create Volume
-------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - name
     - 
     - required
   * - server
     - None
     - 
   * - part
     - a
     - 
   * - path
     - None
     - 
   * - quota
     - 0
     - 
   * - ro
     - False
     - 
   * - acl
     - None
     - 
   * - orphan
     - False
     - 

**Documentation**

Create and mount a volume.

Create a volume and optionally mount the volume. Also optionally create
a read-only clone of the volume and release the new new volume. Release the
parent volume if it is replicated.

Directory Entry Should Exist
----------------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required

**Documentation**

Fails if directory entry does not exist in the given path.

File Should Be Executable
-------------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required

**Documentation**

Fails if path is not an executable file for the current user.

Get Cache Size
--------------

**Documentation**

Get the cache size.

Outputs AFS cache size as the number of 1K blocks.

Get Inode
---------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required

**Documentation**

Returns the inode number of a path.

Get Version
-----------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - host
     - 
     - required
   * - port
     - 
     - required

**Documentation**

Request the software version number.

Get Volume Id
-------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - name
     - 
     - required

**Documentation**

Lookup the volume numeric id.

Inode Should Be Equal
---------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - a
     - 
     - required
   * - b
     - 
     - required

**Documentation**

Fails if paths have different inodes.

Link
----

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - src
     - 
     - required
   * - dst
     - 
     - required
   * - code_should_be
     - 0
     - 

**Documentation**

Create a hard link.

Link Count Should Be
--------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required
   * - count
     - 
     - required

**Documentation**

Fails if the path has an unexpected inode link count.

Login
-----

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - user
     - 
     - required
   * - password
     - None
     - 
   * - keytab
     - None
     - 

**Documentation**

Acquire an AFS token for authenticated access.

Logout
------

**Documentation**

Release the AFS token.

Mount Volume
------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required
   * - vol
     - 
     - required
   * - options
     - 
     - 

**Documentation**

Mount a volume on a path.

Pag From Groups
---------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - gids
     - None
     - 

**Documentation**

Return the PAG from the given group id list.

Pag Shell
---------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - script
     - 
     - required

**Documentation**

Run a command in the pagsh and returns the output.

Pag Should Be Valid
-------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - pag
     - 
     - required

**Documentation**

Fails if the given PAG number is out of range.

Pag Should Exist
----------------

**Documentation**

Fails if a PAG is not set.

Pag Should Not Exist
--------------------

**Documentation**

Fails if a PAG is set.

Release Volume
--------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - name
     - 
     - required

**Documentation**

Release the volume.

Remove Volume
-------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - name_or_id
     - 
     - required
   * - path
     - None
     - 
   * - flush
     - False
     - 
   * - server
     - None
     - 
   * - part
     - None
     - 
   * - zap
     - False
     - 

**Documentation**

Remove a volume.

Remove the volume and any clones. Optionally remove the given mount point.

Should Be A Dump File
---------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - filename
     - 
     - required

**Documentation**

Fails if filename is not an AFS dump file.

Should Be Dir
-------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required

**Documentation**

Fails if path is not a directory.

Should Be File
--------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required

**Documentation**

Fails if path is not a file.

Should Be Symlink
-----------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required

**Documentation**

Fails if path is not a symlink.

Should Not Be Dir
-----------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required

**Documentation**

Fails if path is a directory.

Should Not Be Symlink
---------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required

**Documentation**

Fails if path is a symlink.

Symlink
-------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - src
     - 
     - required
   * - dst
     - 
     - required
   * - code_should_be
     - 0
     - 

**Documentation**

Create a symlink.

Unlink
------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - path
     - 
     - required
   * - code_should_be
     - 0
     - 

**Documentation**

Unlink the directory entry.

Volume Location Matches
-----------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - name_or_id
     - 
     - required
   * - server
     - 
     - required
   * - part
     - 
     - required
   * - vtype
     - rw
     - 

**Documentation**

Fails if volume is not located on the given server and partition.

Volume Should Be Locked
-----------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - name
     - 
     - required

**Documentation**

Fails if the volume is not locked.

Volume Should Be Unlocked
-------------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - name
     - 
     - required

**Documentation**

Fails if the volume is locked.

Volume Should Exist
-------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - name_or_id
     - 
     - required

**Documentation**

Verify the existence of a read-write volume.

Fails if the volume entry is not found in the VLDB or the volume is
not present on the fileserver indicated by the VLDB.

Volume Should Not Exist
-----------------------

**Arguments**

.. list-table::
   :header-rows: 1

   * - Name
     - Default value
     - Notes
   * - name_or_id
     - 
     - required

**Documentation**

Fails if volume exists.

