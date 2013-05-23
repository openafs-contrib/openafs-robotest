#!/usr/bin/python
#
# tidy-rst.py - convert RF test cases to reStructuredText format
#
# This tool can be used to convert Robot Framework (RF) testdocs to
# reStructuredText format. The resulting files can be included in ReST
# documents and can be used to generate HTML test plan documentation.
#
# The current RF tidy tool (as of 2.7.7) does not support ReST as an
# output format. This tool was written instead of patching RF modules.
#

import os
import sys
from robot.errors import DataError
from robot.parsing import ResourceFile, TestDataDirectory, TestCaseFile, disable_curdir_processing
from robot.writer.dataextractor import DataExtractor

MIN_COL_WIDTH = 3

# stolen from robot/tidy.py
def _is_init_file(path):
    return os.path.splitext(os.path.basename(path))[0].lower() == '__init__'

# stolen from robot/tidy.py
@disable_curdir_processing
def _parse_data(path):
    if os.path.isdir(path):
        return TestDataDirectory(source=path).populate()
    if _is_init_file(path):
        path = os.path.dirname(path)
        return TestDataDirectory(source=path).populate(recurse=False)
    try:
        return TestCaseFile(source=path).populate()
    except DataError:
        try:
            return ResourceFile(source=path).populate()
        except DataError:
            raise DataError("Invalid data source '%s'." % path)

def column_widths(table):
    ''' Determine the column widths for this table. '''
    rows = DataExtractor().rows_from_table(table)
    widths = [len(table.header[0])]
    for row in rows:
        for i, col in enumerate(row):
            width = max(len(col), MIN_COL_WIDTH)
            if i >= len(widths):
                widths.append(width)
            elif width > widths[i]:
                widths[i] = width
    return widths

def make_ruler(widths):
    return ' '.join([''.ljust(w+1, '=') for w in widths])

def print_header(table, widths):
    second = {
       'setting': 'Value',
       'variable': 'Value',
       'test case': 'Step',
       'keyword': 'Step',
    }
    header = []
    for i, w in enumerate(widths):
        if i == 0:
            header.append(table.header[0])
        elif i == 1:
            header.append(second[table.type])
        else:
            header.append("Arg")
    print_row(widths, header)

def print_rows(table, widths):
    rows = DataExtractor().rows_from_table(table)
    for row in rows:
        print_row(widths, row)

def print_row(widths, row):
    if len(row) == 0:
        row = ['']
    for i, col in enumerate(row):
	if i == 0 and len(col) == 0:
            col = ".."
        sys.stdout.write(col.ljust(widths[i]+2))
    sys.stdout.write("\n");

def print_table(table):
    widths = column_widths(table)
    ruler = make_ruler(widths)
    print ruler
    print_header(table, widths)
    print ruler
    print_rows(table, widths)
    print ruler
    sys.stdout.write("\n");

def main(args):
    if len(args) < 2:
        sys.stderr.write("usage: %s <testdoc> [<testdoc> ...]\n" % (os.path.basename(args[0])))
        return 255
    for file in args[1:]:
        for table in _parse_data(file):
            if table:
                print_table(table)

if __name__ == "__main__":
    main(sys.argv)
