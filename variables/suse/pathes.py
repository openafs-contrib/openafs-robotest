AFS_SERVER_ETC_DIR = "/etc/openafs/server"
AFS_SERVER_LIB_DIR  = "/var/lib/openafs"
AFS_SERVER_LIBEXEC_DIR  = "/usr/lib64/openafs"
AFS_CLIENT_ETC_DIR = "/etc/openafs"


if __name__ == "__main__":
    for var in dir() :
        if var.startswith("_") : continue
        print "%s='%s'" % (var, eval(var))

