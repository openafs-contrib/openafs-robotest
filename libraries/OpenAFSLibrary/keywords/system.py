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

import sys
import os
import re
import math
import socket
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn
from OpenAFSLibrary.util import _get_var,_run_program

class System:
    @staticmethod
    def current():
        uname = os.uname()[0]
        if uname == "Linux":
            return Linux()
        elif uname == "SunOS":
            return Solaris()
        else:
            raise AssertionError("Unsupported operating system: %s" % (uname))

    def sudo(self, cmd, *args):
        cmd = "sudo -n /usr/sbin/afs-robotest-sudo %s %s" % (cmd, " ".join(args))
        logger.info("running: %s" % cmd)
        pipe = os.popen("%s 2>&1" % (cmd))
        for line in pipe.readlines():
            logger.info("output: %s" % line.rstrip())
        rc = pipe.close()
        if rc:
            code = (rc & 0xff00) >> 8  # process exit code is in the 16 high bits
            if code == os.EX_NOPERM:
                raise AssertionError("Command not permitted: %s\n" % (cmd));
            else:
                raise AssertionError("Command failed: %s: exit code %d" % (cmd, code))

class Linux(System):
    def get_modules(self):
        """Return loaded kernel module names."""
        modules = []
        f = open("/proc/modules", "r")
        for line in f.readlines():
            module = line.split()[0]
            modules.append(module)
        f.close()
        return modules

    def unload_module(self, name):
        """Unload the kernel module."""
        self.sudo("rmmod", name)

    def get_interfaces(self):
        # Getting information about the network interfaces in a portable way
        # requires some non-core modules; so instead just run the native
        # command line program.
        addrs = []
        cmd = "ip -oneline -family inet addr show"
        # Example output:
        # 1: lo    inet 127.0.0.1/8 scope host lo
        # 2: eth0    inet 172.16.50.143/24 brd 172.16.50.255 scope global eth0
        pipe = os.popen(cmd)
        for line in pipe.readlines():
            s = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
            if s:
                addr = s.group(1)
                if not addr.startswith("127."):
                    addrs.append(addr)
        pipe.close
        return addrs


class Solaris(System):
    def _get_kernel_modules(self):
        """Return loaded kernel module names and ids."""
        modules = {}
        pipe = os.popen("/usr/sbin/modinfo -w")
        for line in pipe.readlines():
            if line.lstrip().startswith("Id"):
                continue # skip header line
            # Fields are: Id Loadaddr Size Info Rev Module Name (Desc)
            m = re.match(r'\s*(\d+)\s+\S+\s+\S+\s+\S+\s+\d+\s+(\S+)', line)
            if m:
                id = m.group(1)
                name = m.group(2)
                modules[name] = id  # remove duplicate entries
            else:
                raise AssertionError("Unexpected modinfo output: %s" % (line))
        pipe.close()
        return modules

    def get_modules(self):
        """Return loaded kernel module names."""
        return self._get_kernel_modules().keys()

    def unload_module(self, name):
        """Unload the kernel module."""
        modules = self._get_kernel_modules()
        if name in modules:
            self.sudo("modunload", "-i", modules[name])

    def get_interfaces(self):
        # Getting information about the network interfaces in a portable way
        # requires some non-core modules; so instead just run the native
        # command line program.
        addrs = []
        cmd = "ipadm show-addr -p -o STATE,ADDR"
        # Example output:
        # ok:127.0.0.1/8
        # ok:172.16.50.146/24
        # ok:\:\:1/128
        # ok:fe80\:\:20c\:29ff\:fe3d\:f60c/10
        pipe = os.popen(cmd)
        for line in pipe.readlines():
            m = re.match(r'ok:(\d+\.\d+\.\d+\.\d+)', line)
            if m:
                addr = m.group(1)
                if not addr.startswith("127."):
                    addrs.append(addr)
        pipe.close
        return addrs



class _SystemKeywords(object):

    def __init__(self):
        self.system = System.current()

    def run_program(self, cmd_line):
        rc,out,err = _run_program(cmd_line)
        if rc:
            raise AssertionError("Program failed: '%s', exit code='%d'" % (cmd_line, rc))

    def sudo(self, cmd, *args):
        # Run a command as root.
        self.system.sudo(cmd, *args)

    def get_host_by_name(self, hostname):
        """Return the ipv4 address of the hostname."""
        return socket.gethostbyname(hostname)

    def get_device(self, path):
        """Return the device id of the given path as '(major,minor)'."""
        device = os.stat(path).st_dev
        return "(%d,%d)" % (os.major(device), os.minor(device))

    def program_should_be_running(self, program):
        if program not in self._get_running_programs():
            raise AssertionError("Program '%s' is not running!" % (program))

    def program_should_not_be_running(self, program):
        if program in self._get_running_programs():
            raise AssertionError("Program '%s' is running!" % (program))

    def _get_running_programs(self):
        rc,out,err = _run_program("ps ax")
        if rc != 0:
            raise AssertionError("Failed to run 'ps', exit code='%d'" % (rc))
        programs = set()
        lines = out.splitlines()
        # The first line of the ps output is a header line which shows
        # the columns for the fields.
        column = lines[0].index('COMMAND')
        for line in lines[1:]:
            cmd_line = line[column:]
            if cmd_line[0] == '[':  # skip linux threads
                continue
            command = cmd_line.split()[0]
            programs.add(os.path.basename(command))
        return list(programs)

    def get_modules(self):
        """Return a list of loaded kernel module names."""
        return self.system.get_modules()

    def unload_module(self, name):
        """Unload the kernel module."""
        return self.system.unload_module(name)

    def get_interfaces(self):
        """Find the non-loopback IPv4 addresses of the network interfaces."""
        return self.system.get_interfaces()

    def _get_crash_count(self):
        count = 0
        last = ""
        filename = "%s/BosLog" % _get_var('AFS_LOGS_DIR')
        log = open(filename, "r")
        for line in log.readlines():
            if 'core dumped' in line:
                last = line
                count += 1
        log.close()
        return (count, last)

    def init_crash_check(self):
        (count, last) = self._get_crash_count()
        BuiltIn().set_suite_variable('${CRASH_COUNT}', count)
        BuiltIn().set_suite_variable('${CRASH_LAST}', last)

    def crash_check(self):
        before = _get_var('CRASH_COUNT')
        (after, last) = self._get_crash_count()
        if after != before:
            raise AssertionError("Server crash detected! %s" % last)

    def directory_entry_should_exist(self, path):
        """Fails if directory entry does not exist in the given path."""
        base = os.path.basename(path)
        dir = os.path.dirname(path)
        if not base in os.listdir(dir):
            raise AssertionError("Directory entry '%s' does not exist in '%s'" % (base, dir))

    def create_files(self, path, count, size=0):
        """Create count number fixed size files in the given path.

        Fails if the files are already present.
        """
        count = int(count)
        size = int(size)
        if count <= 0:
            return
        fmt = "%%0%dd" % (int(math.log10(float(count))) + 1) # fixed width filenames
        if size > 0:
            block = '\0' * 8192
            blocks = size // len(block)
            partial = size % len(block)
            if partial > 0:
                pblock = '\0' * partial
        for i in xrange(0, count):
            num = os.path.join(path, fmt % (i))
            fd = os.open(num, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0777)
            if size > 0:
                for j in xrange(0, blocks):
                    if os.write(fd, block) != len(block):
                        raise IOError("Failed to write block %d to file '%s'" % (j,num))
                if partial:
                    if os.write(fd, pblock) != len(pblock):
                        raise IOError("Failed to write to file '%s'" % num)
            os.close(fd)


