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

"""System utilities."""

import logging
import os
import re
import subprocess
import sys

logger = logging.getLogger(__name__)

class RingBuffer:
    """Circular array for appending."""
    # Adapted from the python cookbook.
    def __init__(self, size_max):
        self.size_max = size_max
        self.data = []

    class __FullBuffer:
        def append(self, x):
            """Append an element overwriting the oldest one."""
            self.data[self.cursor] = x
            self.cursor = (self.cursor + 1) % self.size_max

        def get(self):
            """Return list of elements in correct order."""
            return self.data[self.cursor:] + self.data[:self.cursor]

    def append(self,x):
        """Append an element at the end of the buffer."""
        self.data.append(x)
        if len(self.data) == self.size_max:
            # We are full; switch to the circular functions.
            self.cursor = 0
            self.__class__ = self.__FullBuffer

    def get(self):
        """ Return a list of elements from the oldest to the newest. """
        return self.data


class CommandMissing(Exception):
    """Command not found."""

class CommandFailed(Exception):
    """Command exited with a non-zero exit code."""
    def __init__(self, args, code, out):
        self.cmd = subprocess.list2cmdline(args)
        self.args = args
        self.code = code
        self.out = out

    def __str__(self):
        msg = "Command failed! %s; code=%d, out='%s'" % \
              (self.cmd, self.code, self.out.strip())
        return repr(msg)

def sh(*args, **kwargs):
    """Execute the command line arguments.

    Execute the command line and optionally return the output as
    a list of lines.  Raises a CommandFailed exception if the
    command exits with a non-zero code.

    args:     command-line arguments
    output:   return output lines as a list (default: True)
    quiet:    do not log command line and output (default: False)
    prefix:   log message prefix (default: None)
    sed:      output line filter function (default: None)
    dryrun:   print the command instead of executing it (defualt: False)
    tailsize: number of lines to report when output=False (default:20)
    """
    output = kwargs.get('output', True)
    quiet = kwargs.get('quiet', False)
    prefix = kwargs.get('prefix', None)
    sed = kwargs.get('sed', None)
    dryrun = kwargs.get('dryrun', False)
    tailsize = kwargs.get('tailsize', 20)

    # Fixup the argument list for Popen.
    # 1. Create a tuple if just one arg was given.
    # 2. Convert numeric args to strings.
    if isinstance(args, basestring):
        args = (args)
    args = [arg.__str__() for arg in args]

    # Be sure the first arg is actually a program, otherwise Popen
    # will fail with a cryptic exception.
    args[0] = which(args[0], raise_errors=True)
    cmdline = subprocess.list2cmdline(args)

    # Dryrun mode: Just print what would be run.
    if dryrun:
        sys.stdout.write("%s\n" % (cmdline))
        return

    # Execute command and process output.
    lines = []
    if output and not sed:
        tail = None
    else:
        tail = RingBuffer(tailsize)  # Save the tail for error reporting.
    if quiet:
        if prefix:
            logger.debug("%s: running: %s", prefix, cmdline)
        else:
            logger.debug("running: %s", cmdline)
    else:
        if prefix:
            logger.info("%s: running: %s", prefix, cmdline)
        else:
            logger.info("running: %s", cmdline)
    p = subprocess.Popen(args,
                        bufsize=1,
                        env=os.environ,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT) # Redirect stderr capture errors.
    with p.stdout:
        for line in iter(p.stdout.readline, ''):
            line = line.rstrip("\n")
            if tail:
                tail.append(line)
            if not quiet:
                if prefix:
                    logger.info("%s: %s", prefix, line)
                else:
                    logger.info("%s", line)
            if output:
                if sed:
                    line = sed(line)
                if line:
                    lines.append(line)
    code = p.wait()
    if code != 0:
        if tail:
            lines = tail.get()
        out = "\n".join(lines)
        raise CommandFailed(args, code, out)
    return lines

def which(program, extra_paths=None, raise_errors=False):
    """Find a program in the PATH.

    program: program name or program full path
    extra_paths: list of paths to search in addition to PATH
    raise_errors: raise an exception if not found (default: False)
    """
    if not isinstance(program, basestring):
        raise ValueError("which() requires a string argument")
    dirname,basename = os.path.split(program)
    if dirname:
        # Full path was given; verify it is an executable file.
        if os.path.isfile(program) and os.access(program, os.X_OK):
            return program
        if raise_errors:
            raise CommandMissing("Program '%s' is not an executable file." % (program))
    else:
        # Just the basename was given; search the paths.
        paths = os.environ['PATH'].split(os.pathsep)
        if extra_paths:
            paths = paths + extra_paths
        for path in paths:
            path = path.strip('"')
            fpath = os.path.join(path, program)
            if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
                return fpath
        if raise_errors:
            raise CommandMissing("Could not find '%s' in paths %s" % (program, ":".join(paths)))
    return None

def file_should_exist(path, description=None):
    """Fails if the given file does not exist."""
    if not os.path.isfile(path):
        if description is None:
            description = "File '%s' does not exist." % (path)
        raise AssertionError(description)
    return True

def directory_should_exist(path, description=None):
    """Fails if the given directory does not exist."""
    if not os.path.isdir(path):
        if description is None:
            description = "Directory '%s' does not exist." % (path)
        raise AssertionError(description)
    return True

def directory_should_not_exist(path, description=None):
    """Fails if the given directory does exist."""
    if os.path.exists(path):
        if description is None:
            description = "Directory '%s' already exists." % (path)
        raise AssertionError(description)
    return True

def path_join(a, *p):
    # os.path.join() is brain dead.
    p = [x.lstrip('/') for x in p]
    return os.path.join(a, *p)

def get_running():
    """Get a set of running processes."""
    if os.uname()[0] == 'SunOS':
        ps = which('/usr/bin/ps') # avoid the old BSD variant
    else:
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
    uname = os.uname()[0]
    if uname == 'Linux':
        pattern = r'^AFS on (/.\S+)'
    elif uname == 'SunOS':
        pattern = r'(/.\S+) on AFS'
    else:
        raise AssertionError("Unsupported operating system: %s" % (uname))
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

def nproc():
    """Return the number of processing units."""
    nproc = which('nproc')
    if nproc is None:
        return 1  # default
    return int(sh('nproc')[0])

def _linux_network_interfaces():
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

def _linux_is_loaded(kmod):
    with open("/proc/modules", "r") as f:
        for line in f.readlines():
            if kmod == line.split()[0]:
                return True
    return False

def _linux_configure_dynamic_linker(path):
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

def _linux_unload_module():
    output = sh('/sbin/lsmod')
    for line in output:
        kmods = re.findall(r'^(libafs|openafs)\s', line)
        for kmod in kmods:
            sh('rmmod', kmod)

def _linux_detect_gfind():
    return which('find')

def _solaris_network_interfaces():
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

def _solaris_is_loaded(kmod):
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

def _solaris_detect_gfind():
    return which('gfind', extra_paths=['/opt/csw/bin'])

def mkdirp(path):
    """Make a directory with parents."""
    # Do not raise an execption if the directory already exists.
    if not os.path.isdir(path):
        os.makedirs(path)

def cat(files, path):
    """Combine one or more files."""
    dst = open(path, 'w')
    for f in files:
        with open(f, 'r') as src:
            dst.write(src.read())
    dst.close()

def touch(path):
    """Touch a file; create a empty file if not already existing."""
    with open(path, 'a'):
        os.utime(path, None)

def symlink(src, dst):
    """Create a symlink dst to src."""
    logger.debug("Creating symlink %s -> %s", dst, src)
    if not os.path.isfile(src):
        raise AssertionError("Failed to make symlink: src %s not found" % (src))
    if os.path.exists(dst) and not os.path.islink(dst):
        raise AssertionError("Failed to make symlink: dst %s exists" % (dst))
    if os.path.islink(dst):
        os.remove(dst)
    os.symlink(src, dst)

def tar(tarball, source_path):
    tar = 'gtar' if os.uname()[0] == "SunOS" else 'tar'
    sh(tar, 'czf', tarball, source_path, quiet=True)

def untar(tarball, chdir=None):
    savedir = None
    if chdir:
        savedir = os.getcwd()
        os.chdir(chdir)
    tar = 'gtar' if os.uname()[0] == "SunOS" else 'tar'
    try:
        sh(tar, 'xzf', tarball, quiet=True)
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

def _solaris_configure_dynamic_linker(path):
    if not os.path.isdir(path):
        raise AssertionError("Failed to configure dynamic linker: path %s not found." % (path))
    _so_symlinks(path)
    sh('/usr/bin/crle', '-u', '-l', path)
    sh('/usr/bin/crle', '-64', '-u', '-l', path)

def _solaris_unload_module():
    module_id = _solaris_is_loaded('afs')
    if module_id != 0:
        sh('modunload', '-i', module_id)

_uname = os.uname()[0]
if _uname == "Linux":
    network_interfaces = _linux_network_interfaces
    is_loaded = _linux_is_loaded
    configure_dynamic_linker = _linux_configure_dynamic_linker
    unload_module = _linux_unload_module
    detect_gfind = _linux_detect_gfind
elif _uname == "SunOS":
    network_interfaces = _solaris_network_interfaces
    is_loaded = _solaris_is_loaded
    configure_dynamic_linker = _solaris_configure_dynamic_linker
    unload_module = _solaris_unload_module
    detect_gfind = _solaris_detect_gfind
else:
    raise AssertionError("Unsupported operating system: %s" % (_uname))
