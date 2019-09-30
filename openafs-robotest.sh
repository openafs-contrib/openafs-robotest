#!/bin/bash
set -e

ROBOTRC=~/.openafs-robotest/robotrc

if [ $# -eq 0 ]; then
    echo "usage: ./openafs-robotest.sh [options] <tests> [<tests>..]"
    echo ""
    echo "Run the robot framework tests for OpenAFS."
    echo ""
    echo "examples:"
    echo "   ./openafs-robotest.sh tests                       -- run all of the tests"
    echo "   ./openafs-robotest.sh tests/workload/basic.robot  -- run tests in basic.robot"
    echo ""
    echo "See '${ROBOTRC}' for current options."
    echo "See 'robot --help' for available options."
    exit 1
fi

robot --argumentfile "${ROBOTRC}" "$@"
