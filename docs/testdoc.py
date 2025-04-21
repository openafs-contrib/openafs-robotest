#
# Generate sphinx rst file from robot files.
#
# Walk the test directory to find robot files and extract documentation and
# test names to generate the rst doc file.  This script uses the robot 4.0
# parsing api to parse the robot files.
#

import os
import sys
import ast
import robot.api.parsing

def parse(filename):
    doc = ''
    settings = []
    tests = []
    model = robot.api.parsing.get_model(filename)
    for node in ast.walk(model):
        if isinstance(node, robot.parsing.model.blocks.SettingSection):
            settings.append(node)
        if isinstance(node, robot.parsing.model.statements.TestCaseName):
            tests.append(node.name)
    for s in settings:
        for node in ast.walk(s):
            if isinstance(node, robot.parsing.model.statements.Documentation):
                doc = doc + ' ' + node.value
    info = {
        'name': os.path.basename(filename).replace('.robot', '').capitalize(),
        'doc': doc.strip(),
        'tests': sorted(tests),
    }
    return info

def walk(topdir):
    sections = []
    topdir = os.path.abspath(topdir)
    if not topdir.endswith('/'):
        topdir += '/'
    for root, dirs, files in os.walk(topdir):
        dirs.sort()
        files.sort()
        suites = []
        for file_ in files:
            if file_ == '__init__.robot':
                continue
            if not file_.endswith('.robot'):
                continue
            filename = os.path.join(root, file_)
            suites.append(parse(filename))
        tail = root.replace(topdir, '')
        section = '.'.join([i.capitalize() for i in tail.split('/')])
        sections.append({'name': section, 'suites': suites})
    return sections

def print_heading(fp, name, level=1):
    underline = {1: '=', 2: '-', 3: '~'}
    fp.write('%s\n' % name)
    fp.write('%s\n' % (underline[level] * len(name)))
    fp.write('\n')

def render(fp, sections):
    print_heading(fp, 'Tests', 1)
    for section in sections:
        print_heading(fp, section['name'], 2)
        for suite in section['suites']:
            print_heading(fp, suite['name'], 3)
            if suite['doc']:
                fp.write('%s\n' % suite['doc'])
                fp.write('\n')
            for test in suite['tests']:
                fp.write('* %s\n' % test)
            fp.write('\n')

def main():
    output = sys.argv[1]
    with open(output, 'w') as fp:
        render(fp, walk('../tests'))

if __name__ == '__main__':
    main()
