# Copyright (c) 2017 Sine Nomine Associates
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""Create command line subcommands with argparse

This module provides a thin wrapper over the standard argparse package to
declaratively create command line subcommands. A decorator turns regular
functions into cli subcommands. The argument function defines command line
options.

Example:

    @subcommand(
        argument("host", metavar="<host>", help="example positional option"),
        argument("--filename", "-f", help="example optional flag"),
        argument("--output", default="example", help="example option"),
        )
    def example(**args):
        'example subcommand'
        print("args:", args['host'], args['filename'], args['output'])
        return 0

    dispatch()
    # usage: cli example [options]

"""


from __future__ import print_function
import argparse, logging, os, sys
from afsutil.system import CommandFailed
try:
    from configparser import ConfigParser # python3
except ImportError:
    from ConfigParser import ConfigParser # python2

progname = 'afsutil'
root = argparse.ArgumentParser()
parent = root.add_subparsers(dest='subcommand')
config = ConfigParser()
config.read([
    '/etc/{0}.ini'.format(progname),
    os.path.expanduser('~/.{0}.ini'.format(progname)),
])

def _get_config(section, option, default):
    """Get the config option"""
    value = default
    if isinstance(value, list) or isinstance(value, tuple):
        subsection = "{0}.{1}".format(section, option)
        if config.has_section(subsection):
            value = []
            for k,v in config.items(subsection):
                value.append("{0}={1}".format(k,v))
        elif config.has_option(section, option):
            value = config.get(section, option).split()
    else:
        if config.has_option(section, option):
            value = config.get(section, option)
    return value

def _long_flag(name_or_flags):
    """Find the long flag name, if one."""
    for opt in name_or_flags:
        if opt.startswith('--'):
            return opt.lstrip('--')
    return None

def argument(*name_or_flags, **options):
    """Helper to declare subcommand arguments."""
    return (name_or_flags, options)

def subcommand(*arguments, **kwargs):
    """Decorator to declare command line subcommands."""
    def decorator(function):
        name = function.__name__.strip('_')
        desc = function.__doc__
        parser = parent.add_parser(name, description=desc)
        args = list(arguments) # Local var to add common args.
        if name not in ('help', 'version'):
            args.insert(0, argument('-q', '--quiet', help='print less messages', action='store_true'))
            args.insert(1, argument('-v', '--verbose', help='print more messages', action='store_true'))
            args.insert(2, argument('-l', '--log', help='log file location'))
        for arg in args:
            name_or_flags,options = arg
            default = options.get('default') # may be a list
            flag = _long_flag(name_or_flags)
            if flag:
                default = _get_config(name, flag, default)
                options['default'] = default
            if default and 'help' in options:
                if isinstance(default, list):
                    default = " ".join(default)
                options['help'] += " (default: {0})".format(default)
            parser.add_argument(*name_or_flags, **options)
        parser.set_defaults(function=function, **kwargs)
        return function
    return decorator

def usage():
    """Print a summary of the subcommands."""
    print("usage: {0} <command> [options]".format(progname))
    print("")
    print("commands:")
    for name,parser in parent.choices.items():
        print("  {name:12} {desc}".format(name=name, desc=parser.description))
    return 0

def _setup_logging(verbose=False, quiet=False, log=None, **kwargs):
    options = {
        'level':logging.INFO,
        'format':'%(message)s',
    }
    if quiet:
        options['level'] = logging.ERROR
    if verbose:
        options['level'] = logging.DEBUG
    if log:
        options['filename'] = log
        options['format'] = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(**options)
    return logging.getLogger('afsutil')

def dispatch():
    """Parse arguments and dispatch the subcommand."""
    args = vars(root.parse_args())
    requires_root = args.pop('requires_root', False)
    function = args.pop('function')
    if requires_root and os.geteuid() != 0:
        sys.stderr.write("afsutil: Must run as root!\n")
        sys.exit(1)
    log = _setup_logging(**args)
    cwd = None
    chdir = args.get('chdir')
    if chdir:
        log.info("Changing to directory %s", chdir)
        cwd = os.getcwd()
        os.chdir(chdir)
    try:
        code = function(**args)
    except CommandFailed as e:
        if args.get('log') or args.get('verbose'):
            log.exception(e)
        sys.stderr.write("Command failed: %s, code %d\n" % (e.cmd, e.code))
        sys.stderr.write("output:\n")
        sys.stderr.write("%s\n" % (e.out))
        code = 1
    finally:
        if cwd:
            os.chdir(cwd)
    return code
