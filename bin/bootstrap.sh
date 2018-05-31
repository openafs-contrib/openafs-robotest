#!/bin/bash
# Copyright (c) 2017, Sine Nomine Associates
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#
#------------------------------------------------------------------------
#
# bootstrap.sh - build and test a trivial OpenAFS cell
#
#   * detect the os type and install prerequisites
#   * install openafs-robotest
#   * clone the OpenAFS git repo and build OpenAFS
#   * install the OpenAFS client and servers
#   * create a AFS cell for testing
#   * run the test suites as the test user
#
#------------------------------------------------------------------------
set -e
AFSROBOT_USERNAME='afsrobot'
AFSROBOT_GROUP='testers'
AFSROBOT_IFDEVICE=
AFSROBOT_CREDS='/root/creds'

die() {
    echo "$*" >&2
    exit 1
}

gopt() {
    if [ -z "$2" ]; then
        echo "Option --$1 requires an argument." >&2
        exit 1
    fi
    echo "$2"
}

usage() {
    cat <<EOF
usage: sudo ./bootstrap.sh [--help] [--username <username>] [--group <group>]
                           [--ifdevice <device>] [--creds <location>]

where:
   --help        display help then exit
   --username    username to be created (default: afsrobot)
   --group       group to be created (default: testers)
   --ifdevice    network link device, e.g., eth0 (default: detect)
   --creds       path or url to package credentials (default: /root/creds)
EOF
}

while :; do
    case "$1" in
    -h|--help)     usage; exit 0 ;;
    -u|--username) AFSROBOT_USERNAME=`gopt username "$2"`; shift 2 ;;
    -g|--group)    AFSROBOT_GROUP=`gopt group "$2"`; shift 2 ;;
    -i|--ifdevice) AFSROBOT_IFDEVICE=`gopt ifdevice "$2"`; shift 2 ;;
    -c|--creds)    AFSROBOT_CREDS=`gopt creds "$2"`; shift 2 ;;
    --)            break;;
    -?*)           echo "Unknown option: $1"; usage; exit 1;;
    *)             break;;
    esac
done
export AFSROBOT_USERNAME
export AFSROBOT_GROUP
export AFSROBOT_IFDEVICE
export AFSROBOT_CREDS

make install       || die "install failed"

echo "Installing build tools..."
afsutil getdeps --creds $AFSROBOT_CREDS || die "Failed to install build tools."

sudo -u $AFSROBOT_USERNAME -i <<'EOF'
#!/bin/bash
set -e
set -x

HOSTNAME=`hostname`
BINDIR="/usr/local/bin"
DISTDIR="$HOME/dist"
REPO="https://github.com/openafs/openafs.git"
BRANCH="master"

echo "Building openafs; this will take a while..."
TMPDIR=`mktemp -d -p /var/tmp`
trap "cd $HOME; rm -rf $TMPDIR; exit" 0 1 2 3 15
cd $TMPDIR
git clone -q $REPO openafs
cd openafs
git reset --hard origin/openafs-stable-1_6_x
afsutil build --log $HOME/build-aklog.log --target aklog
mkdir -p $HOME/bin
cp src/aklog/aklog $HOME/bin/aklog-1.6
git clean -f -d -x -q
git reset --hard origin/$BRANCH
mkdir -p $DISTDIR
afsutil build --log $HOME/build-${BRANCH}.log --tarball $DISTDIR/openafs-${BRANCH}.tar.gz
cd $HOME
rm -rf $TMPDIR

afsrobot init
afsrobot config set variables aklog $HOME/bin/aklog-1.6
afsrobot config set host:$HOSTNAME installer transarc
afsrobot config set host:$HOSTNAME dest $DISTDIR/openafs-${BRANCH}.tar.gz

afsrobot setup
afsrobot run
afsrobot teardown
EOF
