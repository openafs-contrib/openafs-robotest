#!/bin/sh

PROGNAME=`basename $0`
TARGETS=""
VERBOSE="no"
PACKAGES="afsutil afsrobot OpenAFSLibrary"

DIR_PREFIX="/usr/local"
DIR_ROOT="$DIR_PREFIX/afsrobotest"
DIR_HTML="$DIR_ROOT/html"
DIR_DOC="$DIR_HTML/doc"
DIR_LOG="$DIR_HTML/log"
DIR_OUTPUT="$DIR_HTML/output"

usage() {
    echo "usage: sudo $PROGNAME [--verbose] [<target>]"
    echo ""
    echo "where <target> is one of:"
    echo "  all   - full install (default)"
    echo "  deps  - external dependencies"
    echo "  tests - test suites"
    echo "  doc   - generate docs"
    echo "  pkg   - python packages"
}

_run() {
    if [ "$VERBOSE" = "yes" ]; then
        $@ || exit 1
    else
        $@ >/dev/null || exit 1
    fi
}

_detect_sysname() {
    # We might not have python yet, so we can't use python -m platform.
    case `uname` in
    Linux)
        if [ -f /etc/debian_version ]; then
            sysname="linux-debian"
        elif [ -f /etc/centos-release ]; then
            sysname="linux-centos"
        elif [ -f /etc/redhat-release ]; then
            sysname="linux-rhel"
        else
            sysname="linux-unknown"
        fi
        ;;
    SunOS)
        osrel=`uname -r | sed 's/^5\.//'`
        sysname="solaris-$osrel"
        ;;
    *)
        syname="unknown"
        ;;
    esac
    echo "$sysname"
}

_debian_install_deps() {
    # Install dependencies on Debian.
    echo "Installing python."
    _run apt-get install -q -y python
    echo "Installing pip."
    _run apt-get install -q -y python-pip
    echo "Installing argparse."
    _run apt-get install -q -y python-argparse
    echo "Installing robotframework."
    _run pip -q install robotframework
}

_rhel_install_deps() {
    # Install dependencies on RHEL/CentOS.
    echo "Installing epel."
    _run yum install -q -y epel-release
    echo "Installing python."
    _run yum install -q -y python
    echo "Installing pip."
    _run yum install -q -y python-pip
    echo "Installing argparse."
    _run yum install -q -y python-argparse
    echo "Installing robotframework."
    _run pip -q install robotframework
}

_solaris_install_deps() {
    # Install dependencies on Solaris.
    if [ ! -x /opt/csw/bin/pkgutil ]; then
        cat <<_EOF_ >.pkgadd
mail=
instance=overwrite
partial=nocheck
runlevel=nocheck
idepend=nocheck
rdepend=nocheck
space=nocheck
setuid=nocheck
conflict=nocheck
action=nocheck
networktimeout=60
networkretries=3
authentication=quit
keystore=/var/sadm/security
proxy=
basedir=default
_EOF_
        echo "Installing OpenCSW pkgutil."
        _run pkgadd -a .pkgadd -d http://get.opencsw.org/now CSWpkgutil
        rm -f .pkgadd
    fi
    _run /opt/csw/bin/pkgutil -U
    echo "Installing python 2.7."
    _run /opt/csw/bin/pkgutil -y -i python27
    echo "Installing pip."
    _run /opt/csw/bin/pkgutil -y -i py_pip
    echo "Installing argparse."
    _run /opt/csw/bin/pkgutil -y -i py_argparse
    echo "Installing robotframework."
    _run pip -q install robotframework
}

install_deps() {
    sysname=`_detect_sysname`
    case "$sysname" in
    linux-debian*)
        _debian_install_deps
        ;;
    linux-centos*|linux-rhel*)
        _rhel_install_deps
        ;;
    solaris-10*|solaris-11*)
        _solaris_install_deps
        ;;
    *)
        echo "WARNING: Unable to install deps on unknown platform: $sysname" >&2
        ;;
    esac
}

make_output_dirs() {
    _run mkdir -p $DIR_LOG
    _run mkdir -p $DIR_OUTPUT
}

make_doc() {
    # Generate the library documentation. Requires robotframework.
    pypath=libraries/OpenAFSLibrary/OpenAFSLibrary
    input="$pypath"
    output="$DIR_DOC/OpenAFSLibary.html"
    echo "Generating documentation file $output."
    _run mkdir -p $DIR_DOC
    _run python -m robot.libdoc --format HTML --pythonpath $pypath $input $DIR_DOC/OpenAFSLibary.html
}

make_sdist() {
    package=$1
    _run rm -f libraries/$package/dist/*  # Remove any old versions.
    echo "Creating source distribution for package '${package}'."
    ( cd libraries/${package} && python setup.py $VERBOSITY sdist --formats gztar ) || exit 1
}

install_package() {
    package=$1
    ( cd libraries/$package && ./install.sh ) || exit 1
}

make_sdists() {
    for package in $PACKAGES
    do
        _run make_sdist $package
    done
}

install_packages() {
    for package in $PACKAGES
    do
        echo "Installing package ${package}."
        _run install_package $package
    done
}

install_tests() {
    _run mkdir -p $DIR_ROOT
    _run cp -r tests/ $DIR_ROOT
    _run cp -r resources/ $DIR_ROOT
}

while :; do
    case "$1" in
    -h|--help|help)
        usage
        break
        ;;
    -v|--verbose)
        VERBOSE="yes"
        shift
        ;;
    deps)
        install_deps
        shift
        ;;
    doc)
        make_doc
        break
        ;;
    pkg)
        install_packages
        break
        ;;
    tests)
        install_tests
        make_output_dirs
        break
        ;;
    all|"")
        install_deps
        install_packages
        install_tests
        make_output_dirs
        make_doc
        break
        ;;
    *)
        usage
        exit 1
        ;;
    esac
done
