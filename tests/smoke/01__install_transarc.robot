OpenAFS Installation (Transarc)
-------------------------------

Install the AFS client and server binaries from a binary distribution. After this
test suite completes, the AFS servers and clients can be started and the
cell can be created.


*** Setting ***
DefaultTags    install(transarc)
Library        OperatingSystem
Resource       keywords/utility.robot

*** Test Case ***
OpenAFS server installation
    sudo    mkdir -p /usr/afs
    sudo    cp -r -p ${IBM_DEST}/root.server/usr/afs/bin /usr/afs

OpenAFS cache manager installation
    sudo    mkdir -p /usr/vice
    sudo    mkdir -p /usr/vice/cache
    sudo    mkdir -p /usr/vice/etc
    sudo    cp -r -p ${IBM_DEST}/root.client/usr/vice/etc /usr/vice

OpenAFS workstation installation
    sudo    mkdir -p /usr/afsws
    sudo    cp -r -p ${IBM_DEST}/bin /usr/afsws
    sudo    cp -r -p ${IBM_DEST}/etc /usr/afsws
    sudo    cp -r -p ${IBM_DEST}/include /usr/afsws
    sudo    cp -r -p ${IBM_DEST}/lib /usr/afsws
    sudo    cp -r -p ${IBM_DEST}/man /usr/afsws

