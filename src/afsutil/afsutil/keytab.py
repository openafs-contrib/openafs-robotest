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
#

"""Utility to set the AFS service key."""

import hashlib
import os
import struct
import time
import logging
import shutil

from afsutil.system import CommandFailed, mkdirp
from afsutil.transarc import AFS_CONF_DIR
from afsutil.cmd import asetkey, aklog

logger = logging.getLogger(__name__)

KFORMATS = ['transarc', 'rxkad-k5', 'extended']
DEFAULT_KEYTAB = "/tmp/afs.keytab"
DEFAULT_USER = "admin"

KRB_ENCTYPES = {
    1: 'des-cbc-crc',
    2: 'des-cbc-md4',
    3: 'des-cbc-md5',
    5: 'des3-cbc-md5',
    7: 'des3-cbc-sha1',
    9: 'dsaWithSHA1-CmsOID',
    10: 'md5WithRSAEncryption-CmsOID',
    11: 'sha1WithRSAEncryption-CmsOID',
    12: 'rc2CBC-EnvOID',
    13: 'rsaEncryption-EnvOID',
    14: 'rsaES-OAEP-ENV-OID',
    15: 'des-ede3-cbc-Env-OID',
    16: 'des3-cbc-sha1-kd',
    17: 'aes128-cts-hmac-sha1-96',
    18: 'aes256-cts-hmac-sha1-96',
    23: 'rc4-hmac',
    24: 'rc4-hmac-exp',
    25: 'camellia128-cts-cmac',
    26: 'camellia256-cts-cmac',
    65: 'subkey-keymaterial',
}

# Helpers

def _split_principal(principal):
    """Split a fully qualified principal string into (components, realm)."""
    if not '@' in principal:
        raise ValueError("Missing realm name in principal")
    names,realm = principal.split('@')
    comps = names.split('/')
    return (comps, realm)

def _lookup_eno(enctype):
    """Lookup the eno (number) from the enctype (string)."""
    enos = {}
    for k,v in KRB_ENCTYPES.items():
        assert not v in enos
        enos[v] = k
    try:
        eno = enos[enctype]
    except KeyError:
        raise ValueError("Unsupported enctype '%s'." % enctype)
    return eno

def _is_des_eno(eno):
    """Return true if the eno is for a DES enctype."""
    return (eno in (1,2,3,15))

def _check_for_extended_keyfile_support():
    """Returns true if asetkey supports the new extended key files.

    Runs asetkey without options to elicit the usage message, then
    checks for the new 'add' subcommand."""
    logger.debug("Checking if asetkey supports extended key files.")
    usage = None
    try:
        usage = asetkey(quiet=True)
    except CommandFailed as e:
        usage = e.out
    logger.debug("asetkey usage: %s", usage)
    if usage is None or not "usage" in usage:
        raise AssertionError("Failed to get asetkey usage.")
    new_asetkey = "add <type> <kvno> <subtype> <keyfile> <princ>" in usage
    if new_asetkey:
        logger.info("asetkey supports extended key format.")
    else:
        logger.info("asetkey does not support extended key format.")
    return new_asetkey

class KeytabException(Exception):
    pass

class InvalidKeytab(KeytabException):
    pass

class NotFoundKeytab(KeytabException):
    pass

class Keytab(object):
    """Utility to support testing with keytabs and akimpersonate.

    Examples:
        from afsutil.keytab import Keytab
        principal = "afs/mycell@MYREALM"

        # Create a fake keytab file for testing with akimpersonate.
        k = Keytab()
        k.add_fake_key(principal)
        k.write("path/to/my/fake.keytab")

        # Read an existing keytab file and find entries.
        k = Keytab().load("path/to/my/file.keytab")
        kvno = k.get_kvno(principal)
        for e in k.get_entries(principal):
            print e['kvno'], e['principal'], e['enctype']
        if k.is_des(principal):
            print "DES service key present"

        # Create an empty keytab file.
        # The created file will have the current user permissions
        # and can be updated with sudo kadmin.local.
        k = Keytab()
        k.write("path/to/my/empty.keytab")


    """
    _KRB_KEYTAB_MAGIC_OLD = 0x0501
    _KRB_KEYTAB_MAGIC = 0x0502
    _KRB_NT_PRINCIPAL = 1

    # The following C-like structure definitions illustrate the MIT keytab
    # file format. All values are in network byte order. All text is ASCII.
    #
    #   keytab {
    #       uint16_t file_format_version;                    /* 0x502 */
    #       keytab_entry entries[*];
    #   };
    #   keytab_entry {
    #       int32_t size;
    #       uint16_t num_components;    /* sub 1 if version 0x501 */
    #       counted_octet_string realm;
    #       counted_octet_string components[num_components];
    #       uint32_t name_type;   /* not present if version 0x501 */
    #       uint32_t timestamp;
    #       uint8_t vno8;
    #       keyblock key;
    #       uint32_t vno; /* only present if >= 4 bytes left in entry */
    #   };
    #   counted_octet_string {
    #       uint16_t length;
    #       uint8_t data[length];
    #   };
    #   keyblock {
    #       uint16_t type;
    #       counted_octet_string key;
    #   };

    def __init__(self):
        self.entries = []
        self.filename = None

    @classmethod
    def load(cls, path):
        keytab = cls()
        keytab.read(path)
        return keytab

    def _read(self, f, fmt):
        """Read and unpack one or more fields."""
        size = struct.calcsize(fmt)
        data = f.read(size)
        if len(data) != size:
            raise IOError("Failed to read keytab data.")
        return struct.unpack(fmt, data) # returns a tuple

    def _write(self, f, fmt, *args):
        """Pack and write one or more fields."""
        data = struct.pack(fmt, *args)
        f.write(data)

    def _read_string(self, f):
        """Read and unpack a string."""
        length = self._read(f, "!H")
        string, = self._read(f, "%ds" % length)
        return string

    def _write_string(self, f, s):
        """Pack and write a string."""
        self._write(f, "!H%ds" % (len(s)), len(s), s)

    def _read_entry(self, f, version):
        numc, = self._read(f, "!h")
        if version == 0x0501:
            numc -= 1
        realm = self._read_string(f)
        comps = []
        for i in xrange(0, numc):
            comps.append(self._read_string(f))
        if version != 0x0501:
            name_type, = self._read(f, "!L")
        timestamp, = self._read(f, "!L")
        vno8, = self._read(f, "!B")
        eno, = self._read(f, "!H")
        key = self._read_string(f)
        principal = "%s@%s" % ('/'.join(comps), realm)
        entry = {
            'realm': realm,
            'components': comps,
            'principal': principal,
            'timestamp': timestamp,
            'kvno': vno8,
            'eno': eno,
            'enctype': KRB_ENCTYPES[eno],
            'key': key,
        }
        return entry

    def _write_entry(self, f, k):
        # first pass: predicate the size to be written
        fmt = ["!"]
        fmt.append("h")  # number of components
        fmt.append("H%ds" % (len(k['realm'])))
        for c in k['components']:
            fmt.append("H%ds" % (len(c))) # c[i]
        fmt.append("L") # KRB_NT_PRINCIPAL
        fmt.append("L") # timestamp
        fmt.append("B") # kvno
        fmt.append("H") # eno
        fmt.append("H%ds" % len(k['key'])) # key
        size = struct.calcsize("".join(fmt))
        # second pass: write the data
        self._write(f, "!l", size)
        self._write(f, "!h", len(k['components']))
        self._write_string(f, k['realm'])
        for c in k['components']:
            self._write_string(f, c)
        self._write(f, "!L", Keytab._KRB_NT_PRINCIPAL)
        self._write(f, "!L", k['timestamp'])
        self._write(f, "!B", k['kvno'])
        self._write(f, "!H", k['eno'])
        self._write_string(f, k['key'])

    def _kdf(self, secret, size):
        """For test purposes only."""
        h = hashlib.sha256()
        if secret:
            h.update(secret)
        else:
            h.update(os.urandom(size))
        d = h.digest()
        return d.ljust(size)[:size]

    def _generate_des_key(self, secret):
        """Generate a random DES key with correct parity bits."""
        keybytes = bytearray(self._kdf(secret, 8))
        key = bytearray(0)
        for i in keybytes:
            b = bin(i & 0xfe)
            nb = len(b.split('1'))
            # nb is one more than the number of bits set
            key.append(int(b, 2) + (nb % 2))
        return bytes(key)

    def read(self, path):
        """Read the entries from a keytab file.

        Read the data from the keytab file directly. This avoid requiring
        the external klist utility on systems where akimpersonate is
        used instead of kinit.
        """
        logger.debug("reading keytab %s", path)
        self.filename = path
        try:
            stat = os.stat(path)
        except OSError as e:
            if e.errno == os.errno.ENOENT:
                raise NotFoundKeytab("File {0} not found.".format(path))
            else:
                raise e
        file_size = stat.st_size
        with open(path, 'r') as f:
            offset = struct.calcsize("!h")
            try:
                version, = self._read(f, "!h")
            except IOError:
                raise InvalidKeytab("File {0} is not keytab.".format(path))
            if version != 0x0502 and version != 0x051:  # magic
                raise InvalidKeytab("File {0} is not keytab.".format(path))
            while offset < file_size:
                f.seek(offset)
                size, = self._read(f, "!l") # record size, not including this field
                entry = self._read_entry(f, version)
                self.entries.append(entry)
                # Calculate next record location.
                record_size = struct.calcsize("!l") + size
                offset += record_size
        return self

    def add_fake_key(self, principal, enctype='aes256-cts-hmac-sha1-96', secret=None):
        """Create a synthetic key for testing with akimpersonate."""
        logger.debug("Adding fake key for principal '%s', enctype='%s'.", principal, enctype)
        timestamp = int(time.time())
        kvno = 1
        comps,realm = _split_principal(principal)
        if isinstance(enctype, int):
            eno = enctype
        else:
            eno = _lookup_eno(enctype)
        if _is_des_eno(eno):
            key = self._generate_des_key(secret)
        elif eno == 17:
            key = self._kdf(secret, 16)
        elif eno == 18:
            key = self._kdf(secret, 32)
        else:
            raise AssertionError("Unsupported enctype for fake keytab: eno=%d" % eno)
        entry = {
           'realm': realm,
           'components': comps,
           'principal': principal,
           'timestamp': timestamp,
           'kvno': kvno,
           'eno': eno,
           'enctype': KRB_ENCTYPES[eno],
           'key': key,
        }
        self.entries.append(entry)
        return self

    def write(self, path):
        logger.debug("Writing keytab %s", path)
        mkdirp(os.path.dirname(path))
        with open(path, 'w') as f:
            self._write(f, '!h', self._KRB_KEYTAB_MAGIC)
            for k in self.entries:
                self._write_entry(f, k)
        self.filename = path
        return self

    def get_kvno(self, principal):
        """Find the largest kvno for the given principal.

        None is returned if no matches are found."""
        kvno = None
        for e in self.entries:
            if e['principal'] == principal:
                if e['kvno'] > kvno:
                    kvno = e['kvno']
        return kvno

    def get_entries(self, principal, kvno=None):
        """Return the list of entries for the given principal and kvno.

        If knvo is not given, then the entries with the largest kvno are
        returned. None is returned if no matches are found."""
        if kvno is None:
            kvno = self.get_kvno(principal)
            if kvno is None:
                return None
        entries = []
        for e in self.entries:
            if e['principal'] == principal and e['kvno'] == kvno:
                entries.append(e)
        return entries

    def is_des(self, principal, kvno=None):
        """Returns true if a DES enctype is present for the given principal.

        Raises an exception if no keys are found for the given principal
        or if a mix of DES and non-DES kes are present."""
        has_des = False
        has_non_des = False
        entries = self.get_entries(principal, kvno)
        if entries is None:
            raise AssertionError("No keytab entries found for %s!" % (principal))
        for e in entries:
            if _is_des_eno(e['eno']):
                has_des = True
            else:
                has_non_des = True
        # Do not allow a mix of des and non-des keys!
        if has_des and has_non_des:
            raise AssertionError("DES and non-DES entries found for %s!" % (principal))
        return has_des

    def service_principals(self):
        """Return the list of afs service principals in this keytab.

        Only modern service principal formats are supported, that is
        the service principals must be in the form afs/<cellname>@<REALMNAME>."""
        sp = set()
        for e in self.entries:
            if e['principal'].startswith("afs/"):
                sp.add(e['principal'])
        return list(sp)

    def _guess_key_format(self, principal):
        """Attempt to detect the key file format for this keytab on this server.

        Returns one of: 'transarc', 'rxkad-k5', or 'extended'.  'rxkad-k5' is
        assumed if the key is not DES and asetkey does not support the extended
        key file format."""
        logger.info("Attempting to detect key format.")
        if self.is_des(principal):
            kformat = 'transarc'
        elif _check_for_extended_keyfile_support():
            kformat = 'extended'
        else:
            # Assume rxkad-k5 is supported for this non-DES service key.
            kformat = 'rxkad-k5'
        logger.info("Detected key format is '%s'." % (kformat))
        return kformat

    def _set_service_key_transarc(self, principal):
        """Set the DES service key."""
        keytab = self.filename
        kvno = "%d" % self.get_kvno(principal)
        asetkey('add', kvno, keytab, principal)

    def _set_service_key_rxkad_k5(self, confdir, principal):
        """Set the non-DES service key for rxkad-k5 support."""
        # Verify this keytab does not contain a DES key for the principal.
        if self.is_des(principal):
            raise AssertionError("Cannot use DES key for rxkad-k5!")
        if not os.path.isdir(confdir):
            raise ValueError("Cannot find server config directory '%s'." % (confdir))
        confdir = os.path.abspath(confdir)
        src = self.filename
        dst = os.path.join(confdir, 'rxkad.keytab')
        if os.path.exists(dst):
            logger.info("Removing old rxkad-k5 file: %s" % (dst))
            os.remove(dst)
        logger.info("Copying rxkad-k5 keytab %s to %s.", src, dst)
        shutil.copyfile(src, dst)
        os.chmod(dst, 0600)

    def _set_service_key_extended(self, principal):
        """Set the non-DES service key."""
        keytab = self.filename
        for e in self.get_entries(principal):
            kvno = "%d" % e['kvno']
            eno = "%d" % e['eno']
            asetkey('add', 'rxkad_krb5', kvno, eno, keytab, principal)

    def _get_service_principal(self, cell, realm):
        if cell is not None:
            if realm is None:
                realm = cell.upper()
            principal = "afs/%s@%s" % (cell, realm)
        else:
            sp = self.service_principals()
            if len(sp) == 1:
                principal = sp[0]
            elif len(sp) == 0:
                raise AssertionError("The keytab '%s' does not contain any afs service principals." % (self.filename))
            elif len(sp) > 1:
                raise AssertionError("The keytab '%s' has more than one afs service principal; "
                                     "Specify which cell and realm should be used." % (self.filename))
            else:
                raise AssertionError("Internal error")
        return principal

    def set_service_key(self, cell, realm, kformat, confdir, dryrun=False, **kwargs):
        """Set the service key given in a keytab file."""
        if self.filename is None:
            raise AssertionError("Must read or write keytab file first.""")

        principal = self._get_service_principal(cell, realm)
        logger.debug("Using service principal '%s'.", principal)
        kvno = self.get_kvno(principal)
        if kvno is None:
            raise ValueError("Principal '%s' not found in keytab %s" % (principal, self.filename))
        enctypes = [e['enctype'] for e in self.get_entries(principal)]

        if not kformat:
            kformat = 'detect'
        if kformat == 'detect':
            kformat = self._guess_key_format(principal)

        if not dryrun:
            msg = "Setting key"
        else:
            msg = "Skipping set key for dryrun"
        logger.info("%s; keytab '%s', principal '%s', kvno '%s', enctypes '%s', format '%s'",
                    msg, self.filename, principal, kvno, ", ".join(enctypes), kformat)

        if kformat == 'transarc':
            if not dryrun:
                self._set_service_key_transarc(principal)
        elif kformat == 'rxkad-k5':
            if not dryrun:
                self._set_service_key_rxkad_k5(confdir, principal)
        elif kformat == 'extended':
            if not dryrun:
                self._set_service_key_extended(principal)
        else:
            raise ValueError("Unknown key file format name: %s" % (kformat))

    def akimpersonate(self, user=None, cell=None, realm=None, **kwargs):
        if self.filename is None:
            raise AssertionError("Must read or write keytab file first.")
        if user is None:
            user = DEFAULT_USER
        user = user.replace('.', '/')  # convert k4-style separators (used by afs) to k5-style
        sp = self._get_service_principal(cell, realm) # lookup the cell/realm if needed
        if self.get_kvno(sp) is None:
            raise AssertionError("No service principal found!")
        cell,realm = sp.replace('afs/', '').split('@')
        principal = "%s@%s" % (user, realm)

        output = aklog('-d', '-c', cell, '-k', realm, '-principal', principal, '-keytab', self.filename)
        for line in output.splitlines():
            logger.info(line)

def create(cell='robotest', realm=None, keytab='/tmp/afs.keytab',
           enctype=None, secret=None, **kwargs):
    """Create a fake keytab file.

    cell: afs cell name
    realm: kerberos realm name
    keytab: destination file path
    enctype: encyption type
    secret: key data
    """
    if realm is None:
        realm = cell.upper()
    principal = "afs/{0}@{1}".format(cell, realm)
    k = Keytab()
    k.add_fake_key(principal, enctype=enctype, secret=secret)
    k.write(keytab)

def destroy(keytab='/tmp/afs.keytab', force=False, **kwargs):
    """Remove a keytab file.

    keytab: path of the keytab file to be removed
    force:  delete even if the file is not a valid keytab
    """
    try:
        k = Keytab().load(keytab)
        logger.debug("removing keytab file %s", k.filename)
        os.remove(k.filename)
    except NotFoundKeytab:
        logger.debug("keytab not found %s", keytab)
    except InvalidKeytab:
        if not force:
            logger.info("skipping removal of non-keytab file %s", keytab)
        else:
            logger.debug("removing invalid keytab file %s (forced)", keytab)
            os.remove(keytab)

def setkey(keytab='/tmp/afs.keytab', cell=None, realm=None,
        kformat=None, confdir=AFS_CONF_DIR, **kwargs):
    """Set a service key from a keytab file.

    keytab: path of the keytab file
    cell: cellname
    realm: kerberos realm name
    kformat: keyfile format
    confdir: server config file path
    """
    k = Keytab.load(keytab)
    k.set_service_key(cell, realm, kformat, confdir, **kwargs)
