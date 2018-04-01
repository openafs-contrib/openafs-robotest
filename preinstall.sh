#!/bin/sh
#
# usage: sudo preinstall.sh
#

OSID=`preinstall/detect-os.sh`
preinstall/preinstall.${OSID}
