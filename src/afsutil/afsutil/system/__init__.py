
from os import uname as _uname
if _uname()[0] == "Linux":
    from afsutil.system import linux as _mod
elif _uname()[0] == "SunOS":
    from afsutil.system import sunos as _mod
else:
    raise ImportError("Unsuppored uname")

CommandMissing = _mod.CommandMissing
CommandFailed = _mod.CommandFailed
afs_mountpoint = _mod.afs_mountpoint
afs_umount = _mod.afs_umount
cat = _mod.cat
configure_dynamic_linker = _mod.configure_dynamic_linker
detect_gfind = _mod.detect_gfind
directory_should_exist = _mod.directory_should_exist
directory_should_not_exist = _mod.directory_should_not_exist
file_should_exist = _mod.file_should_exist
get_running = _mod.get_running
is_afs_mounted = _mod.is_afs_mounted
is_loaded = _mod.is_loaded
is_running = _mod.is_running
mkdirp = _mod.mkdirp
network_interfaces = _mod.network_interfaces
nproc = _mod.nproc
path_join = _mod.path_join
sh = _mod.sh
symlink = _mod.symlink
tar = _mod.tar
touch = _mod.touch
unload_module = _mod.unload_module
untar = _mod.untar
which = _mod.which
