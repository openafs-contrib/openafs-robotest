*** Comments ***
Copyright (c) 2025 Sine Nomine Associates
See LICENSE


*** Settings ***
Documentation    Health check suite has test cases that will ensure that an OpenAFS environment is properly
...    configured before the main OpenAFS test cases are executed.

Variables    ../test_env_vars.py
Library    Remote    http://${SERVER1}.${DOMAIN}:${PORT}    AS   server1
Library    Remote    http://${SERVER2}.${DOMAIN}:${PORT}    AS   server2
Library    Remote    http://${SERVER3}.${DOMAIN}:${PORT}    AS   server3
Library    Remote    http://${CLIENT1}.${DOMAIN}:${PORT}    AS   client1
Library    Remote    http://${CLIENT2}.${DOMAIN}:${PORT}    AS   client2
Library    String


*** Test Cases ***
Robot servers are running
    [Documentation]    Robot servers are running
    ...
    ...    Runs 'true' command on each server to check if it succeeds.

    server1.Command Should Succeed   true
    server2.Command Should Succeed   true
    server3.Command Should Succeed   true

File servers are running
    [Documentation]    File servers are running
    ...
    ...    Run bos status (unauthenticated) on both clients and ensure
    ...    OpenAFS servers are running.

    ${rc}    ${output}=    client1.Run And Return Rc And Output    bos status ${SERVER1}
    Log Many    ${rc}    ${output}
    Should Be Equal As Integers    ${rc}    0
    Should Contain    ${output}    Instance ptserver, currently running normally.
    Should Contain    ${output}    Instance vlserver, currently running normally.
    Should Contain    ${output}    Instance dafs, currently running normally.
    Should Contain    ${output}    Auxiliary status is: file server running.

    ${rc}    ${output}=    client1.Run And Return Rc And Output    bos status ${SERVER2}
    Log Many    ${rc}    ${output}
    Should Be Equal As Integers    ${rc}    0
    Should Contain    ${output}    Instance ptserver, currently running normally.
    Should Contain    ${output}    Instance vlserver, currently running normally.
    Should Contain    ${output}    Instance dafs, currently running normally.
    Should Contain    ${output}    Auxiliary status is: file server running.

    ${rc}    ${output}=    client1.Run And Return Rc And Output    bos status ${SERVER3}
    Log    ${rc}
    Log    ${output}
    Should Be Equal As Integers    ${rc}    0
    Should Contain    ${output}    Instance ptserver, currently running normally.
    Should Contain    ${output}    Instance vlserver, currently running normally.
    Should Contain    ${output}    Instance dafs, currently running normally.
    Should Contain    ${output}    Auxiliary status is: file server running.

    ${rc}    ${output}=    client2.Run And Return Rc And Output    bos status ${SERVER1}
    Log    ${rc}
    Log    ${output}
    Should Be Equal As Integers    ${rc}    0
    Should Contain    ${output}    Instance ptserver, currently running normally.
    Should Contain    ${output}    Instance vlserver, currently running normally.
    Should Contain    ${output}    Instance dafs, currently running normally.
    Should Contain    ${output}    Auxiliary status is: file server running.

    ${rc}    ${output}=    client2.Run And Return Rc And Output    bos status ${SERVER2}
    Log    ${rc}
    Log    ${output}
    Should Be Equal As Integers    ${rc}    0
    Should Contain    ${output}    Instance ptserver, currently running normally.
    Should Contain    ${output}    Instance vlserver, currently running normally.
    Should Contain    ${output}    Instance dafs, currently running normally.
    Should Contain    ${output}    Auxiliary status is: file server running.

    ${rc}    ${output}=    client2.Run And Return Rc And Output    bos status ${SERVER3}
    Log    ${rc}
    Log    ${output}
    Should Be Equal As Integers    ${rc}    0
    Should Contain    ${output}    Instance ptserver, currently running normally.
    Should Contain    ${output}    Instance vlserver, currently running normally.
    Should Contain    ${output}    Instance dafs, currently running normally.
    Should Contain    ${output}    Auxiliary status is: file server running.

OpenAFS-server systemd service is running
    [Documentation]    OpenAFS-server systemd service is running
    ${rc}    ${output}=    server1.Run And Return Rc And Output    systemctl is-active openafs-server
    Log Many    ${rc}    ${output}
    Should Be Equal As Integers    ${rc}    0
    Should Contain    ${output}    active

    ${rc}    ${output}=    server2.Run And Return Rc And Output    systemctl is-active openafs-server
    Log Many    ${rc}    ${output}
    Should Be Equal As Integers    ${rc}    0
    Should Contain    ${output}    active

    ${rc}    ${output}=    server3.Run And Return Rc And Output    systemctl is-active openafs-server
    Log Many    ${rc}    ${output}
    Should Be Equal As Integers    ${rc}    0
    Should Contain    ${output}    active

Cell volumes exist and are online
    [Documentation]    Cell volumes exist and are online
    ...
    ...    Calls vos listvldb and vos listvol -server localhost to ensure that
    ...    cell volumes exist in vldb.

    ${rc}    ${output}=    client1.Run And Return Rc And Output    vos examine root.afs
    Log Many    ${rc}    ${output}
    Should Be Equal As Integers    ${rc}    0
    Should Contain    ${output}    On-line
    Should Contain    ${output}    root.afs
    Should Contain    ${output}    number of sites -> 4

Kerberos KDC is running
    [Documentation]    Kerberos KDC is running
    ...
    ...    Check status of krb5kdc service and make sure it is active and running

    ${rc}    ${output}=    server1.Run And Return Rc And Output    systemctl status krb5kdc.service
    Should Be Equal As Integers    ${rc}    0
    Should Contain    ${output}    Active: active (running)
    Should Contain    ${output}    Loaded: loaded
    Should Contain    ${output}    enabled

    ${rc}    ${output}=    server1.Run And Return Rc And Output    systemctl status krb5kdc.service
    Should Be Equal As Integers    ${rc}    0
    Should Contain    ${output}    Active: active (running)
    Should Contain    ${output}    Loaded: loaded
    Should Contain    ${output}    enabled

Rxdebug version check
    [Documentation]    Rxdebug version check

    ${version_server1}=    server1.Get Version    localhost    7002
    Log    server1 rxdebug version = ${version_server1}
    Set Suite Metadata   Server1 OpenAFS Version    ${version_server1}

    ${version_server2}=    server2.Get Version    localhost    7002
    Log    server2 rxdebug version = ${version_server2}
    Set Suite Metadata   Server2 OpenAFS Version    ${version_server2}

    ${version_server3}=    server3.Get Version    localhost    7002
    Log    server3 rxdebug version = ${version_server3}
    Set Suite Metadata   Server3 OpenAFS Version    ${version_server3}
