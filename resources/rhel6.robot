
*** Settings ***
Documentation  Install the AFS client and server binaries from the RPM
...            packages. After this test suite completes, the AFS servers
...            and clients can be started and the cell can be created.
Variables      rpm.py


*** Keywords ***
Get Package File
    [Arguments]  ${name}
    ${file}=  Set Variable
    ...  ${RPM_PACKAGE_DIR}/${name}-${RPM_AFSVERSION}-${RPM_AFSRELEASE}${RPM_DIST}.${RPM_ARCH}.rpm
    [Return]  ${file}

Get Kernel Package File
    ${file}=  Set Variable
    ...  ${RPM_PACKAGE_DIR}/kmod-openafs-${RPM_AFSVERSION}-${RPM_AFSRELEASE}.${RPM_KVERSION}.rpm
    [Return]  ${file}

Install RPM
    [Arguments]  ${packages}
    Sudo  rpm -v --install ${packages}

Install OpenAFS Common Packages
    ${package}=  Get Package File    openafs
    Install RPM  ${package}

Install OpenAFS Kerberos5 Packages
    ${package}=  Get Package File    openafs-krb5
    Install RPM  ${package}

Install OpenAFS Server Packages
    ${package}=  Get Package File    openafs-server
    Install RPM  ${package}

Install OpenAFS Client Packages
    ${package}=       Get Package File    openafs-client
    ${kmod_package}=  Get Kernel Package File
    Install RPM  ${package} ${kmod_package}

Set Client Configuration
    [Documentation]    Copy the cell config from the server directories.
    Sudo  cp /usr/afs/etc/CellServDB /usr/vice/etc/CellServDB
    Sudo  cp /usr/afs/etc/ThisCell /usr/vice/etc/ThisCell
    Sudo  cp /usr/afs/etc/CellServDB /usr/vice/etc/CellServDB.local

Start the bosserver
    Sudo  service openafs-server start

Stop the bosserver
    Sudo  service openafs-server stop

Start the Cache Manager
    Sudo  service openafs-client start

Stop the Cache Manager
    Sudo  service openafs-client stop

Remove Packages
    Sudo  rpm --erase
    ...  openafs-${RPM_AFSVERSION}-${RPM_AFSRELEASE}${RPM_DIST}.${RPM_ARCH}
    ...  openafs-krb5-${RPM_AFSVERSION}-${RPM_AFSRELEASE}${RPM_DIST}.${RPM_ARCH}
    ...  openafs-server-${RPM_AFSVERSION}-${RPM_AFSRELEASE}${RPM_DIST}.${RPM_ARCH}
    ...  openafs-client-${RPM_AFSVERSION}-${RPM_AFSRELEASE}${RPM_DIST}.${RPM_ARCH}
    ...  kmod-openafs-${RPM_AFSVERSION}-${RPM_AFSRELEASE}.${RPM_KVERSION}   # kversion includes dist and arch

Remove Server Configuration
    Sudo  rm -rf /usr/afs/etc
    Sudo  rm -rf /usr/afs/db
    Sudo  rm -rf /usr/afs/local
    Sudo  rm -rf /usr/afs/logs
    Sudo  rmdir /usr/afs

Remove Cache Manager Configuration
    Sudo  rm -rf /usr/vice/etc
