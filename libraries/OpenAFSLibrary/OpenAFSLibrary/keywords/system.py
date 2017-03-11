# Copyright (c) 2014-2015, Sine Nomine Associates
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
#

import socket
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn
from OpenAFSLibrary.variable import get_var
from OpenAFSLibrary.command import run_program

def set_global_variables():
    # Save this hostname as a global variable.
    try:
        hostname = socket.gethostname()
        BuiltIn().set_global_variable("${HOSTNAME}", hostname)
    except AttributeError:
        pass # allow to load outside of RF

def get_crash_count():
    count = 0
    last = ""
    filename = "%s/BosLog" % get_var('AFS_LOGS_DIR')
    log = open(filename, "r")
    for line in log.readlines():
        if 'core dumped' in line:
            last = line
            count += 1
    log.close()
    return (count, last)

class _SystemKeywords(object):
    def command_should_succeed(self, cmd, msg=None):
        """Fails if command does not exit with a zero status code."""
        rc,out,err = run_program(cmd)
        logger.info("Output: " + out)
        logger.info("Error: " + err)
        if rc != 0:
            if not msg:
                msg = "Command Failed! %s" % cmd
            raise AssertionError(msg)

    def command_should_fail(self, cmd):
        """Fails if command exits with a zero status code."""
        rc,out,err = run_program(cmd)
        logger.info("Output: " + out)
        logger.info("Error: " + err)
        logger.info("Code: %d" % rc)
        if rc == 0:
            raise AssertionError("Command should have failed: %s" % cmd)

    def init_crash_check(self):
        """Initialize the crash check counter."""
        (count, last) = get_crash_count()
        BuiltIn().set_suite_variable('${CRASH_COUNT}', count)
        BuiltIn().set_suite_variable('${CRASH_LAST}', last)

    def crash_check(self):
        """Fails if a server process crash was detected."""
        before = get_var('CRASH_COUNT')
        (after, last) = get_crash_count()
        if after != before:
            raise AssertionError("Server crash detected! %s" % last)

set_global_variables()

