#!/bin/bash

PACKAGES="afsutil afsrobot OpenAFSLibrary"
OPT_VERBOSE="no"
OPT_ALLOW_USER="no"

DIR_PREFIX="/usr/local"
DIR_ROOT="$DIR_PREFIX/afsrobotest"
DIR_HTML="$DIR_ROOT/html"
DIR_DOC="$DIR_HTML/doc"
DIR_LOG="$DIR_HTML/log"
DIR_OUTPUT="$DIR_HTML/output"

art_usage() {
    _progname=`basename $0`
    echo "usage: ./$_progname [--user] [--verbose] [<target> ...]"
    echo ""
    echo "where <target> is:"
    echo "  all  - full install (default)"
    echo "  dep  - external dependencies"
    echo "  test - test suites"
    echo "  doc  - generate docs"
    echo "  pkg  - python packages"
}

art_run() {
    if [ "$OPT_VERBOSE" = "yes" ]; then
        $@ || exit 1
    else
        $@ >/dev/null || exit 1
    fi
}

art_detect_sysname() {
    # We might not have python yet, so we can't use python -m platform.
    case `uname` in
    Linux)
        if [ -f /etc/debian_version ]; then
            echo "linux-debian"
        elif [ -f /etc/centos-release ]; then
            echo "linux-centos"
        elif [ -f /etc/redhat-release ]; then
            echo "linux-rhel"
        else
            echo "linux-unknown"
        fi
        ;;
    SunOS)
        _osrel=`uname -r | sed 's/^5\.//'`
        echo "solaris-$_osrel"
        ;;
    *)
        echo "unknown"
        ;;
    esac
}

art_debian_install_deps() {
    # Install missing dependencies on Debian.
    if ! dpkg --status python >/dev/null 2>/dev/null; then
        echo "Installing python."
        art_run apt-get install -q -y python
    fi
    if ! dpkg --status python-pip >/dev/null 2>/dev/null; then
        echo "Installing pip."
        art_run apt-get install -q -y python-pip
    fi
    # argparse has been pulled into the python core package on
    # modern systems, but it a separate package on older systems.
    if ! python -c 'import argparse' >/dev/null 2>/dev/null; then
        echo "Installing argparse."
        art_run apt-get install -q -y python-argparse
    fi
    if ! python -c 'import robot.api' >/dev/null 2>/dev/null; then
        echo "Installing robotframework."
        art_run pip -q install robotframework
    fi
}

art_rhel_install_deps() {
    # Install missing dependencies on RHEL/CentOS.
    if ! rpm -q epel-release >/dev/null 2>/dev/null; then
        echo "Installing epel."
        art_run yum install -q -y epel-release
    fi
    if ! rpm -q python >/dev/null 2>/dev/null; then
        echo "Installing python."
        art_run yum install -q -y python
    fi
    if ! rpm -q python-pip >/dev/null 2>/dev/null; then
        echo "Installing pip."
        art_run yum install -q -y python-pip
    fi
    # argparse has been pulled into the python core package on
    # modern systems, but it a separate package on older systems.
    if ! python -c 'import argparse' >/dev/null 2>/dev/null; then
        echo "Installing argparse."
        art_run yum install -q -y python-argparse
    fi
    if ! python -c 'import robot.api' >/dev/null 2>/dev/null; then
        echo "Installing robotframework."
        art_run pip -q install robotframework
    fi
}

art_solaris_install_deps() {
    # Install dependencies on Solaris.
    DID_UPDATE='no'
    if [ ! -x /opt/csw/bin/pkgutil ]; then
        cat <<_EOF_ >/tmp/pkgadd-conf-$$
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
        art_run pkgadd -a /tmp/pkgadd-conf-$$ -d http://get.opencsw.org/now CSWpkgutil
        rm -f /tmp/pkgadd-conf-$$
    fi
    if ! /opt/csw/bin/pkgutil --list | grep '^CSWpython27$' >/dev/null; then
        echo "Installing python 2.7."
        if [ $DID_UPDATE = 'no' ]; then
            art_run /opt/csw/bin/pkgutil -U
            DID_UPDATE='yes'
        fi
        art_run /opt/csw/bin/pkgutil -y -i python27
    fi
    if ! /opt/csw/bin/pkgutil --list | grep '^CSWpy-pip$' >/dev/null; then
        echo "Installing pip."
        if [ $DID_UPDATE = 'no' ]; then
            art_run /opt/csw/bin/pkgutil -U
            DID_UPDATE='yes'
        fi
        art_run /opt/csw/bin/pkgutil -y -i py_pip
    fi
    if ! /opt/csw/bin/pkgutil --list | grep '^CSWpy-argparse$' >/dev/null; then
        echo "Installing argparse."
        if [ $DID_UPDATE = 'no' ]; then
            art_run /opt/csw/bin/pkgutil -U
            DID_UPDATE='yes'
        fi
        art_run /opt/csw/bin/pkgutil -y -i py_argparse
    fi
    if ! python -c 'import robot.api' >/dev/null 2>/dev/null; then
        echo "Installing robotframework."
        art_run pip -q install robotframework
    fi
}

art_install_deps() {
    echo "Checking dependencies."
    sysname=`art_detect_sysname`
    case "$sysname" in
    linux-debian*)
        art_debian_install_deps
        ;;
    linux-centos*|linux-rhel*)
        art_rhel_install_deps
        ;;
    solaris-10*|solaris-11*)
        art_solaris_install_deps
        ;;
    *)
        echo "WARNING: Unable to install deps on unknown platform: $sysname" >&2
        ;;
    esac
}

art_make_output_dirs() {
    echo "Making output directories."
    art_run mkdir -p $DIR_LOG
    art_run mkdir -p $DIR_OUTPUT
}

art_make_doc() {
    echo "Generating documentation."
    # Generate the library documentation. Requires robotframework.
    pypath=libraries/OpenAFSLibrary/OpenAFSLibrary
    input="$pypath"
    output="$DIR_DOC/OpenAFSLibary.html"
    if [ "$OPT_VERBOSE" = "yes" ]; then
        echo "Writing file $output"
    fi
    art_run mkdir -p $DIR_DOC
    art_run python -m robot.libdoc --format HTML --pythonpath $pypath $input $DIR_DOC/OpenAFSLibary.html
}

art_install_package() {
    ( cd libraries/$1 && ./install.sh )
}

art_install_packages() {
    echo "Installing our packages."
    for package in $PACKAGES
    do
        echo "  Installing package ${package}."
        art_run art_install_package $package
    done
}

art_install_tests() {
    echo "Installing test suites."
    art_run mkdir -p $DIR_ROOT
    art_run cp -r tests/ $DIR_ROOT
    art_run cp -r resources/ $DIR_ROOT
}

SEEN=""
while :; do
    case "$1" in
    "")
        break
        ;;
    -h|--help)
        art_usage
        exit 0
        ;;
    -u|--user)
        OPT_ALLOW_USER="yes"
        shift
        ;;
    -v|--verbose)
        OPT_VERBOSE="yes"
        shift
        ;;
    dep|doc|pkg|test)
        SEEN="$SEEN:$1:"
        shift
        ;;
    all)
        SEEN="$SEEN:dep:doc:pkg:test:"
        shift
        ;;
    *)
        art_usage
        exit 1
        ;;
    esac
done

# Avoid accidental local installs by requiring --user when
# not run by root.
if [ `python -c 'import os; print os.getuid()'` -ne 0 ]; then
    if [ "$OPT_ALLOW_USER" = "no" ]; then
        echo "Please run as root, or give the --user option for a local installation."
        exit 1
    fi
fi

# Install specified targets.
if [ -z $SEEN ]; then
    SEEN=":dep:doc:pkg:test:"  # Install all by default.
fi
for TARGET in "dep" "pkg" "test" "doc"
do
    if echo "$SEEN" | grep -q ":$TARGET:"; then
        case "$TARGET" in
        dep)    art_install_deps ;;
        pkg)    art_install_packages ;;
        test)   art_install_tests ;;
        doc)    art_make_doc ;;
        esac
    fi
done

# Post install steps.
if echo "$SEEN" | grep -q ":test:"; then
    art_make_output_dirs
fi
if echo "$SEEN" | grep -q ":pkg:"; then
    afsutil check
fi
echo "Done."
