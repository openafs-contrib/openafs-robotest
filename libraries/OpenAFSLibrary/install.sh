#!/bin/sh

python setup.py sdist --formats gztar --verbose || exit 1
sdist=`ls dist/OpenAFSLibrary*.tar.gz` || exit 1
sudo pip install "$sdist"

