#!/bin/sh

# remove old versions
sudo pip uninstall -y afsutil
git clean -f -d -x dist afsutil.egg-info

python setup.py sdist --formats gztar --verbose || exit 1
sdist=`ls dist/afsutil*.tar.gz` || exit 1
sudo pip install "$sdist"
