#!/bin/bash
# Copyright (c) 2014-2017, Sine Nomine Associates
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
set -e

# Get our installation path.
if [ -z "$AFSROBOT_ROOT" ]; then
    if [ $UID -ne 0 ]; then
        AFSROBOT_ROOT="$HOME/afsrobot"
    else
        if [ -d '/usr/local' ]; then
            AFSROBOT_ROOT='/usr/local/afsrobot'
        elif [ -d '/opt' ]; then
            AFSROBOT_ROOT='/opt/afsrobot'
        else
            echo "Please specify AFSROBOT_ROOT." >&2
            exit 1
        fi
    fi
fi

# Turn off annoying pip version warnings.
export PIP_DISABLE_PIP_VERSION_CHECK=1

remove_package() {
    package=$1
    if pip show --quiet $package; then
        pip uninstall -y $package
    fi
}

remove_dir() {
    dir=$1
    if [ -z "$dir" ]; then return; fi
    if [ "$dir" = "/" ]; then return; fi
    if [ ! -d "$dir" ]; then return; fi
    echo "Removing $dir"
    rm -rf "$dir"
}

# remove_package afsutil
remove_package afsrobot
remove_package OpenAFSLibrary

remove_dir "$AFSROBOT_ROOT/doc"
remove_dir "$AFSROBOT_ROOT/tests"
remove_dir "$AFSROBOT_ROOT/resources"

