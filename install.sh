#!/bin/sh

PACKAGES="afsutil afsrobot OpenAFSLibrary"
OPT_VERBOSE="no"
DO_CHECK="no"

DIR_PREFIX="/usr/local"
DIR_ROOT="$DIR_PREFIX/afsrobotest"
DIR_HTML="$DIR_ROOT/html"
DIR_DOC="$DIR_HTML/doc"
DIR_LOG="$DIR_HTML/log"
DIR_OUTPUT="$DIR_HTML/output"

art_usage() {
    _progname=`basename $0`
    echo "usage: sudo ./$_progname [--verbose] [<target>]"
    echo ""
    echo "where <target> is one of:"
    echo "  all   - full install (default)"
    echo "  deps  - external dependencies"
    echo "  tests - test suites"
    echo "  doc   - generate docs"
    echo "  pkg   - python packages"
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
    # Install dependencies on Debian.
    echo "Installing python."
    art_run apt-get install -q -y python
    echo "Installing pip."
    art_run apt-get install -q -y python-pip
    echo "Installing argparse."
    art_run apt-get install -q -y python-argparse
    echo "Installing robotframework."
    art_run pip -q install robotframework
}

art_rhel_install_deps() {
    # Install dependencies on RHEL/CentOS.
    echo "Installing epel."
    art_run yum install -q -y epel-release
    echo "Installing python."
    art_run yum install -q -y python
    echo "Installing pip."
    art_run yum install -q -y python-pip
    echo "Installing argparse."
    art_run yum install -q -y python-argparse
    echo "Installing robotframework."
    art_run pip -q install robotframework
}

art_solaris_install_deps() {
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
        art_run pkgadd -a .pkgadd -d http://get.opencsw.org/now CSWpkgutil
        rm -f .pkgadd
    fi
    art_run /opt/csw/bin/pkgutil -U
    echo "Installing python 2.7."
    art_run /opt/csw/bin/pkgutil -y -i python27
    echo "Installing pip."
    art_run /opt/csw/bin/pkgutil -y -i py_pip
    echo "Installing argparse."
    art_run /opt/csw/bin/pkgutil -y -i py_argparse
    echo "Installing robotframework."
    art_run pip -q install robotframework
}

art_install_deps() {
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
    art_run mkdir -p $DIR_LOG
    art_run mkdir -p $DIR_OUTPUT
}

art_make_doc() {
    # Generate the library documentation. Requires robotframework.
    pypath=libraries/OpenAFSLibrary/OpenAFSLibrary
    input="$pypath"
    output="$DIR_DOC/OpenAFSLibary.html"
    echo "Generating documentation file $output."
    art_run mkdir -p $DIR_DOC
    art_run python -m robot.libdoc --format HTML --pythonpath $pypath $input $DIR_DOC/OpenAFSLibary.html
}

art_install_package() {
    ( cd libraries/$1 && ./install.sh )
}

art_install_packages() {
    for package in $PACKAGES
    do
        echo "Installing package ${package}."
        art_run art_install_package $package
    done
}

art_install_tests() {
    art_run mkdir -p $DIR_ROOT
    art_run cp -r tests/ $DIR_ROOT
    art_run cp -r resources/ $DIR_ROOT
}

while :; do
    case "$1" in
    -h|--help|help)
        art_usage
        break
        ;;
    -v|--verbose)
        OPT_VERBOSE="yes"
        shift
        ;;
    deps)
        art_install_deps
        shift
        ;;
    doc)
        art_make_doc
        break
        ;;
    pkg)
        art_install_packages
        DO_CHECK="yes"
        break
        ;;
    tests)
        art_install_tests
        art_make_output_dirs
        break
        ;;
    all|"")
        art_install_deps
        art_install_packages
        art_install_tests
        art_make_output_dirs
        art_make_doc
        DO_CHECK="yes"
        break
        ;;
    *)
        art_usage
        exit 1
        ;;
    esac
done

if [ "$DO_CHECK" = "yes" ]; then
    afsutil check
fi
