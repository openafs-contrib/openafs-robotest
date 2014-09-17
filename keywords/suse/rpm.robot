*** Setting ***
Library    OperatingSystem
Library    String
Variables    variables/suse/rpm.py
Variables    variables/suse/paths.py

*** Keywords ***
get package file
    [arguments]          ${name}
    ${packagefile}       set variable    ${RPM_PACKAGE_DIR}/${name}-${RPM_AFSVERSION}-${RPM_AFSRELEASE}${RPM_DIST}.${RPM_ARCH}.rpm
    [return]             ${packagefile}

get kernel package file
    ${packagefile}       set variable    ${RPM_PACKAGE_DIR}/openafs-kmp-${RPM_KFLAVOUR}*.rpm
    [return]             ${packagefile}

get package contents
    [arguments]    ${package}
    file should exist    ${package}
    ${query}    run    rpm -qpl --nosignature ${package}
    @{files}    split to lines    ${query}
    [return]    @{files}

install
    [Arguments]  ${packages}
    sudo    rpm --install ${packages}

postinstall_server 
    file should not exist    ${AFS_SERVER_LIB_DIR}/NetInfo
    create file    /tmp/NetInfo    ${AFS_IP}
    sudo    cp /tmp/NetInfo ${AFS_SERVER_LIB_DIR}/NetInfo
    run    rm /tmp/NetInfo
