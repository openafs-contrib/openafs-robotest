#!/bin/sh
#
# usage: ./uninstall.sh       # local uninstall
#        sudo ./uninstall.sh  # global uninstall
#

PACKAGE="afsrobot"

pip show --quiet $PACKAGE && pip uninstall -y $PACKAGE

