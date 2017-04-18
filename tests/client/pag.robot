# Copyright (c) 2015 Sine Nomine Associates
# See LICENSE

*** Settings ***
Documentation     AFS PAG tests
Resource          openafs.robot

*** Variables ***
${PRINT_GROUPS}    python -c 'import os; print os.getgroups()'

*** Test Cases ***
Obtain a PAG with pagsh
    [Documentation]   Run a pagsh as a child process verify a PAG is set.
    [Setup]  Run Keyword
    ...    PAG Should Not Exist
    ${gids}=    PAG Shell          ${PRINT_GROUPS}
    ${pag}=     PAG From Groups    ${gids}
    PAG Should Be Valid            ${pag}
    [Teardown]  Run Keywords
    ...    PAG Should Not Exist

