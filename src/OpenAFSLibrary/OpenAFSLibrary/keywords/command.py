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

from robot.api import logger
from OpenAFSLibrary.command import run_program

class _CommandKeywords(object):
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

