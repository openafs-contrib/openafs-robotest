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

DEFAULT_PREFIX="/usr/local"
test -d $DEFAULT_PREFIX || DEFAULT_PREFIX="/opt"
test -d $DEFAULT_PREFIX || DEFAULT_PREFIX=""

OPT_QUIET="no"
OPT_VERBOSE="no"
OPT_PREFIX=$DEFAULT_PREFIX
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

# Pre install check.
if [ $UID -ne 0 ]; then
    die "Please run as root."
fi

# Get paths to python and pip. Use the OpenCSW version if installed.
PYTHON=`PATH=/opt/csw/bin:$PATH which python`
PIP=`PATH=/opt/csw/bin:$PATH which pip`

# Installation directories.
if [ -z "$OPT_PREFIX" ]; then
    echo "Please specify an installation path with --prefix <path>." >&2
    exit 1
fi
AFSROBOTEST_ROOT="$OPT_PREFIX/afsrobotest"

# Save our paths for regular users and the uninstall.
cat <<__EOF__ >/etc/afsrobotest.rc
AFSROBOTEST_ROOT="$AFSROBOTEST_ROOT"
__EOF__

test -d $OPT_PREFIX || die "--prefix $OPT_PREFIX does not exist."
test -x $PYTHON || die "python not found in PATH."
if [ $OPT_INSTALL_LIBS = "yes" ]; then
    test -x $PIP || die "pip not found in PATH."
fi

# Install.
if [ $OPT_INSTALL_LIBS = "yes" ]; then
    info "Installing libraries"
    run pip install --upgrade --no-deps --no-index libraries/afsutil
    run pip install --upgrade --no-deps --no-index libraries/afsrobot
    run pip install --upgrade --no-deps --no-index libraries/OpenAFSLibrary
fi
if [ $OPT_INSTALL_TESTS = "yes" ]; then
    info "Installing test suites"
    run mkdir -p $AFSROBOTEST_ROOT
    run cp -r tests/ $AFSROBOTEST_ROOT
    run cp -r resources/ $AFSROBOTEST_ROOT
fi
if [ $OPT_INSTALL_DOCS = "yes" ]; then
    info "Generating documentation"
    pypath=libraries/OpenAFSLibrary/OpenAFSLibrary
    input="$pypath"
    output="$AFSROBOTEST_ROOT/doc/OpenAFSLibary.html"
    run mkdir -p $(dirname $output)
    run $PYTHON -m robot.libdoc --format HTML --pythonpath $pypath $input $output
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
