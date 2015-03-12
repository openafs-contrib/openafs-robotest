# Copyright (c) 2014-2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Basic Functional Tests, part 2
Resource          openafs.robot

*** Test Cases ***
Stat Multiple Hardlinked Files
    [Tags]  todo  arla  #(hardlink3)
    TODO

Write, Truncate, Rewrite a File
    [Tags]  todo  arla  #(write2)
    TODO

Append to a File
    [Tags]  todo  arla  #(append1)
    TODO

Rename a File Over Another File
    [Tags]  todo  arla  #(rename2)
    TODO

Rename a File Into a Same-Volume Directory
    [Tags]  todo  arla  #(rename4)
    TODO

Rename a File Into Another-Volume Directory
    [Tags]  todo  arla  #(rename6)
    TODO

Rename an Open Directory
    [Tags]  todo  arla  #(rename-under-feet)
    TODO

Create a File with a Large Filename
    [Tags]  todo  arla  #(large-filename)
    TODO

Chmod a File by Descriptor
    [Tags]  todo  arla  #(fchmod)
    TODO

Utimes a File
    [Tags]  todo  arla  #(utime-file)
    TODO

Utimes a directory
    [Tags]  todo  arla  #(utime-dir)
    TODO

Test Directory Link Count Increasing/Decreasing Appropriately
    [Tags]  todo  arla  #(mkdir3)
    TODO

