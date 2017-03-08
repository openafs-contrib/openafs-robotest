#!/bin/sh
#
# usage: ./uninstall.sh       # local uninstall
#        sudo ./uninstall.sh  # global uninstall
#

PATH=/opt/csw/bin:$PATH
RT_PACKAGE="OpenAFSLibrary"
PIP_DISABLE_PIP_VERSION_CHECK=1

pip show --quiet $RT_PACKAGE && pip uninstall -y $RT_PACKAGE

