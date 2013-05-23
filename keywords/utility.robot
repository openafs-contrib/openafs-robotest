*** Setting ***
Library  OperatingSystem

*** Keyword ***
TODO
    [arguments]  ${msg}
    log    TODO: ${msg}

run command
    [arguments]  ${cmd}
    ${rc}  ${output}  run and return rc and output  ${cmd}
    log  ${output}
    should be equal as integers  ${rc}  0

sudo
    [arguments]  ${cmd}
    run command   sudo -n ${cmd}

files should exist
    [arguments]    @{files}
    :FOR    ${file}    IN    @{files}
    \    should exist    ${file}

files should not exist
    [arguments]    @{files}
    :FOR    ${file}    IN    @{files}
    \    should not exist    ${file}

program is running
    [arguments]    ${program}
    ${output}    run    ps --no-headers -o cmd -e
    should contain    ${output}    ${program}

program is not running
    [Arguments]    ${program}
    ${output}    Run    ps --no-headers -o cmd -e
    should not contain    ${output}    ${program}

