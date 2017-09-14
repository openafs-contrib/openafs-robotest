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
AFSROBOT_ROOT=""
test -f /etc/afsrobot.rc && . /etc/afsrobot.rc

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
    test -n "$dir" || return
    test $dir != "/" || return
    test -d $dir || return
    echo "Removing $dir"
    rm -rf $dir
}

remove_package afsutil
remove_package afsrobot
remove_package OpenAFSLibrary
remove_dir "$AFSROBOT_ROOT"
rm -f /etc/afsrobot.rc
