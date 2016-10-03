#!/bin/sh
#
# Install our python packages and scripts.
# Run as a not-root user; invokes sudo as needed.
#

PROGNAME=`basename $0`
VERBOSITY="--quiet"      # Change to "--verbose" for chatty pip commands.
PACKAGES="afsutil afsrobot OpenAFSLibrary"  # Our packages

# Our directories.
ROOT=`pwd`
TESTS=$ROOT/tests
LIBRARIES=$ROOT/libraries
RESOURCES=$ROOT/resources
HTML=$ROOT/html
DOC=$ROOT/html/doc
LOG=$ROOT/html/log
OUTPUT=$ROOT/html/output
DIST=$ROOT/html/dist

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

#
# Install dependencies on Debian.
#
_debian_install_deps() {
    echo "Installing python."
    sudo -n apt-get install -q -y python || exit 1
    echo "Installing pip."
    sudo -n apt-get install -q -y python-pip || exit 1
    echo "Installing argparse."
    sudo -n apt-get install -q -y python-argparse || exit 1
    echo "Installing robotframework."
    sudo -n pip -q install robotframework || exit 1
}

#
# Install dependencies on RHEL/CentOS.
#
_rhel_install_deps() {
    echo "Installing epel."
    sudo -n yum install -q -y epel-release
    echo "Installing python."
    sudo -n yum install -q -y python || exit 1
    echo "Installing pip."
    sudo -n yum install -q -y python-pip || exit 1
    echo "Installing argparse."
    sudo -n yum install -q -y python-argparse || exit 1
    echo "Installing robotframework."
    sudo -n pip -q install robotframework || exit 1
}

#
# Install dependencies on Solaris.
#
_solaris_install_deps() {
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
        sudo -n pkgadd -a .pkgadd -d http://get.opencsw.org/now CSWpkgutil || exit 1
        rm .pkgadd
    fi
    sudo -n /opt/csw/bin/pkgutil -U || exit 1
    echo "Installing python 2.7."
    sudo -n /opt/csw/bin/pkgutil -y -i python27 || exit 1
    echo "Installing pip."
    sudo -n /opt/csw/bin/pkgutil -y -i py_pip || exit 1
    echo "Installing argparse."
    sudo -n /opt/csw/bin/pkgutil -y -i py_argparse || exit 1
    echo "Installing robotframework."
    sudo -n pip -q install robotframework || exit 1
}

#
# Install dependencies.
#
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

#
# Create/upgrade the configuration file.
#
config_init() {
    echo "Creating/updating afs-robotest config file."
    afs-robotest config init || exit 1
}

#
# Make our directories.
#
make_dirs() {
    mkdir -p $HTML
    mkdir -p $DOC
    mkdir -p $LOG
    mkdir -p $OUTPUT
    mkdir -p $DIST
}

#
# Generate the library documentation. Requires robotframework.
#
make_doc() {
    echo "Generating documentation."
    pypath=$LIBRARIES/OpenAFSLibrary/OpenAFSLibrary
    input=$pypath
    output=$DOC/OpenAFSLibary.html
    mkdir -p $DOC
    python -m robot.libdoc --format HTML --pythonpath $pypath $input $output || exit 1
}

#
# Create a source dist archive of our package.
#
make_sdist() {
    package=$1

    echo "Creating source distribution for package '$package'."
    rm -f $LIBRARIES/$package/dist/* # Remove any old versions.
    ( cd $LIBRARIES/$package && python setup.py $VERBOSITY sdist --formats gztar ) || exit 1
    sdist=`ls $LIBRARIES/$package/dist/*.tar.gz` || exit 1
}

#
# Update the package archive repo.
#
copy_sdist() {
    package=$1

    mkdir -p $DIST/$package
    for archive in $LIBRARIES/$package/dist/*.tar.gz
    do
        echo "Copying package archive '`basename $archive`'."
        cp $archive $DIST/$package || exit 1
    done
}

#
# Install the the package. (Global install with sudo.)
#
install_package() {
    package=$1

    echo "Installing python package '$package'."
    sdist=`ls $LIBRARIES/$package/dist/*.tar.gz` || exit 1
    sudo pip $VERBOSITY install --upgrade $sdist || exit 1
}

#
# Make source dist archives for each package.
#
make_sdists() {
    for package in $PACKAGES
    do
        make_sdist $package
    done
}

#
# Update our package archive repo.
#
update_repo() {
    for package in $PACKAGES
    do
        copy_sdist $package
    done
}

#
# Install our python packages.
#
install_packages() {
    for package in $PACKAGES
    do
        install_package $package
    done
}

#
# Print usage.
#
usage() {
    echo "usage: $PROGNAME <target>"
    echo "where <target> is one of:"
    echo "  all  - full install (default)"
    echo "  deps - external dependencies"
    echo "  dirs - make directories"
    echo "  doc  - generate docs"
    echo "  pkg  - our python packages"
}

#
# Main
#
if [ "`id -u`" = "0" ]; then
    echo "$PROGNAME: Please run as a regular user." >&2
    exit 1
fi
case "$1" in
    -h|--help|help)
        usage
        ;;
    deps)
        install_deps
        ;;
    dirs)
        make_dirs
        ;;
    doc)
        make_doc
        ;;
    repo)
        make_sdists
        update_repo
        ;;
    pkg)
        make_sdists
        install_packages
        ;;
    ""|all)
        install_deps
        make_dirs
        make_doc
        make_sdists
        update_repo
        install_packages
        config_init
        ;;
    *)
        usage
        exit 1
        ;;
esac
exit 0
