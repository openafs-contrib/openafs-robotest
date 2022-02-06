#!/usr/bin/python3
#
# robotab - tabulate robot framework test cases
#
# Warning: This script does an in-place conversion, and makes no attempt to
# backup the original file! Make sure your files are backed up/checked in
# before running this.
#
# This is a hack to convert the robot files to pipe separated format with nicer
# column alignment, which is currently unsupported by robotidy.  Hopefully,
# future versions of robotidy will make this script obsolete.
#
# The robot files must be converted to tab separated tables the first time
# this is run.
#
#    $ robotidy --separator tab tests/
#    $ tools/robotab.py tests/
#
# After the initial conversion, it can be run again to fix column alignments in
# specific files, or all files in a directory tree.
#
#    $ tools/robotab.py tests/path/to/example.robot  # one file
#    $ tools/robotab.py tests/                       # all .robot files
#

import os
import sys

def usage():
    """
    Print usage.
    """
    print('robotab PATH [PATH ..]')
    print('')
    print('where:')
    print('   PATH is a .robot filename or directory containing .robot files')


def tabulate(table):
    """
    Add spaces to table elements to align columns.
    """
    cw = {}   # column widths

    # Trim leading and trailing whitespace from each element.
    for i, row in enumerate(table):
        for j, element in enumerate(row):
            table[i][j] = element.strip()

    # Find the max element width for each column.
    for row in table:
        for j, element in enumerate(row):
            cw[j] = max(cw.get(j, 0), len(element))

    # Reformat elements to align columns.
    for i, row in enumerate(table):
        for j, element in enumerate(row):
            table[i][j] = ' ' + element.ljust(cw[j]) + ' '


def append_table(lines, table):
    """
    Append table to output lines as column aligned pipe separated
    format.

    Note an extra sep is added at the beginning of the line to indicate
    this is pipe separated format.
    """
    tabulate(table)
    for row in table:
        lines.append('|' + '|'.join(row).rstrip() + '\n')


def reformat(filename):
    """
    Reformat a robot file.

    Note that pipe separated format requires the lines to start with a
    pipe char, so that extra char is removed before spliting the line.
    """
    print('Reformatting', filename)
    table = None            # Current table
    out_lines = []          # Output lines

    with open(filename) as f:
        in_lines = f.readlines()

    for line in in_lines:
        if table is None:
            if line.startswith('|'):
                table = [line.replace('|', '', 1).split('|')]
            elif line.startswith('\t'):
                table = [line.split('\t')]
            else:
                out_lines.append(line)
        else:
            if line.startswith('|'):
                table.append(line.replace('|', '', 1).split('|'))
            elif line.startswith('\t'):
                table.append(line.split('\t'))
            else:
                append_table(out_lines, table)
                table = None
                out_lines.append(line)
    if table is not None:
        append_table(out_lines, table)

    with open(filename, 'w') as f:
        f.writelines(out_lines)


def recurse(path):
    """
    Find and reformat all the robot files in directory tree.
    """
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith('.robot'):
                filepath = os.path.join(dirpath, filename)
                reformat(filepath)


def main():
    if len(sys.argv) < 2:
        usage()
        return 1
    for path in sys.argv[1:]:
        if os.path.isfile(path):
            reformat(path)
        elif os.path.isdir(path):
            recurse(path)


if __name__ == '__main__':
    main()
