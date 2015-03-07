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
from robot.api import logger

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
        cmd = "sudo -n %s %s" % (cmd, " ".join(args))
        logger.debug("running: %s" % cmd)
        pipe = os.popen("%s 2>&1" % (cmd))
        output = pipe.readlines()
        rc = pipe.close()
        if rc:
            for line in output:
                logger.error(line.strip())
            raise AssertionError("Fail: %s" % (cmd))

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

