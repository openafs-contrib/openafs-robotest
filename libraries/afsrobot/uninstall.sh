#!/bin/sh
#
# usage: ./uninstall.sh       # local uninstall
#        sudo ./uninstall.sh  # global uninstall
#

RT_PACKAGE="afsrobot"
pip show --quiet $RT_PACKAGE && pip uninstall -y $RT_PACKAGE