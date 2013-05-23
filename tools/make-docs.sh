#!/bin/sh

if [ -f ./settings ]; then
    . ./settings
fi

RST2HTML_OPTS="--strict --stylesheet-path=css/robotest.css --no-toc-backlinks"
HTML=${RUN_HTML_DIR:-output}/doc
TMPDIR=/tmp/robotest-doc-$$

test -d $HTML || mkdir -p $HTML
test -d $TMPDIR || mkdir -p $TMPDIR

for t in `find tests -type f -name '*.robot' | sort`
do
    dir=`dirname $t`
    base=`basename $t ".robot"`

    mkdir -p $TMPDIR/$dir
    python tools/tidy-rst.py $t > "$TMPDIR/$dir/$base.rst"

    perl -n -e 'print if $.==1 .. /^\*\*\*/ and !/^\*\*\*/' $t >>"$TMPDIR/test_suites.rst"
    echo ".. include:: $TMPDIR/$dir/$base.rst" >> "$TMPDIR/test_suites.rst"
    echo "" >> "$TMPDIR/test_suites.rst"
done

cp doc/*.rst $TMPDIR
rst2html ${RST2HTML_OPTS} $TMPDIR/testplan.rst $HTML/testplan.html || exit 1
rm -rf $TMPDIR
