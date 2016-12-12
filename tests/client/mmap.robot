# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     mmap tests
Resource          openafs.robot

*** Test Cases ***
Append over a mapped page
    [Tags]  todo  arla  #(append-over-page)
    TODO

Write via mmap to a shared-mapped file
    [Tags]  todo  arla  #(mmap-shared-write)
    TODO

Compare a file being read via mmap private and read
    [Tags]  todo  arla  #(mmap-vs-read2)
    TODO

Compare a file being read via mmap shared and read
    [Tags]  todo  arla  #(mmap-vs-read)
    TODO

Compare a file being read via read and mmap shared
    [Tags]  todo  arla  #(read-vs-mmap2)
    TODO

Compare a file being read via read and mmap private
    [Tags]  todo  arla  #(read-vs-mmap)
    TODO
