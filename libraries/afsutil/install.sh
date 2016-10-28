#!/bin/sh
#
# Build the source distribution and then install it.
#
# To install system-wide:
#
#    sudo ./install.sh [--verbose]
#
# To install to the user's home directory, e.g., ~/.local:
#
#    ./install.sh --user [--verbose]
#

PACKAGE="afsutil"
USAGE="usage: sudo ./install [--user] [--verbose]"
PIP_OPTS="--upgrade"
UID=`python -c 'import os; print os.getuid()'` # for portability

while [ "x$1" != "x" ]; do
    case "$1" in
    -h|--help)
        echo "$USAGE"
        exit 0
        ;;
    -u|--user)
        PIP_OPTS="$PIP_OPTS --user"
        shift
        ;;
    -v|--verbose)
        PIP_OPTS="$PIP_OPTS --verbose"
        shift
        ;;
    *)
        echo "$USAGE" >&2
        exit 1
        ;;
    esac
done

git clean -f -d -x dist/ ${PACKAGE}.egg-info/ || exit 1
if [ $UID -eq 0 ]; then
    owner=`python -c 'import os; import pwd; print pwd.getpwuid(os.stat(".").st_uid).pw_name'`
    echo "Building source distribution as ${owner}."
    su $owner -c "python setup.py sdist --formats gztar --verbose" || exit 1
else
    python setup.py sdist --formats gztar --verbose || exit 1
fi

pip install $PIP_OPTS dist/${PACKAGE}*.tar.gz || exit 1

