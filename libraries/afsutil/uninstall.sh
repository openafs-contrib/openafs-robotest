#!/bin/sh
#
# usage: ./uninstall.sh       # local uninstall
#        sudo ./uninstall.sh  # global uninstall
#

PATH=/opt/csw/bin:$PATH
RT_PACKAGE="afsutil"
RT_UID=`python -c 'import os; print os.getuid()'` # for portability

pip show --quiet $RT_PACKAGE && pip uninstall -y $RT_PACKAGE

if [ $RT_UID -eq 0 ]; then
    rm -f /usr/bin/${RT_PACKAGE}
fi

