OpenAFS Installation (RPM)
--------------------------

Install the AFS client and server binaries from the RPM packages. After this
test suite completes, the AFS servers and clients can be started and the
cell can be created.


*** Setting ***
DefaultTags    install(redhat)
Library    OperatingSystem
Resource    keywords/utility.robot
Resource    keywords/redhat/rpm.robot

*** Test Case ***
OpenAFS common package installation
    ${package}    get package file    openafs
    install    ${package}

OpenAFS kerberos 5 package installation
    ${package}    get package file    openafs-krb5
    install    ${package}

OpenAFS server installation
    ${package}    get package file    openafs-server
    install    ${package}

OpenAFS client installation
    ${package}   get package file    openafs-client
    ${kmod_package}    get kernel package file
    install    ${package} ${kmod_package}

