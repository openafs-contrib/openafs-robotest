*** Setting ***
Library    OperatingSystem
Library    String
Variables    variables/redhat/rpm.py

*** Keywords ***
get package file
    [arguments]          ${name}
    ${packagefile}       set variable    ${RPM_PACKAGE_DIR}/${name}-${RPM_AFSVERSION}-${RPM_AFSRELEASE}${RPM_DIST}.${RPM_ARCH}.rpm
    [return]             ${packagefile}

get kernel package file
    ${packagefile}       set variable    ${RPM_PACKAGE_DIR}/kmod-openafs-${RPM_AFSVERSION}-${RPM_AFSRELEASE}.${RPM_KVERSION}.rpm
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

