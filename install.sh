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

OPT_QUIET="no"
OPT_VERBOSE="no"
OPT_PREFIX="/usr/local"
OPT_INSTALL_LIBS="no"
OPT_INSTALL_TESTS="no"
OPT_INSTALL_DOCS="no"

# Turn off annoying pip version warnings.
PIP_DISABLE_PIP_VERSION_CHECK=1

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
   --prefix      installation path (default: /usr/local)
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
DIR_ROOT="$OPT_PREFIX/afsrobotest"
DIR_HTML="$DIR_ROOT/html"
DIR_DOC="$DIR_HTML/doc"
DIR_LOG="$DIR_HTML/log"
DIR_OUTPUT="$DIR_HTML/output"

# Get paths to python and pip. Use the OpenCSW version if installed.
PYTHON=`PATH=/opt/csw/bin:$PATH which python`
PIP=`PATH=/opt/csw/bin:$PATH which pip`

# Pre install check.
if [ $UID -ne 0 ]; then
    die "Please run as root."
fi
test -d $OPT_PREFIX || die "--prefix $OPT_PREFIX does not exist."
test -x $PYTHON || die "python not found in PATH."
if [ $OPT_INSTALL_LIBS = "yes" ]; then
    test -x $PIP || die "pip not found in PATH."
fi

# Install.
if [ $OPT_INSTALL_LIBS = "yes" ]; then
    info "Installing libraries"
    run pip install libraries/afsutil
    run pip install libraries/afsrobot
    run pip install libraries/OpenAFSLibrary
fi
if [ $OPT_INSTALL_TESTS = "yes" ]; then
    info "Installing test suites"
    run mkdir -p $DIR_ROOT
    run cp -r tests/ $DIR_ROOT
    run cp -r resources/ $DIR_ROOT
    info "Making output directories"
    run mkdir -p $DIR_LOG
    run mkdir -p $DIR_OUTPUT
fi
if [ $OPT_INSTALL_DOCS = "yes" ]; then
    info "Generating documentation"
    pypath=libraries/OpenAFSLibrary/OpenAFSLibrary
    input="$pypath"
    output="$DIR_DOC/OpenAFSLibary.html"
    run mkdir -p $DIR_DOC
    run $PYTHON -m robot.libdoc --format HTML --pythonpath $pypath $input $DIR_DOC/OpenAFSLibary.html
fi

# Post install checks.
if [ $OPT_INSTALL_LIBS = "yes" ]; then
    # Work-around for OpenCSW pip on Solaris 10 to avoid the need to
    # mess with the PATH.
    for cli in afsutil afsrobot afs-robotest; do
        if [ -x /opt/csw/bin/$cli ]; then
            test -h /usr/bin/$cli && rm -f /usr/bin/$cli
            test -f /usr/bin/$cli || ln -s /opt/csw/bin/$cli /usr/bin/$cli
        fi
    done

    # Verify system setup.
    afsutil check || echo "Try: sudo afsutil check --fix-hosts"
fi

info "Done"
