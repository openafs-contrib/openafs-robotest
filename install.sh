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

usage() {
    _progname=`basename $0`
    echo "usage: ./$_progname [--user] [--verbose] [<target> ...]"
    echo ""
    echo "where <target> is:"
    echo "  all   - full install (default)"
    echo "  deps  - external dependencies"
    echo "  tests - test suites"
    echo "  docs  - generate docs"
    echo "  libs  - libraries"
}

run() {
    if [ "$OPT_VERBOSE" = "yes" ]; then
        $@ || exit 1
    else
        $@ >/dev/null || exit 1
    fi
}

detect_sysname() {
    # We might not have python yet, so we can't use python -m platform.
    local sname=`uname -s`
    local rname=`uname -r`
    local vname=`uname -v`
    case $sname in
    Linux)
        if [ -f /etc/debian_version ]; then
            echo "linux-debian"
        elif [ -f /etc/fedora-release ]; then
            echo "linux-fedora"
        elif [ -f /etc/centos-release ]; then
            echo "linux-centos"
        elif [ -f /etc/redhat-release ]; then
            echo "linux-rhel"
        else
            echo "unknown"
        fi
        ;;
    SunOS)
        case $rname in
        5.10)
            echo "solaris-10"
            ;;
        5.11)
            echo "solaris-$vname"
            ;;
        *)
            echo "unknown"
            ;;
        esac
        ;;
    *)
        echo "unknown"
        ;;
    esac
}

debian_install_deps() {
    # Install missing dependencies on Debian.
    if ! dpkg --status python >/dev/null 2>/dev/null; then
        echo "Installing python."
        run apt-get install -q -y python
    fi
    if ! dpkg --status python-pip >/dev/null 2>/dev/null; then
        echo "Installing pip."
        run apt-get install -q -y python-pip
    fi
    # argparse has been pulled into the python core package on
    # modern systems, but it a separate package on older systems.
    if ! python -c 'import argparse' >/dev/null 2>/dev/null; then
        echo "Installing argparse."
        run apt-get install -q -y python-argparse
    fi
    if ! python -c 'import robot.api' >/dev/null 2>/dev/null; then
        echo "Installing robotframework."
        run pip -q install robotframework
    fi
}

fedora_install_deps() {
    # Install missing dependencies on Fedora.
    if ! rpm -q python >/dev/null 2>/dev/null; then
        echo "Installing python."
        run dnf install -q -y python
    fi
    if ! rpm -q python-pip >/dev/null 2>/dev/null; then
        echo "Installing pip."
        run dnf install -q -y python-pip
    fi
    if ! python -c 'import robot.api' >/dev/null 2>/dev/null; then
        echo "Installing robotframework."
        run pip -q install robotframework
    fi
}

rhel_install_deps() {
    # Install missing dependencies on RHEL/CentOS.
    if ! rpm -q epel-release >/dev/null 2>/dev/null; then
        echo "Installing epel."
        run yum install -q -y epel-release
    fi
    if ! rpm -q python >/dev/null 2>/dev/null; then
        echo "Installing python."
        run yum install -q -y python
    fi
    if ! rpm -q python-pip >/dev/null 2>/dev/null; then
        echo "Installing pip."
        run yum install -q -y python-pip
    fi
    # argparse has been pulled into the python core package on
    # modern systems, but it a separate package on older systems.
    if ! python -c 'import argparse' >/dev/null 2>/dev/null; then
        echo "Installing argparse."
        run yum install -q -y python-argparse
    fi
    if ! python -c 'import robot.api' >/dev/null 2>/dev/null; then
        echo "Installing robotframework."
        run pip -q install robotframework
    fi
}

solaris10_install_deps() {
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
        run pkgadd -a /tmp/pkgadd-conf-$$ -d http://get.opencsw.org/now CSWpkgutil
        rm -f /tmp/pkgadd-conf-$$
    fi
    if ! /opt/csw/bin/pkgutil --list | grep '^CSWpython27$' >/dev/null; then
        echo "Installing python 2.7."
        if [ $DID_UPDATE = 'no' ]; then
            run /opt/csw/bin/pkgutil -U
            DID_UPDATE='yes'
        fi
        run /opt/csw/bin/pkgutil -y -i python27
    fi
    if ! /opt/csw/bin/pkgutil --list | grep '^CSWpy-pip$' >/dev/null; then
        echo "Installing pip."
        if [ $DID_UPDATE = 'no' ]; then
            run /opt/csw/bin/pkgutil -U
            DID_UPDATE='yes'
        fi
        run /opt/csw/bin/pkgutil -y -i py_pip
    fi
    if ! /opt/csw/bin/pkgutil --list | grep '^CSWpy-argparse$' >/dev/null; then
        echo "Installing argparse."
        if [ $DID_UPDATE = 'no' ]; then
            run /opt/csw/bin/pkgutil -U
            DID_UPDATE='yes'
        fi
        run /opt/csw/bin/pkgutil -y -i py_argparse
    fi
    if ! python -c 'import robot.api' >/dev/null 2>/dev/null; then
        echo "Installing robotframework."
        run pip -q install robotframework
    fi
}

solaris11_install_deps() {
    if pkg verify -q pkg://solaris/runtime/python-27 2>/dev/null; then
        :
    else
        echo "Installing python 2.7."
        run pkg install pkg://solaris/runtime/python-27
    fi
    if pkg verify -q pkg://solaris/library/python/pip 2>/dev/null; then
        :
    else
        echo "Installing pip."
        run pkg install pkg://solaris/library/python/pip
    fi
    # argparse is bundled in runtime/python-27
    if ! python -c 'import robot.api' >/dev/null 2>/dev/null; then
        echo "Installing robotframework."
        run pip -q install robotframework
    fi
}

# The nm changed in 11.3 which broke libtool.
# See http://lists.gnu.org/archive/html/bug-libtool/2016-01/msg00000.html
solaris113_patch_libtool() {
    if [ -f /usr/share/aclocal/libtool.m4.unpatched ]; then
        echo "Skipping libtool patch; already patched."
        return
    fi
    cp /usr/share/aclocal/libtool.m4 /usr/share/aclocal/libtool.m4.unpatched
    chmod +w /usr/share/aclocal/libtool.m4
    echo "Patching libtool"
    ( cd / ; cat <<_EOF_ | patch -p1 )
--- /usr/share/aclocal/libtool.m4.orig	Sun Aug 14 12:04:03 2016
+++ /usr/share/aclocal/libtool.m4	Sun Aug 14 12:05:55 2016
@@ -3651,7 +3651,7 @@
   symcode='[[BCDEGQRST]]'
   ;;
 solaris*)
-  symcode='[[BDRT]]'
+  symcode='[[BCDRT]]'
   ;;
 sco3.2v5*)
   symcode='[[DT]]'
_EOF_
}

install_deps() {
    echo "Checking dependencies."
    sysname=`detect_sysname`
    case "$sysname" in
    linux-debian*)
        debian_install_deps
        ;;
    linux-fedora*)
        fedora_install_deps
        ;;
    linux-centos*|linux-rhel*)
        rhel_install_deps
        ;;
    solaris-10*)
        solaris10_install_deps
        ;;
    solaris-11.[012])
        solaris11_install_deps
        ;;
    solaris-11.3)
        solaris11_install_deps
        solaris113_patch_libtool
        ;;
    *)
        echo "WARNING: Unable to install deps on unknown platform: $sysname" >&2
        ;;
    esac
}

make_output_dirs() {
    echo "Making output directories."
    run mkdir -p $DIR_LOG
    run mkdir -p $DIR_OUTPUT
}

make_doc() {
    echo "Generating documentation."
    # Generate the library documentation. Requires robotframework.
    pypath=libraries/OpenAFSLibrary/OpenAFSLibrary
    input="$pypath"
    output="$DIR_DOC/OpenAFSLibary.html"
    if [ "$OPT_VERBOSE" = "yes" ]; then
        echo "Writing file $output"
    fi
    run mkdir -p $DIR_DOC
    run python -m robot.libdoc --format HTML --pythonpath $pypath $input $DIR_DOC/OpenAFSLibary.html
}

install_package() {
    ( cd libraries/$1 && ./install.sh )
}

install_packages() {
    echo "Installing our packages."
    for package in $PACKAGES
    do
        echo "  Installing package ${package}."
        run install_package $package
    done
}

install_tests() {
    echo "Installing test suites."
    run mkdir -p $DIR_ROOT
    run cp -r tests/ $DIR_ROOT
    run cp -r resources/ $DIR_ROOT
}

SEEN=""
while :; do
    case "$1" in
    "")
        break
        ;;
    -h|--help)
        usage
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
    deps|docs|libs|tests)
        SEEN="$SEEN:$1:"
        shift
        ;;
    all)
        SEEN="$SEEN:deps:docs:libs:tests:"
        shift
        ;;
    *)
        usage
        exit 1
        ;;
    esac
done

# Avoid accidental local installs by requiring --user when not running as root.
if [ $UID -ne 0 -a "$OPT_ALLOW_USER" = "no" ]; then
    echo "Please run as root, or specify --user for a local installation."
    exit 1
fi
if [ $UID -eq 0 -a "$OPT_ALLOW_USER" = "yes" ]; then
    echo "Cannot do a local installation as root."
    exit 1
fi

# Install specified targets.
if [ -z $SEEN ]; then
    SEEN=":deps:docs:libs:tests:"  # Install all by default.
fi
for TARGET in "deps" "libs" "tests" "docs"
do
    if echo "$SEEN" | grep ":$TARGET:" >/dev/null; then
        case "$TARGET" in
        deps)    install_deps ;;
        libs)    install_packages ;;
        tests)   install_tests ;;
        docs)    make_doc ;;
        esac
    fi
done

# Post install steps.
if echo "$SEEN" | grep ":tests:" >/dev/null; then
    make_output_dirs
fi
if echo "$SEEN" | grep ":libs:" >/dev/null; then
    afsutil check
    if [ $? -ne 0 ]; then
        echo "Try: sudo afsutil check --fix-hosts"
    fi
fi
echo "Done."
