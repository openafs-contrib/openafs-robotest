# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Volserver/vlserver tests
Resource          openafs.robot

*** Variables ***
${SERVER}      ${HOSTNAME}
${VOLID}       0

*** Keywords ***

# TODO move these to the library

Volume Should Exist
    [Arguments]  ${name}  ${server}=*  ${part}=*
    Log  todo

Volume Should Not Exist
    [Arguments]  ${name}  ${server}=*  ${part}=*
    Log  todo

Volume Should Be Locked
    [Arguments]  ${name}
    Log  todo

Volume Should Be Unlocked
    [Arguments]  ${name}
    Log  todo

RO Site Should Exist
    [Arguments]  ${name}  ${server}=*  ${part}=*
    Log  todo

RO Site Should Not Exist
    [Arguments]  ${name}  ${server}=*  ${part}=*
    Log  todo

RW Site Should Exist
    [Arguments]  ${name}  ${server}=*  ${part}=*
    Log  todo

RW Site Should Not Exist
    [Arguments]  ${name}  ${server}=*  ${part}=*
    Log  todo


*** Test Cases ***
Create a Volume
    [Tags]  arla  #(voscreate)
    [Setup]     Login  ${AFS_ADMIN}
    [Teardown]  Run Keywords  Remove Volume  test.create
    ...         AND           Logout
    Volume Should Not Exist  test.create
    Command Should Succeed   ${VOS} create ${SERVER} a test.create
    Volume Should Exist      test.create  server=${SERVER}  part=a

Move a Volume
    [Tags]  arla  #(vosmove)
    [Setup]     Run Keywords  Login  ${AFS_ADMIN}
    ...         AND           Create Volume  ${SERVER}  a  test.move
    [Teardown]  Run Keywords  Remove Volume  test.move
    ...         AND           Logout
    Command Should Succeed   ${VOS} move test.move ${SERVER} a ${SERVER} b
    Volume Should Exist      test.move  server=${SERVER}  part=b
    Volume Should Not Exist  test.move  server=${SERVER}  part=a

Add a Replication Site
    [Tags]  arla  #(vosaddsite)
    [Setup]     Run Keywords  Login  ${AFS_ADMIN}
    ...         AND           Create Volume  ${SERVER}  a  test.add
    [Teardown]  Run Keywords  Command Should Succeed    ${VOS} remsite ${SERVER} a test.add
    ...         AND           Remove Volume  test.add
    ...         AND           Logout
    Command Should Succeed  ${VOS} addsite ${SERVER} a test.add
    RO Site Should Exist    test.add  server=${SERVER}  part=a

Release a Volume
    [Tags]  arla  #(vosrelease)
    [Setup]     Run Keywords  Login  ${AFS_ADMIN}
    ...         AND           Create Volume  ${SERVER}  a  test.rel
    [Teardown]  Run Keywords  Command Should Succeed    ${VOS} remove ${SERVER} a test.rel.readonly
    ...         AND           Remove Volume  test.rel
    ...         AND           Logout
    Command Should Succeed  ${VOS} addsite ${SERVER} a test.rel
    Command Should Succeed  ${VOS} release test.rel
    RO Site Should Exist    test.rel           server=${SERVER}  part=a
    Volume Should Exist     test.rel.readonly  server=${SERVER}  part=a

Remove a Replication Site
    [Tags]  arla  #(vosremsite)
    [Setup]     Run Keywords  Login  ${AFS_ADMIN}
    ...         AND           Create Volume  ${SERVER}  a  test.rem
    ...         AND           Command Should Succeed    ${VOS} addsite ${SERVER} a test.rem
    ...         AND           Command Should Succeed    ${VOS} release test.rem
    [Teardown]  Run Keywords  Command Should Succeed    ${VOS} remove ${SERVER} a test.rem.readonly
    ...         AND           Remove Volume  test.rem
    ...         AND           Logout
    Command Should Succeed    ${VOS} remsite ${SERVER} a test.rem
    RO Site Should Not Exist  test.rem ${SERVER} a
    Volume Should Exist       test.rem.readonly ${SERVER} a

Remove a Replicated Volume
    [Tags]  arla  #(vosremove)
    [Setup]     Run Keywords  Login  ${AFS_ADMIN}
    ...         AND           Create Volume  ${SERVER}  a  test.rem.2
    ...         AND           Command Should Succeed    ${VOS} addsite ${SERVER} a test.rem.2
    ...         AND           Command Should Succeed    ${VOS} release test.rem.2
    [Teardown]  Logout
    Command Should Succeed    ${VOS} remove ${SERVER} a -id test.rem.2.readonly
    Command Should Succeed    ${VOS} remove -id test.rem.2
    Volume Should Not Exist   test.rem.2.readonly  server=${SERVER}  part=a
    Volume Should Exist       test.rem.2           server=${SERVER}  part=a

Delete a VLDB Entry
    [Tags]  todo  arla  #(vosdelentry)
    [Setup]     Run Keywords  Login  ${AFS_ADMIN}
    ...         AND           Create Volume  ${SERVER}  a  test.delent
    [Teardown]  Run Keywords  Command Should Succeed  ${VOS} zap -server ${SERVER} -part a -id ${VOLID}
    ...         AND           Logout
    Command Should Succeed    ${VOS} delentry test.delent
    RW Site Should Not Exist  test.delent  server=${SERVER}  part=a
    Volume Should Exist       test.delent  server=${SERVER}  part=a

Synchronize VLDB to Volumes
    [Tags]  todo  arla  #(vossyncvldb)
    [Setup]     Login  ${AFS_ADMIN}
    [Teardown]  Logout
    Command Should Succeed  ${VOS} syncserv ${SERVER} a

Zap a Volume
    [Tags]  todo  arla  #(voszap)
    [Setup]     Run Keywords  Login  ${AFS_ADMIN}
    ...         AND           Create Volume  ${VOLUME}  a  test.zap
    [Teardown]  Logout
    Command Should Succeed  ${VOS} zap -server ${SERVER} -part a -id ${VOLID}

Synchronize Volumes to VLDB
    [Tags]  todo  arla  #(vossyncserv)
    [Setup]     Login  ${AFS_ADMIN}
    [Teardown]  Logout
    Command Should Succeed  ${VOS} syncserv ${SERVER} a

Lock a VLDB Entry
    [Tags]  todo  arla  #(voslock)
    [Setup]     Run Keywords  Login  ${AFS_ADMIN}
    ...         AND           Create Volume  ${SERVER}  a  test.lock
    [Teardown]  Run Keywords  Remove Volume  test.lock
    ...         AND           Logout
    Command Should Succeed  ${VOS} lock test.lock

Unlock a VLDB Entry
    [Tags]  todo  arla  #(vosunlock)
    [Setup]     Run Keywords  Login  ${AFS_ADMIN}
    ...         AND           Create Volume  ${SERVER}  a  test.unlock
    ...         AND           Command Should Succeed    ${VOS} lock test.unlock
    [Teardown]  Run Keywords  Remove Volume  test.unlock
    ...         AND           Logout
    Volume Should Be Locked    test.unlock
    Command Should Succeed     ${VOS} unlock test.unlock
    Volume Should Be UnLocked  test.unlock


Unlock all VLDB Entries After Locking One or More
    [Tags]  todo  arla  #(vosunlockall)
    [Setup]     Run Keywords  Login  ${AFS_ADMIN}
    ...         AND           Create Volume  ${SERVER}  a  test.lock.1
    ...         AND           Create Volume  ${SERVER}  a  test.lock.2
    [Teardown]  Run Keywords  Remove Volume  test.unlock
    ...         AND           Logout
    Command Should Succeed     ${VOS} lock test.lock.1
    Command Should Succeed     ${VOS} lock test.lock.2
    Volume Should Be Locked    test.lock.1
    Volume Should Be Locked    test.lock.2
    Command Should Succeed     ${VOS} unlockvldb ${SERVER}
    Volume Should Be Unlocked  test.lock.1
    Volume Should Be Unlocked  test.lock.2

Rename a Volume
    [Tags]  todo  arla  #(vosrename)
    [Setup]     Run Keywords  Login  ${AFS_ADMIN}
    ...         AND           Create Volume  ${SERVER}  a  test.rename.1
    [Teardown]  Run Keywords  Remove Volume  test.rename.2
    ...         AND           Logout
    Command Should Succeed  ${VOS} rename test.rename.1 test.rename.2

List All Volumes On A Partition
    [Tags]  todo  arla  #(voslistvol)
    TODO
    # my ($host, $ret, %vols, $lvol, %vol);
    # $host = `hostname`;
    # &AFS_Init();
    #
    # %vols = &AFS_vos_listvol("localhost","b",);
    # $lvol=$vols{'testvol3'};
    # %vol=%$lvol;
    # # if it worked it worked...
    # if ($vol{'part'} ne "b") {
    #     exit(1);
    # }
    # exit(0);

List VLDB
    [Tags]  todo  arla  #(voslistvldb)
    TODO
    # my ($host, $ret, %vols, $lvol, %vol);
    # $host = `hostname`;
    # &AFS_Init();
    #
    # %vols = &AFS_vos_listvldb(undef,"localhost","b",,);
    # $lvol=$vols{'testvol3'};
    # %vol=%$lvol;
    # # if it worked it worked...
    # if ($vol{'rwpart'} ne "b") {
    #     exit(1);
    # }
    # exit(0);


Get Partition Info
    [Tags]  todo  arla  #(vospartinfo)
    TODO
    #%info = &AFS_vos_partinfo("localhost",,);
    #

List Partitions
    [Tags]  todo  arla  #(voslistpart)
    TODO
    #my ($host, $ret, @parts, $count);
    #$host = `hostname`;
    #&AFS_Init();
    #
    #@parts = &AFS_vos_listpart("localhost",);
    #$ret = shift(@parts);
    #if ($ret ne "a") {
    #    exit (1);
    #}
    #$ret = shift(@parts);
    #if ($ret ne "b") {
    #    exit (1);
    #}
    #exit(0);

Backup a Volume
    [Tags]  todo  arla  #(vosbackup)
    [Setup]     Run Keywords  Login  ${AFS_ADMIN}
    ...         AND           Create Volume  ${SERVER}  a  test.bk
    [Teardown]  Run Keywords  Remove Volume  test.bk
    ...         AND           Logout
    Command Should Succeed  ${VOS} backup test.bk

Examine a Volume
    [Tags]  todo  arla  #(vosexamine)
    TODO
    # %info = &AFS_vos_examine("rep",);
    # if ($info{'rwpart'} ne "a") {
    #     exit 1;
    # }
    #
    # $ret = $info{'rosites'};
    # @rosites = @$ret;
    # while ($ret = pop(@rosites)) {
    #     @rosite = @$ret;
    #     if ($rosite[1] ne "a") {
    # 	exit 1;
    #     }
    # }
    #
    #exit(0);

