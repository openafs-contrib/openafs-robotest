#!/bin/bash
set -e
set -x

rm -f ~/afsrobot/afsrobot.cfg
afsrobot init --quiet
afsrobot config set test aklog /usr/local/bin/aklog-1.6
afsrobot config set host.0 installer transarc
afsrobot config set host.0 dest ~/src/openafs/amd64_linux26/dest
afsrobot config set host.1 name deb9a
afsrobot config set host.1 installer transarc
afsrobot config set host.1 dest ~/src/openafs/amd64_linux26/dest
afsrobot config set host.1 dafileserver "-d 10"
afsrobot config set cell fs mantis,deb9a

afsrobot setup
afsrobot test
afsrobot teardown
