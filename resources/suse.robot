
*** Settings ***
Documentation  Keywords for OpenAFS on SuSE.
Variables      sysinfo.py
Variables      rpm.py

*** Keywords ***
Install OpenAFS on SuSE
    OpenAFS Common Package Installation
    OpenAFS Kerberos 5 Package Installation
    OpenAFS Docs Package Installation
    OpenAFS Server Installation
    OpenAFS Client Installation

OpenAFS Common Package Installation
    ${package}    Get Package File    openafs
    Install    ${package}

OpenAFS Kerberos 5 Package Installation
    ${package}    get package file    openafs-krb5-mit
    install    ${package}

OpenAFS Docs Package Installation
    ${package}    Get Package File    openafs-docs
    Install    ${package}

OpenAFS Server Installation
    ${package}    Get Package File    openafs-server
    install    ${package}
    postinstall_server

OpenAFS Client Installation
    ${package}   Get Package File    openafs-client
    ${kmod_package}    Get Kernel Package File
    Install    ${package}    ${kmod_package}

Postinstall Server
    File Should Not Exist    ${AFS_SERVER_LIB_DIR}/NetInfo
    Should Not Be Empty      ${HOSTADDRESS}
    Create File    /tmp/NetInfo    ${HOSTADDRESS}
    Sudo    cp /tmp/NetInfo ${AFS_SERVER_LIB_DIR}/NetInfo
    Run     rm /tmp/NetInfo

Get Package File
    [Arguments]  ${name}
    Should Not Be Empty  ${name}
    Should Not Be Empty  ${RPM_PACKAGE_DIR}
    Should Not Be Empty  ${RPM_AFSVERSION}
    Should Not Be Empty  ${RPM_AFSRELEASE}
    Should Not Be Empty  ${RPM_DIST}
    Should Not Be Empty  ${RPM_ARCH}
    ${file}=  Set Variable
    ...  ${RPM_PACKAGE_DIR}/${name}-${RPM_AFSVERSION}-${RPM_AFSRELEASE}${RPM_DIST}.${RPM_ARCH}.rpm
    File Should Exist  ${file}
    [Return]  ${file}

Get Kernel Package File
    Should Not Be Empty  ${RPM_KFLAVOUR}
    ${file}=  Set Variable
    ...  ${RPM_PACKAGE_DIR}/openafs-kmp-${RPM_KFLAVOUR}*.rpm
    File Should Exist  ${file}
    [Return]  ${file}

Install
    [Arguments]  @{packages}
    Sudo  rpm -v --install --replacepkgs  @{packages}

Set Client Configuration
    [Documentation]    Copy the cell config from the server directories.
    Sudo    cp ${AFS_SERVER_ETC_DIR}/CellServDB ${AFS_CLIENT_ETC_DIR}/CellServDB
    Sudo    cp ${AFS_SERVER_ETC_DIR}/ThisCell ${AFS_CLIENT_ETC_DIR}/ThisCell

Start the bosserver
    Sudo  /sbin/service openafs-server start

Stop the bosserver
    Sudo  /sbin/service openafs-server stop

Start the Cache Manager
    Sudo  /sbin/service openafs-client start

Stop the Cache Manager
    Sudo  /sbin/service openafs-client stop

Remove Packages
    ${rc}  ${output}  Run And Return Rc And Output    rpm -qa openafs*
    Should Be Equal As Integers  ${rc}  0
    @{packages}=  Split To Lines  ${output}
    Sudo  rpm -v --erase  @{packages}

Remove Cache Manager Configuration
    Should Not Be Empty     ${AFS_KERNEL_DIR}
    Directory Should Exist  ${AFS_KERNEL_DIR}
    Sudo  rm -rf ${AFS_KERNEL_DIR}

Remove Server Configuration
    Should Not Be Empty  ${AFS_LOGS_DIR}
    Should Not Be Empty  ${AFS_DB_DIR}
    Should Not Be Empty  ${AFS_LOCAL_DIR}
    Should Not Be Empty  ${AFS_CONF_DIR}
    Sudo  rm -rf ${AFS_LOGS_DIR}
    Sudo  rm -rf ${AFS_DB_DIR}
    Sudo  rm -rf ${AFS_LOCAL_DIR}
    Sudo  rm -rf ${AFS_CONF_DIR}

