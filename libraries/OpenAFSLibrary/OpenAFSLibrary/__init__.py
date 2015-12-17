# Copyright (c) 2014-2015 Sine Nomine Associates
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

from OpenAFSLibrary.keywords import *
from OpenAFSLibrary.version import VERSION

__version__ = VERSION

class OpenAFSLibrary(
    _SystemKeywords,
    _LoginKeywords,
    _PathKeywords,
    _ACLKeywords,
    _VolumeKeywords,
    _RxKeywords):
    """Robot Framework test library for OpenAFS (preliminary).

    `OpenAFSLibrary` provides keywords for basic OpenAFS testing. It
    includes keywords to install OpenAFS client and servers and
    setup a cell for testing.

    = Settings =

    == Test cell name ==

    The following settings specify the test cell and user names:
    | AFS_CELL          | Test cell name |
    | AFS_ADMIN         | Test cell admin username |
    | AFS_USER          | Test cell username |

    == Test cell options ==

    The following settings determine how OpenAFS is installed:
    | AFS_DIST          | Distribution style; one of 'rhel6','suse','transarc' |
    | AFS_AKIMPERSONATE | Use akimpersonate for Kerberos-less testing |
    | AFS_KEY_FILE      | Service key style; one of 'KeyFile','rxkad.keytab','KeyFileExt' |
    | AFS_DAFS          | Run the DAFS fileserver |
    | AFS_CSDB_DIST     | Pathname of file with extra CellServDB entries |
    | DO_TEARDOWN       | Perform the cell teardown after running the tests |

    == Kerberos options ==

    The following settings are used when `AFS_AKIMPERSONATE` is `False`:
    | KRB_ADMIN_KEYTAB  | Admin user keytab file |
    | KRB_AFS_ENCTYPE   | AFS service key encryption type |
    | KRB_AFS_KEYTAB    | AFS service keytab file |
    | KRB_USER_KEYTAB   | Test user keytab |
    | KADMIN_LOCAL      | Kerberos kadmin.local pathname |
    | KADMIN            | Kerberos kadmin pathname |
    | KDESTROY          | Kerberos kdestroy pathname |
    | KINIT             | Kerberos kinit pathname |
    | KLIST             | Kerberos klist pathname |

    == RPM options ==

    The following options are used when `AFS_DIST` refers to an RPM based
    distribution:
    | RPM_AFSRELEASE    | RPM release number |
    | RPM_AFSVERSION    | AFS Version Number |
    | RPM_PACKAGE_DIR   | Path the RPM packages |

    == Transarc style options ==

    The following options are used when `AFS_DIST` is `transarc`:
    | TRANSARC_DEST     | Directory containing binaries |
    | TRANSARC_TARBALL  | Optional pathname of tar archive |
    | GTAR              | GNU tar utility pathname |


    == Distribution options ==

    === Directory paths ===

    The following settings are used to specify the directory paths
    used by the OpenAFS binaries.
    | AFS_CONF_DIR        |   `/usr/afs/etc` |
    | AFS_KERNEL_DIR      |   `/usr/vice/etc` |
    | AFS_SRV_BIN_DIR     |    `/usr/afs/bin` |
    | AFS_SRV_SBIN_DIR    |   `/usr/afs/bin` |
    | AFS_SRV_LIBEXEC_DIR |   `/usr/afs/bin` |
    | AFS_DB_DIR          |   `/usr/afs/db` |
    | AFS_LOGS_DIR        |   `/usr/afs/logs` |
    | AFS_LOCAL_DIR       |   `/usr/afs/local` |
    | AFS_BACKUP_DIR      |   `/usr/afs/backup` |
    | AFS_BOS_CONFIG_DIR  |   `/usr/afs/local` |
    | AFS_DATA_DIR        |   `/usr/vice/etc` |
    | AFS_CACHE_DIR       |   `/usr/vice/cache` |

    === Command paths ===

    | AKLOG   |   `/usr/afsws/bin/aklog` |
    | ASETKEY |   `/usr/afs/bin/asetkey` |
    | BOS     |   `/usr/afs/bin/bos` |
    | FS      |   `/usr/afs/bin/fs` |
    | PTS     |   `/usr/afs/bin/pts` |
    | RXDEBUG |   `/usr/afsws/etc/rxdebug` |
    | TOKENS  |   `/usr/afsws/bin/tokens` |
    | UDEBUG  |   `/usr/afs/bin/udebug` |
    | UNLOG   |   `/usr/afsws/bin/unlog` |
    | VOS     |   `/usr/afs/bin/vos` |

    === Startup options ===

    | BOSSERVER_OPTIONS |  "-pidfiles" |
    | AFSD_OPTIONS      |  "-dynroot -fakestat" |
    | AFSD_DYNROOT      |  Try if dynroot is set |


    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = __version__


