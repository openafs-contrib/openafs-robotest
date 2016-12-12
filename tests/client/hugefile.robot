# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Regression
Resource          openafs.robot

*** Test Cases ***
Create a Larger Than 2gb File
    [Tags]  todo  #(write-large)
    TODO

Write a File Larger than the Cache
    [Tags]  todo  #(fcachesize-write-file)
    TODO

Read a File Larger than the Cache
    [Tags]  todo  #(fcachesize-read-file)
    TODO

