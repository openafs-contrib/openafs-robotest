#!/bin/sh
#
# usage: ./uninstall.sh       # local uninstall
#        sudo ./uninstall.sh  # global uninstall
#

PATH=/opt/csw/bin:$PATH
RT_PACKAGE="OpenAFSLibrary"

pip show --quiet $RT_PACKAGE && pip uninstall -y $RT_PACKAGE

