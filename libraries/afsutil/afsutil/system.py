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

"""System utilities for setting up AFS."""

import logging
import os
import re
import socket
import subprocess
import sys
import time

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


class CommandFailed(Exception):
    """Command exited with a non-zero exit code."""
    def __init__(self, args, code, out, err):
        self.cmd = subprocess.list2cmdline(args)
        self.args = args
        self.code = code
        self.out = out
        self.err = err

    def __str__(self):
        msg = "Command failed! %s; code=%d, stderr='%s'" % \
              (self.cmd, self.code, self.err.strip())
        return repr(msg)

def run(cmd, args=None, quiet=False, retry=0, wait=1, cleanup=None):
    """Run a command and return the output.

    Raises a CommandFailed exception if the command exits with an
    a non zero exit code."""
    if args is None:
        args = []
    else:
        args = list(args)
    cmd = which(cmd, raise_errors=True)
    args.insert(0, cmd)
    for attempt in xrange(0, (retry + 1)):
        if attempt > 0:
            c = os.path.basename(cmd)
            logger.info("Retrying %s command in %d seconds; retry %d of %d.", c, wait, attempt, retry)
            time.sleep(wait)
            if cleanup:
                cleanup()  # Try to cleanup the mess from the last failure.
        logger.debug("running: %s", subprocess.list2cmdline(args))
        proc = subprocess.Popen(
                   args,
                   executable=cmd,
                   shell=False,
                   bufsize=-1,
                   env=os.environ,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)
        output,error = proc.communicate()
        rc = proc.returncode
        logger.debug("result of %s; rc=%d", cmd, rc)
        if output:
            logger.debug("<stdout>")
            logger.debug(output)
            logger.debug("</stdout>")
        if error:
            logger.debug("<stderr>")
            logger.debug(error)
            logger.debug("</stderr>")
        if rc == 0:
            return output
    raise CommandFailed(args, rc, output, error);

def sh(*args, **kwargs):
    """Run the command line and write the output to the logger."""
    args = list(args)
    output = kwargs.get('output', False)
    quiet = kwargs.get('quiet', False)
    prefix = kwargs.get('prefix', '')
    if prefix:
        prefix = "%s: " % (prefix)
    args[0] = which(args[0], raise_errors=True)
    args = [arg.__str__() for arg in args]  # subprocess expects string args.
    output_lines = []
    tail = RingBuffer(20)  # Save the last few lines for error reporting.

    # Redirect stderr to the same pipe to capture errors too.
    if not quiet:
        cmdline = subprocess.list2cmdline(args)
        logger.info("running %s", cmdline)
    p = subprocess.Popen(args, bufsize=1, env=os.environ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    with p.stdout:
        for line in iter(p.stdout.readline, ''):
            line = line.rstrip("\n")
            tail.append(line)
            if not quiet:
                logger.info("%s%s", prefix, line)
            if output:
                output_lines.append(line)
    code = p.wait()
    if code != 0:
        raise CommandFailed(args, code, "", "\n".join(tail.get()))
    return output_lines

def which(program, extra_paths=None, raise_errors=False):
    """Find a program in the PATH."""
    dirname, basename = os.path.split(program)
    if dirname:
        # Full path was given; verify it is an executable file.
        if os.path.isfile(program) and os.access(program, os.X_OK):
            return program
        if raise_errors:
            raise AssertionError("Program '%s' is not an executable file." % (program))
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
            raise AssertionError("Could not find '%s' in paths %s" % (program, ":".join(paths)))
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
    lines = sh(ps, '-e', '-f', output=True, quiet=True)
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
    uname = os.uname()[0]
    if uname == 'Linux':
        pattern = r'^AFS on (/.\S+)'
    elif uname == 'SunOS':
        pattern = r'(/.\S+) on AFS'
    else:
        raise AssertionError("Unsupported operating system: %s" % (uname))
    mount = which('mount', extra_paths=['/bin', '/sbin', '/usr/sbin'])
    output = run(mount)
    found = re.search(pattern, output, re.M)
    if found:
        mountpoint = found.group(1)
    else:
        mountpoint = None
    return mountpoint

def is_afs_mounted():
    """Returns true if afs is mounted."""
    return afs_mountpoint() is not None

def afs_umount():
    """Attempt to unmount afs, if mounted."""
    afs = afs_mountpoint()
    if afs:
        umount = which('umount', extra_paths=['/bin', '/sbin', '/usr/sbin'])
        run(umount, args=[afs])

def nproc():
    """Return the number of processing units."""
    nproc = which('nproc')
    if nproc is None:
        return 1  # default
    return int(sh('nproc', output=True)[0])

def _linux_network_interfaces():
    """Return list of non-loopback network interfaces."""
    addrs = []
    out = run("/sbin/ip", args=["-oneline", "-family", "inet", "addr", "show"])
    for line in out.splitlines():
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
    run("/sbin/ldconfig")

def _linux_unload_module():
    output = run('/sbin/lsmod')
    kmods = re.findall(r'^(libafs|openafs)\s', output, re.M)
    for kmod in kmods:
        run('rmmod', args=[kmod])

def _linux_load_module(kmod):
    run('insmod', args=[kmod])

def _linux_detect_gfind():
    return which('find')

def _solaris_network_interfaces_old():
    """Return a list of non-loopback networks interfaces."""
    addrs = []
    lines = sh('/usr/sbin/ifconfig', '-a', output=True, quiet=True)
    for line in lines:
        match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
        if match:
            addr = match.group(1)
            if not addr.startswith("127."):
                addrs.append(addr)
    return addrs

def _solaris_network_interfaces():
    """Return list of non-loopback network interfaces."""
    addrs = []
    out = run("ipadm", args=["show-addr", "-p", "-o", "STATE,ADDR"])
    for line in out.splitlines():
        match = re.match(r'ok:(\d+\.\d+\.\d+\.\d+)', line)
        if match:
            addr = match.group(1)
            if not addr.startswith("127."):
                addrs.append(addr)
    return addrs

def _solaris_is_loaded(kmod):
    """Returns the list of currently loaded kernel modules."""
    out = run("/usr/sbin/modinfo", args=["-w"])
    for line in out.splitlines()[1:]: # skip header line
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
    run("/usr/bin/crle", args=["-u", "-l", path])
    run("/usr/bin/crle", args=["-64", "-u", "-l", path])

def _solaris_unload_module():
    module_id = _solaris_is_loaded('afs')
    if module_id != 0:
        run('modunload', args=["-i", module_id])

def _solaris_load_module(kmod):
    # Adpapted from the solaris openafs-client init script.
    afs = '/kernel/drv/amd64/afs' # modern path
    sh('cp', kmod, afs)
    logger.info("Loading AFS kernel extensions.")
    sh('modload', afs)

def check_hosts_file():
    """Check for loopback addresses in the /etc/hosts file.

    Modern linux distros assign a loopback address to the hostname. While not
    strictly incorrect, this can confuse OpenAFS which gets our IP address from
    gethostbyname()."""
    result = True
    nr = 0
    hostname = socket.gethostname()
    with open('/etc/hosts', 'r') as f:
        for line in f.readlines():
            nr += 1
            if line.startswith('127.'):
                if hostname in line.split()[1:]:
                    sys.stderr.write(
                        "Warning: loopback address '%s' assigned to our hostname '%s' on line %d of /etc/hosts.\n" % \
                        (line.split()[0], hostname, nr))
                    result = False
    return result

def fix_hosts_file():
    hostname = socket.gethostname()
    ips = network_interfaces()
    if len(ips) == 0:
        raise AssertionError("Unable to detect any non-loopback network interfaces.")
    ip = ips[0]

    with open('/etc/hosts', 'r') as f:
        hosts = f.read()

    with open('/etc/hosts', 'w') as f:
        for line in hosts.splitlines():
            line = line.strip()
            if not re.search(r'\b%s\b' % (hostname), line):
                f.write("%s\n" % line)
        f.write("%s\t%s\n" % (ip, hostname))

def check_host_address():
    """Verify our hostname resolves to a useable address."""
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    ips = network_interfaces()
    if len(ips) == 0:
        sys.stderr.write("Warning: Unable to detect any non-loopback network interfaces.\n")
        return False
    if not ip in ips:
        sys.stderr.write("Warning: hostname '%s' resolves to '%s', not found in network interfaces: '%s'.\n" % \
                         (hostname, ip, " ".join(ips)))
        return False
    return True

_uname = os.uname()[0]
_osrel = os.uname()[2]
if _uname == "Linux":
    network_interfaces = _linux_network_interfaces
    is_loaded = _linux_is_loaded
    configure_dynamic_linker = _linux_configure_dynamic_linker
    unload_module = _linux_unload_module
    load_module = _linux_load_module
    detect_gfind = _linux_detect_gfind
elif _uname == "SunOS":
    if _osrel == "5.10":
        network_interfaces = _solaris_network_interfaces_old
    else:
        network_interfaces = _solaris_network_interfaces
    is_loaded = _solaris_is_loaded
    configure_dynamic_linker = _solaris_configure_dynamic_linker
    unload_module = _solaris_unload_module
    load_module = _solaris_load_module
    detect_gfind = _solaris_detect_gfind
else:
    raise AssertionError("Unsupported operating system: %s" % (_uname))

