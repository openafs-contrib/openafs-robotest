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

# Determine default value of --prefix
if [ $UID -ne 0 ]; then
    DEFAULT_PREFIX=$HOME
elif [ -d "/usr/local" ]; then
    DEFAULT_PREFIX="/usr/local"
elif [ -d "/opt" ]; then
    DEFAULT_PREFIX="/opt"
else
    DEFAULT_PREFIX="" # must be specified.
fi

OPT_QUIET="no"
OPT_VERBOSE="no"
OPT_PREFIX="$DEFAULT_PREFIX"
OPT_INSTALL_LIBS="no"
OPT_INSTALL_TESTS="no"
OPT_INSTALL_DOCS="no"

# Turn off annoying pip version warnings.
export PIP_DISABLE_PIP_VERSION_CHECK=1

die() {
    echo "$1" >&2
    exit 1
}

info() {
    if [ $OPT_QUIET = "no" ]; then
        echo "$1"
    fi
}

run() {
    if [ "$OPT_VERBOSE" = "yes" ]; then
        $@ || die "Command failed: $@"
    else
        $@ >/dev/null || die "Command failed: $@"
    fi
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
usage: sudo ./install.sh [--help] [--quiet] [--verbose] [--prefix <path>] [<component> [...]]

where:
   --help        display help then exit
   --quiet       no progress messages
   --verbose     more verbose output
   --prefix      installation path (default: $DEFAULT_PREFIX)
   <component>   valid components: libs, tests, docs (default: all)
EOF
}

while :; do
    case "$1" in
    -h|--help)    usage; exit 0;;
    -v|--verbose) OPT_VERBOSE="yes"; shift;;
    -q|--quiet)   OPT_QUIET="yes"; shift;;
    -p|--prefix)  OPT_PREFIX=`gopt prefix "$2"`; shift 2;;
    --)           break;;
    -?*)          echo "Unknown option: $1"; usage; exit 1;;
    *)            break;;
    esac
done
if [ $# -eq 0 ]; then
    OPT_INSTALL_LIBS="yes"
    OPT_INSTALL_TESTS="yes"
    OPT_INSTALL_DOCS="yes"
else
    for arg; do
        case "$arg" in
        lib|libs)   OPT_INSTALL_LIBS="yes" ;;
        test|tests) OPT_INSTALL_TESTS="yes" ;;
        doc|docs)   OPT_INSTALL_DOCS="yes" ;;
        *)          echo "Invalid component name: $arg" >&2; usage; exit 1;;
        esac
    done
fi

# Installation directories.
if [ -z "$OPT_PREFIX" ]; then
    die "Please specify an installation path with --prefix <path>."
fi
if [ ! -d "$OPT_PREFIX" ]; then
    mkdir -p "$OPT_PREFIX" || die "Cannot make --prefix directory $OPT_PREFIX."
fi

# Get paths to python and pip. Use the OpenCSW version if installed.
PYTHON=`PATH=/opt/csw/bin:$PATH which python`
PIP=`PATH=/opt/csw/bin:$PATH which pip`
test -x $PYTHON || die "python not found in PATH."
if [ $OPT_INSTALL_LIBS = "yes" ]; then
    test -x $PIP || die "pip not found in PATH."
fi

# Install.
AFSROBOT_ROOT="$OPT_PREFIX/afsrobot"
if [ $OPT_INSTALL_LIBS = "yes" ]; then
    info "Installing libraries"
    OPT_PIP="--upgrade --no-deps --no-index"
    if [ $UID -ne 0 ]; then
        OPT_PIP="$OPT_PIP --user"
    fi
    # xxx: afsutil needs to be run as root, so a --user install will not work.
    #      move to setup? use pypi?
    # run pip install $OPT_PIP libraries/afsutil
    run pip install $OPT_PIP libraries/afsrobot
    run pip install $OPT_PIP libraries/OpenAFSLibrary
fi
if [ $OPT_INSTALL_TESTS = "yes" ]; then
    info "Installing test suites"
    run mkdir -p $AFSROBOT_ROOT
    run cp -r tests/ $AFSROBOT_ROOT
    run cp -r resources/ $AFSROBOT_ROOT
fi
if [ $OPT_INSTALL_DOCS = "yes" ]; then
    info "Generating documentation"
    pypath=libraries/OpenAFSLibrary/OpenAFSLibrary
    input="$pypath"
    output="$AFSROBOT_ROOT/doc/OpenAFSLibary.html"
    run mkdir -p $(dirname $output)
    run $PYTHON -m robot.libdoc --format HTML --pythonpath $pypath $input $output
fi

if [ $UID -ne 0 ]; then
    # Create/update user configuration.
    afsrobot init
fi

info "Done"
