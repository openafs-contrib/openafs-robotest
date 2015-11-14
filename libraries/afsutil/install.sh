#!/bin/sh
#
# Run bdist as the regular user first to avoid polluting this working directory
# with files owned by root.
python setup.py bdist && sudo python setup.py install
