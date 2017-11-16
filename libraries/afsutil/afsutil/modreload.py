# Copyright (c) 2014-2017 Sine Nomine Associates
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

"""Reload the client after rebuilding from source (developer tool)"""

import logging
import os
import re

from afsutil.system import file_should_exist
import afsutil.service

logger = logging.getLogger(__name__)

def _linux_kernel_packaging():
    """Returns true if built with --with-linux-kernel-packaging."""
    value = False
    with open('src/config/Makefile.config', 'r') as f:
        for line in f.readlines():
            m = re.search(r'^LINUX_KERNEL_PACKAGING = (\S+)', line)
            if m:
                value = (m.group(1) == 'yes')
                break
    return value

def _linux_libafs_name():
    """Get the libafs filename."""
    sysname, nodename, release, version, machine = os.uname()
    if _linux_kernel_packaging():
        libafs = 'openafs.ko'
    else:
        mp = '.mp' if 'SMP' in version else ''
        libafs = "libafs-%s%s.ko" % (release, mp)
    return libafs

def _linux_modload_name():
    """Get the modload directory name."""
    sysname, nodename, release, version, machine = os.uname()
    if _linux_kernel_packaging():
        modload = "MODLOAD-%s-SP" % (release)
    else:
        mp = 'MP' if 'SMP' in version else 'SP'
        modload = "MODLOAD-%s-%s" % (release, mp)
    return modload

def _kmod():
    """Get the kernel module file name in the build tree."""
    sysname = os.uname()[0]
    if sysname == 'Linux':
        libafs = _linux_libafs_name()
        modload = _linux_modload_name()
        kmod = os.path.abspath("src/libafs/%s/%s" % (modload, libafs))
    elif sysname == 'SunOS':
        kmod = os.path.abspath("src/libafs/MODLOAD64/libafs.o")
    else:
        raise AssertionError("Unsupported operating system: %s" % (sysname))
    return kmod

def _client_setup():
    """Get the client setup object for this os."""
    uname = os.uname()[0]
    if uname == "Linux":
        cs = afsutil.transarc.LinuxClientSetup()
    elif uname == "SunOS":
        cs = afsutil.transarc.SolarisClientSetup()
    else:
        raise AssertionError("Unsupported operating system: %s" % (uname))
    return cs

def modreload(**kwargs):
    """Reload the kernel module and restart the cache manager after a build.

    This is a helper for testing and debugging the afs kernel module and afsd
    without resorting to a full reinstallation after every code change. The cache
    manager must be installed at least once, then can be reloaded after each code
    change and build with this function.

    This should be run as root in the top level source directory. At this time,
    only transarc-style installations are supported by modreload.

    A typical workflow, using the afsutil front-end script:

        $ sudo afsutil install --dist transarc [options]
        $ sudo afsutil start client
        ... test/debug/etc ...
        ... edit files in src/afs ...

        $ make libafs
        $ sudo afsutil reload
        ... test/debug/etc ...
        ... edit files in src/afs ...

        $ make libafs
        $ sudo afsutil reload
        ... repeat ...
    """
    cs = _client_setup()
    afsd = os.path.abspath('src/afsd/afsd')
    kmod = _kmod()
    file_should_exist(afsd)        # Check before stopping.
    file_should_exist(kmod)
    afsutil.service.stop(components=['client'])
    cs.install_afsd(afsd)
    cs.install_kmod(kmod)
    afsutil.service.start(components=['client'])
