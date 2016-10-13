#!/bin/sh

DIR_PREFIX="/usr/local"
DIR_ROOT="$DIR_PREFIX/afsrobotest"
DIR_HTML="$DIR_ROOT/html"

PACKAGES="afsutil afsrobot OpenAFSLibrary"
VERBOSE="no"

for package in $PACKAGES
do
    if pip show --quiet $package; then
        libraries/$package/uninstall.sh || exit 1
    fi
done

rm -r -f $DIR_HTML/doc || exit 1
rm -r -f $DIR_HTML/log || exit 1
rm -r -f $DIR_HTML/output || exit 1
rm -r -f $DIR_ROOT/html || exit 1

rm -r -f $DIR_ROOT/tests || exit 1
rm -r -f $DIR_ROOT/resources || exit 1

if [ -d $DIR_PREFIX/afsrobotest ]; then
    rmdir $DIR_PREFIX/afsrobotest && echo "Removed $DIR_PREFIX/afsrobotest" || exit 1
fi

