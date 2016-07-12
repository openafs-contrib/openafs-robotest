#!/bin/sh
#
# Install afs-robotest script and python packages.
# Run as a not-root user; invokes sudo as needed.
#

PROGNAME=`basename $0`
VERBOSITY="--quiet"      # Change to "--verbose" for chatty pip commands.
BINDIR="/usr/local/bin"  # Where to install scripts; customize as desired.
PACKAGES="afsutil OpenAFSLibrary"  # Our packages

# Our directories.
ROOT=`pwd`
ETC=$HOME/.afsrobotestrc # Put the rc under HOME, instead of ROOT.
TESTS=$ROOT/tests
LIBRARIES=$ROOT/libraries
RESOURCES=$ROOT/resources
HTML=$ROOT/html
DOC=$ROOT/html/doc
LOG=$ROOT/html/log
OUTPUT=$ROOT/html/output
DIST=$ROOT/html/dist

#
# Make our directories.
#
make_dirs() {
    mkdir -p $ETC
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
# Install the front-end script to a directory in the path.
#
install_script() {
    echo "Installing script to $BINDIR."
    sudo cp afs-robotest $BINDIR || exit 1
    if test ! -f afs-robotest.conf ; then
        echo "Creating default config file."
        afs-robotest config init || exit 1
    fi
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
    echo "$PROGNAME: [all|dirs|doc|packages|script|repo]"
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
    packages)
        make_sdists
        install_packages
        ;;
    script)
        install_script
        ;;
    ""|all)
        make_dirs
        make_doc
        make_sdists
        update_repo
        install_packages
        install_script
        ;;
    *)
        usage
        exit 1
        ;;
esac
exit 0
