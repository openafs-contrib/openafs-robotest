*** Comments ***
Copyright (c) 2025 Sine Nomine Associates
See LICENSE


*** Settings ***
Documentation    Status checks suite has a test case that allows us to ping
...    all the virtual machines on the network.
Library    Remote    http://client1.example.com:8270    AS   client1
Library    Remote    http://client2.example.com:8270    AS   client2
Library    Remote    http://server1.example.com:8270    AS   server1
Library    Remote    http://server2.example.com:8270    AS   server2
Library    Remote    http://server3.example.com:8270    AS   server3


*** Test Cases ***
Ping robot server
    [Documentation]    Ping robot server
    client1.Command Should Succeed   true
    client2.Command Should Succeed   true
    server1.Command Should Succeed   true
    server2.Command Should Succeed   true
    server3.Command Should Succeed   true
