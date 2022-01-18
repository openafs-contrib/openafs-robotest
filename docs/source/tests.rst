Tests
=====




Admin
-----

Bosserver
~~~~~~~~~

Bosserver tests

* Add a Superuser
* List Server Hosts
* List Superusers
* Remove a Superuser

Ptserver
~~~~~~~~

Ptserver tests

* Add a User to a Group
* Chown a Group
* Create a Group
* Create a User
* Delete a Group
* Delete a User
* Examine a Group
* Examine a User
* Get Group Membership
* Get User Membership
* List Groups a User Owns
* Remove a User from a Group
* Set Fields on a User
* Set and List Maxuser

Admin.Volume
------------

Backup
~~~~~~

* Avoid creating a rogue volume during backup
* Create a Backup Volume

Clone
~~~~~

* Avoid creating a rogue volume during clone

Create
~~~~~~

Volserver/vlserver tests

* Add a Replication Site
* Avoid creating a rogue volume during create
* Create a Volume
* Display Header and VLDB Information
* Display VLDB Information
* Display Volume Header Information
* Remove a Replicated Volume
* Remove a Replication Site

Dump
~~~~

* Dump a Volume
* Dump an Empty Volume
* Dump and Restore Data Integrity

Move
~~~~

* Avoid creating a rogue volume during move
* Move a Volume
* Move a volume between servers

Release
~~~~~~~

* Avoid creating a rogue volume during release
* Release a Volume

Restore
~~~~~~~

Tests to verify volume restore operations with the
various of the restore options and to test the volume
server robustness while attempting to restore invalid
volume dump streams.

* Avoid creating a rogue volume during restore
* Restore a Volume Containing a Bogus ACL
* Restore a volume
* Restore an empty volume

Workload
--------

Basic
~~~~~

Basic Functional Tests

* Create a Cross-Volume Hard Link
* Create a Directory
* Create a File
* Create a Hard Link to a Directory
* Create a Hard Link within a Directory
* Create a Hard Link within a Volume
* Create a Symlink
* Rename a File
* Rewrite a file
* Timestamp rollover after 2147483647 (January 19, 2038 03:14:07 UTC)
* Touch a file
* Write and Execute a Script in a Directory
* Write to a File

Dir
~~~

Directory Object tests

* Unicode File Name

Find
~~~~

File Hierarchy Traversal Tests

* Traverse Simple Tree
* Traverse Tree with Two Parents

Hugefile
~~~~~~~~

Regression

* Create a Larger Than 2gb File
* Read Write a File Larger than 4G
* Read a File Larger than the Cache
* Write a File Larger than the Cache

Mountpoint
~~~~~~~~~~

Mountpoint tests

* Create a Mountpoint to a Nonexistent Volume
* Make and Remove a Mountpoint
* Make and Remove a Mountpoint with Command Aliases

Pag
~~~

AFS PAG tests

* Obtain a PAG with pagsh

Readonly
~~~~~~~~

Read-only tests

* Write a File in a Read-only Volume

Stress
~~~~~~

Client stess tests

* Create a Large Number of Entries in a Directory

