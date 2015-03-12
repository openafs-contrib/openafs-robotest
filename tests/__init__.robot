# Copyright (c) 2014 Sine Nomine Associates
# See LICENSE

*** Settings ***
Suite setup       Setup Test System
Suite teardown    Teardown Test System
Resource          openafs.robot

*** Keywords ***
Setup Test System
    Precheck System
    Install OpenAFS
    Create Test Cell

Teardown Test System
    Shutdown OpenAFS
    Remove OpenAFS
    Purge Files
