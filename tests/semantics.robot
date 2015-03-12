# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Filesystem Semantics tests
Resource          openafs.robot

*** Test Cases ***
Create a File with 8 bit Characters in its Name
    [Tags]  todo  arla  #(strange-characters)
    TODO

Test pine Lockfile Semantics
    [Tags]  todo  arla  #(pine)
    TODO

Create and Remove a Single File in Parallel
    [Tags]  todo  arla  #(parallel1)
    TODO

Create a Larger Than 2gb File
    [Tags]  todo  arla  #(write-large)
    TODO

