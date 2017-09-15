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
# preq.sh - install system-wide prerequiests (as root).
#
# Run this script to detect the os type and install system prerequisites
# for commonly used systems. This should be run as root before running
# ./install.sh to install the tests and user files.
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
usage: sudo ./preq.sh [--help] [--username <username>] [--group <group>]
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

. setup/functions.sh

test $UID -eq 0 || die "Please run as root."
OS_ID=`detect_os`
test -f ./setup/$OS_ID || die "Sorry, no setup file found for '$OS_ID'."
echo "Running $OS_ID setup..."
./setup/$OS_ID || die "Failed to setup $OS_ID."
echo "Now run ./install.sh to install tests."
