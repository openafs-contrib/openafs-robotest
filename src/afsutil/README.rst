=======
afsutil
=======

Utility classes and command-line tool to build, install, and setup OpenAFS.

Classes
-------

::

    build     build and package OpenAFS from source
    cell      setup a new OpenAFS cell
    cmd       basic OpenAFS command wrappers
    install   interface to install and remove OpenAFS binaries
    keytab    import Kerberos 5 keytabs and create fake keytabs for testing
    rpm       install and remove OpenAFS rpm packages
    service   interface to start and stop OpenAFS services
    system    misc system utilities
    transarc  install and remove legacy Transarc-style OpenAFS binaries

Command line interface
----------------------

::

    usage: afsutil <command> ...
    where command is:
        version   print version information
        getdeps   install build dependencies
        check     check system
        build     build binaries
        reload    reload the kernel module after a build
        package   build packages
        install   install binaries
        remove    remove binaries
        start     start afs services
        stop      stop afs services
        fakekey   generate a keytab file for testing
        setkey    add a service key from a keytab file
        newcell   setup a new cell
        addfs     add a new fileserver to the cell
        login     obtain token with a keytab

Examples
--------

To build OpenAFS from sources::

    afsutil build

To install legacy "Transarc-style" binaries::

    sudo afsutil install \
      --force \
      --dist transarc \
      --components server client \
      --dir /usr/local/src/openafs-test/amd64_linux26/dest \
      --cell example.com \
      --realm EXAMPLE.COM \
      --hosts myhost1 myhost2 myhost3 \
      --csdb /root/CellServDB.dist \
      -o "afsd=-dynroot -fakestat -afsdb" \
      -o "bosserver=-pidfiles"

To setup the OpenAFS service key from a Kerberos 5 keytab file::

    sudo afsutil setkey
      --cell example.com \
      --realm EXAMPLE.COM \
      --keytab /root/fake.keytab

To start the OpenAFS servers and client::

    sudo afsutil start server
    sudo afsutil start client

To setup a new OpenAFS cell on 3 servers (after 'afsutil install' has been run
on each)::

    sudo afsutil newcell \
      --cell example.com \
      --realm EXAMPLE.COM \
      --admin example.admin \
      --top test \
      --akimpersonate \
      --keytab /root/fake.keytab \
      --fs myhost1 myhost2 myhost3 \
      --db myhost1 myhost2 myhost3 \
      --aklog /usr/local/bin/aklog-1.6 \
      -o "dafs=yes" \
      -o "afsd=-dynroot -fakestat -afsdb" \
      -o "bosserver=-pidfiles" \
      -o "dafileserver=L"
