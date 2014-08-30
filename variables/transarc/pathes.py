AFS_SERVER_ETC_DIR = "/usr/afs/etc"
AFS_SERVER_LIB_DIR  = "/usr/afs/lib"
AFS_SERVER_LIBEXEC_DIR  = "/usr/afs/bin"
AFS_CLIENT_ETC_DIR = "/usr/vice/etc"


if __name__ == "__main__":
    for var in dir() :
        if var.startswith("_") : continue
        print "%s='%s'" % (var, eval(var))

