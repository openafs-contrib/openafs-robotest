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

PATH=/opt/csw/bin:$PATH
RT_PACKAGE="afsutil"
RT_USAGE="usage: sudo ./install [--user] [--verbose]"
RT_PIPOPTS="--upgrade"
RT_UID=`python -c 'import os; print os.getuid()'` # for portability

while [ "x$1" != "x" ]; do
    case "$1" in
    -h|--help)
        echo "$RT_USAGE"
        exit 0
        ;;
    -u|--user)
        RT_PIPOPTS="$RT_PIPOPTS --user"
        shift
        ;;
    -v|--verbose)
        RT_PIPOPTS="$RT_PIPOPTS --verbose"
        shift
        ;;
    *)
        echo "$RT_USAGE" >&2
        exit 1
        ;;
    esac
done

git clean -f -d -x dist/ ${RT_PACKAGE}.egg-info/ || exit 1
if [ $RT_UID -eq 0 ]; then
    RT_OWNER=`python -c 'import os; import pwd; print pwd.getpwuid(os.stat(".").st_uid).pw_name'`
    echo "Building source distribution as ${RT_OWNER}."
    su $RT_OWNER -c "python setup.py sdist --formats gztar --verbose" || exit 1
else
    python setup.py sdist --formats gztar --verbose || exit 1
fi

pip install $RT_PIPOPTS dist/${RT_PACKAGE}*.tar.gz || exit 1

