#!/bin/sh
#
# Run the test and publish the html test plan and results.
#

RST2HTML_OPTS="--strict --stylesheet-path=css/robotest.css --no-toc-backlinks"

[ -d html ] || mkdir html || exit 255
[ -d results ] || mkdir results || exit 255

rst2html ${RST2HTML_OPTS} tests/example.rst html/example.html || exit 255
pybot --outputdir results html/example.html

echo "see file://`pwd`/results/report.html"
