#
# Generate a rst file with robot.libdoc for the sphinx doc tree.
#
# Robotframework 4.0 or better is required for the libdoc json support.
#

import json
import robot.libdoc


def write_arguments(f, args):
    """
    Write the argument table for a keyword.
    """
    f.write('**Arguments**\n\n')
    f.write('.. list-table::\n')
    f.write('   :header-rows: 1\n')
    f.write('\n')
    f.write('   * - Name\n')
    f.write('     - Default value\n')
    f.write('     - Notes\n')
    for a in args:
        rq = 'required' if a['required'] else ''
        dv = a['defaultValue'] if a['defaultValue'] else ''
        f.write('   * - %s\n' % a['name'])
        f.write('     - %s\n' % dv)
        f.write('     - %s\n' % rq)
    f.write('\n')


def write_keyword(f, keyword):
    """
    Write the keyword documentation.
    """
    if not keyword['doc']:
        raise AssertionError(
            'Missing doc for keyword "%s" in file "%s".' %
            (keyword['name'], keyword['source']))
    f.write('%s\n%s\n\n' % (keyword['name'], '-' * len(keyword['name'])))
    if keyword['args']:
        write_arguments(f, keyword['args'])
    f.write('**Documentation**\n\n')
    f.write('%s\n\n' % keyword['doc'])


def main():
    """
    Generate the keyword.rst file with libdoc.
    """
    # First, generate an intermediate machine readable file.
    robot.libdoc.LibDoc().execute(
        '../OpenAFSLibrary/',
        'build/libdoc.json',
        format='json',
        docformat='html',
        quiet=True)

    # Load our intermediate json file.
    with open('build/libdoc.json') as f:
        libspec = json.load(f)

    # Write the rst output.
    with open('source/keywords.rst', 'w') as f:
        f.write('Keywords\n')
        f.write('========\n\n')
        f.write('Version: %s\n\n' % (libspec['version']))
        for keyword in libspec['keywords']:
            write_keyword(f, keyword)


if __name__ == '__main__':
    main()
