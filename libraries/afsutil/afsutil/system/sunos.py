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

"""Solaris specific utilities."""

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
    ps = which('/usr/bin/ps') # avoid the old BSD variant
    lines = sh(ps, '-e', '-f', quiet=True)
    # The first line of the `ps' output is a header line which is
    # used to find the data field columns.
    column = lines[0].index('CMD')
    procs = set()
    for line in lines[1:]:
        cmd_line = line[column:]
        command = cmd_line.split()[0]
        procs.add(os.path.basename(command))
    return procs

def is_running(program):
    """Returns true if program is running."""
    return program in get_running()

def afs_mountpoint():
    mountpoint = None
    pattern = r'(/.\S+) on AFS'
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
    try:
        command = which('ipadm')
        args = ('show-addr', '-p', '-o', 'STATE,ADDR')
        pattern = r'ok:(\d+\.\d+\.\d+\.\d+)'
    except CommandMissing:
        # Fall back to old command on old solaris releases.
        command = which('/usr/sbin/ifconfig')
        args = ('-a')
        pattern = r'inet (\d+\.\d+\.\d+\.\d+)'
    addrs = []
    output = sh(command, *args)
    for line in output:
        match = re.match(pattern, line)
        if match:
            addr = match.group(1)
            if not addr.startswith("127."):
                addrs.append(addr)
    return addrs

def is_loaded(kmod):
    """Returns the list of currently loaded kernel modules."""
    output = sh('/usr/sbin/modinfo', '-w')
    for line in output[1:]: # skip header line
        # Fields are: Id Loadaddr Size Info Rev Module (Name)
        m = re.match(r'\s*(\d+)\s+\S+\s+\S+\s+\S+\s+\d+\s+(\S+)', line)
        if not m:
            raise AssertionError("Unexpected modinfo output: %s" % (line))
        mid = m.group(1)  # We will need the id to remove the module.
        mname = m.group(2)
        if kmod == mname:
            return mid
    return 0

def detect_gfind():
    return which('gfind', extra_paths=['/opt/csw/bin'])

def tar(tarball, source_path):
    sh('gtar', 'czf', tarball, source_path, quiet=True)

def untar(tarball, chdir=None):
    savedir = None
    if chdir:
        savedir = os.getcwd()
        os.chdir(chdir)
    try:
        sh('gtar', 'xzf', tarball, quiet=True)
    finally:
        if savedir:
            os.chdir(savedir)

def _so_symlinks(path):
    """Create shared lib symlinks."""
    if not os.path.isdir(path):
        assert AssertionError("Failed to make so symlinks: path '%s' is not a directory.", path)
    for dirent in os.listdir(path):
        fname = os.path.join(path, dirent)
        if os.path.isdir(fname) or os.path.islink(fname):
            continue
        m = re.match(r'(.+\.so)\.(\d+)\.(\d+)\.(\d+)$', fname)
        if m:
            so,x,y,z = m.groups()
            symlink(fname, "%s.%s.%s" % (so, x, y))
            symlink(fname, "%s.%s" % (so, x))
            symlink(fname, so)

def configure_dynamic_linker(path):
    if not os.path.isdir(path):
        raise AssertionError("Failed to configure dynamic linker: path %s not found." % (path))
    _so_symlinks(path)
    sh('/usr/bin/crle', '-u', '-l', path)
    sh('/usr/bin/crle', '-64', '-u', '-l', path)

def unload_module():
    module_id = is_loaded('afs')
    if module_id != 0:
        sh('modunload', '-i', module_id)
