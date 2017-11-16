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

"""Linux specific utilities."""

import logging
import os
import re

from afsutil.system import common as _mod
CommandMissing = _mod.CommandMissing
CommandFailed = _mod.CommandFailed
cat = _mod.cat
directory_should_exist = _mod.directory_should_exist
directory_should_not_exist = _mod.directory_should_not_exist
file_should_exist = _mod.file_should_exist
mkdirp = _mod.mkdirp
nproc = _mod.nproc
path_join = _mod.path_join
sh = _mod.sh
symlink = _mod.symlink
touch = _mod.touch
which = _mod.which

logger = logging.getLogger(__name__)

def get_running():
    """Get a set of running processes."""
    ps = which('ps')
    lines = sh(ps, '-e', '-f', quiet=True)
    # The first line of the `ps' output is a header line which is
    # used to find the data field columns.
    column = lines[0].index('CMD')
    procs = set()
    for line in lines[1:]:
        cmd_line = line[column:]
        if cmd_line[0] == '[':  # skip linux threads
            continue
        command = cmd_line.split()[0]
        procs.add(os.path.basename(command))
    return procs

def is_running(program):
    """Returns true if program is running."""
    return program in get_running()

def afs_mountpoint():
    mountpoint = None
    pattern = r'^AFS on (/.\S+)'
    mount = which('mount', extra_paths=['/bin', '/sbin', '/usr/sbin'])
    output = sh(mount, quiet=True)
    for line in output:
        found = re.search(pattern, line)
        if found:
            mountpoint = found.group(1)
    return mountpoint

def is_afs_mounted():
    """Returns true if afs is mounted."""
    return afs_mountpoint() is not None

def afs_umount():
    """Attempt to unmount afs, if mounted."""
    afs = afs_mountpoint()
    if afs:
        umount = which('umount', extra_paths=['/bin', '/sbin', '/usr/sbin'])
        sh(umount, afs)

def network_interfaces():
    """Return list of non-loopback network interfaces."""
    addrs = []
    output = sh('/sbin/ip', '-oneline', '-family', 'inet', 'addr', 'show')
    for line in output:
        match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
        if match:
            addr = match.group(1)
            if not addr.startswith("127."):
                addrs.append(addr)
    logger.debug("Found network interfaces: %s", ",".join(addrs))
    return addrs

def is_loaded(kmod):
    with open("/proc/modules", "r") as f:
        for line in f.readlines():
            if kmod == line.split()[0]:
                return True
    return False

def configure_dynamic_linker(path):
    """Configure the dynamic linker with ldconfig.

    Add a path to the ld configuration file for the OpenAFS shared
    libraries and run ldconfig to update the dynamic linker."""
    conf = '/etc/ld.so.conf.d/openafs.conf'
    paths = set()
    paths.add(path)
    if os.path.exists(conf):
        with open(conf, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line.startswith("#") or line == "":
                    continue
                paths.add(line)
    with open(conf, 'w') as f:
        logger.debug("Writing %s", conf)
        for path in paths:
            f.write("%s\n" % path)
    sh('/sbin/ldconfig')

def unload_module():
    output = sh('/sbin/lsmod')
    for line in output:
        kmods = re.findall(r'^(libafs|openafs)\s', line)
        for kmod in kmods:
            sh('rmmod', kmod)

def detect_gfind():
    return which('find')

def tar(tarball, source_path):
    sh('tar', 'czf', tarball, source_path, quiet=True)

def untar(tarball, chdir=None):
    savedir = None
    if chdir:
        savedir = os.getcwd()
        os.chdir(chdir)
    try:
        sh('tar', 'xzf', tarball, quiet=True)
    finally:
        if savedir:
            os.chdir(savedir)
