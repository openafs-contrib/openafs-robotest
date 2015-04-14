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

import os
import re
import sys
import time
from struct import pack,calcsize
from robot.api import logger
from OpenAFSLibrary.util import get_var

KRB_KEYTAB_MAGIC = 0x0502
KRB_NT_PRINCIPAL = 1

# IANA Kerberos Encryption Type Numbers
KRB_ENCTYPE_NUMBERS = {
    'des-cbc-crc': 1,
    'des-cbc-md4': 2,
    'des-cbc-md5': 3,
    'des3-cbc-md5': 5,
    'des3-cbc-sha1': 7,
    'dsaWithSHA1-CmsOID': 9,
    'md5WithRSAEncryption-CmsOID': 10,
    'sha1WithRSAEncryption-CmsOID': 11,
    'rc2CBC-EnvOID': 12,
    'rsaEncryption-EnvOID': 13,
    'rsaES-OAEP-ENV-OID': 14,
    'des-ede3-cbc-Env-OID': 15,
    'des3-cbc-sha1-kd': 16,
    'aes128-cts-hmac-sha1-96': 17, # common
    'aes256-cts-hmac-sha1-96': 18, # common
    'rc4-hmac': 23,
    'rc4-hmac-exp': 24,
    'camellia128-cts-cmac': 25,
    'camellia256-cts-cmac': 26,
    'subkey-keymaterial': 65,
}

KRB_ENCTYPE_DESCS = {
    'aes128-cts-hmac-sha1-96': "AES-128 CTS mode with 96-bit SHA-1 HMAC",
    'aes256-cts-hmac-sha1-96': "AES-256 CTS mode with 96-bit SHA-1 HMAC",
    'arcfour-hmac': "ArcFour with HMAC/md5" ,
    'des3-cbc-sha1': "Triple DES cbc mode with HMAC/sha1",
    'des-cbc-crc': "DES cbc mode with CRC-32",
}

def encryption_type_number(enctype):
    """Get the enctype number of an enctype string."""
    if not enctype in KRB_ENCTYPE_NUMBERS:
        raise AssertionError("Unknown enctype: %s" % (enctype))
    return KRB_ENCTYPE_NUMBERS[enctype]

def encryption_type_is_des(self, enctype):
    """Returns true if the enctype uses the single DES cipher."""
    eno = encryption_type_number(enctype)
    return (eno in [1, 2, 3, 15])

def normalize_enctype(enctype):
    if enctype in KRB_ENCTYPE_NUMBERS:
        return enctype
    for k in KRB_ENCTYPE_DESCS:
        if enctype == KRB_ENCTYPE_DESCS[k]:
            return k
    raise AssertionError("Invalid enctype string: %s" % (enctype))

def get_keytab_keys(keytab):
    """Read the list of (kvno,principal,enctype) tuples from a keytab."""
    klist = get_var('KLIST')
    entries = []
    command = "%s -e -k -t %s" % (klist, keytab)
    logger.info("Running: %s " % (command))
    pipe = os.popen(command)
    for line in pipe.readlines():
        logger.info(line.rstrip())
        if line.startswith('Keytab name:'):
            continue
        if line.startswith('KVNO'):
            continue
        if line.startswith('----'):
            continue
        m = re.match(r'^\s*(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+\((.+)\)', line)
        if m:
            kvno = int(m.group(1))
            principal = m.group(4)
            enctype = normalize_enctype(m.group(5))
        else:
           raise AssertionError("Unexpected klist line: %s" % (line))
        entries.append({'kvno':kvno, 'principal':principal, 'enctype':enctype})
    rc = pipe.close()
    if rc:
        raise AssertionError("klist failed: exit code=%d" % (rc))
    return entries

def get_principal_keys(principal):
    kadmin_local = get_var('KADMIN_LOCAL')
    keys = []
    if "'" in principal:
        raise AssertionError("Invalid principal string: %s" % (principal))
    command = "sudo -n %s -q 'get_principal %s'" % (kadmin_local, principal)
    logger.info("Running: %s" % command)
    pipe = os.popen(command)
    for line in pipe.readlines():
        logger.info(line.rstrip())
        if line.startswith("Key:"):
            k = [x.strip() for x in line.replace("Key:", "", 1).split(',')]
            kvno = int(k[0].strip('vno '))
            enctype = k[1]
            salt = k[2]
            if salt == 'no salt':
                salt = 'normal'
            keys.append({'kvno':kvno, 'enctype':enctype, 'salt':salt, 'principal':principal})
    rc = pipe.close()
    if rc:
        raise AssertionError("kadmin.local failed: exit code=%d" % (rc))
    return keys

def get_key_version_number(keytab, cell, realm, enctype="des-cbc-crc"):
    """Get the kvno of the AFS service key.

    Returns the kvno of the AFS service key for the given cell, realm and
    enctype pattern. The largest kvno is returned if more than one key matches.
    """
    logger.info("Searching for afs/%s@%s (or afs@%s) with enctype %s in %s" % \
        (cell, realm, realm, enctype, keytab))
    p = re.compile(r'afs(/%s)?@%s$' % (cell, realm))
    e = re.compile(r'%s$' % (enctype))
    kvnos = [k['kvno'] for k in get_keytab_keys(keytab) if p.match(k['principal']) and e.match(k['enctype'])]
    if len(kvnos) == 0:
        raise AssertionError("Failed to find a kvno in keytab '%s'." % (keytab))
    kvno = sorted(kvnos, reverse=True)[0]
    return kvno

def add_principal(principal):
    """Add a principal to the Kerberos realm."""
    kadmin_local = get_var('KADMIN_LOCAL')
    if "'" in principal:
        raise AssertionError("Invalid principal string: %s" % (principal))
    command = "sudo -n %s -q 'add_principal -randkey %s'" % (kadmin_local, principal)
    logger.info("Running: %s" % command)
    pipe = os.popen(command)
    for line in pipe.readlines():
        logger.info(line.rstrip())
    rc = pipe.close()
    if rc:
        raise AssertionError("kadmin.local failed: exit code=%d" % (rc))

def add_entry_to_keytab(keytab, principal, enctype=None, salt='normal'):
    """Write an entry to a keytab."""
    kadmin_local = get_var('KADMIN_LOCAL')
    if principal and "'" in principal:
        raise AssertionError("Invalid principal string: %s" % (principal))
    if enctype and "'" in enctype:
        raise AssertionError("Invalid enctype string: %s" % (enctype))
    if salt and "'" in salt:
        raise AssertionError("Invalid salt string: %s" % (salt))

    if enctype:
        query = "ktadd -k %s -e %s:%s %s" % (keytab, enctype, salt, principal)
    else:
        query = "ktadd -k %s %s" % (keytab, principal)
    command = "sudo -n %s -q '%s'" % (kadmin_local, query)
    logger.info("Running: %s " % (command))
    pipe = os.popen(command)
    for line in pipe.readlines():
        logger.info(line.rstrip())
    rc = pipe.close()
    if rc:
        raise AssertionError("kadmin.local failed: exit code=%d" % (rc))

def generate_des_key():
    """Generate a random DES key with correct parity bits."""
    keybytes = bytearray(os.urandom(8))
    key = bytearray(0)
    for i in keybytes:
        b = bin(i & 0xfe)
        nb = len(b.split('1'))
        # nb is one more than the number of bits set
        key.append(int(b, 2) + (nb % 2))
    return bytes(key)

def create_empty_keytab(keytab):
    """Create an emtpy keytab file.

    If the keytab is created by kadmin.local (under sudo), it will be
    owned by root and not readable by the test user.  Instead of trying
    to steal ownship after the file is created, create an empty keytab
    file owned by the non-root user and have kadmin write the keys to
    the empty file.

    kadmin will not write to the keytab file unless it begins with a
    magic file format number, so put that at the beginning of the new file.
    """
    if not os.path.exists(os.path.dirname(keytab)):
        os.makedirs(os.path.dirname(keytab))
    f = open(keytab, 'wb')
    f.write(pack('!h', KRB_KEYTAB_MAGIC))  # requried by kadmin
    f.close()

def create_afs_service_keytab(self, keytab, cell, realm, enctype):
    """Create the AFS service key and write it to a keytab.

    Create the afs service key using kadmin.local if it does not
    exist and write the key to a keytab if the key version number is
    not already in the keytab.
    """
    principal = "afs/%s@%s" % (cell, realm)
    if encryption_type_is_des(enctype):
        salt = 'afs3'
    else:
        salt = 'normal'
    # Create the key, if needed
    keys = get_principal_keys(principal)
    if not keys:
        add_principal(principal)
        keys = get_principal_keys(principal)
    kvno = [k['kvno'] for k in keys][0]
    # Create an empty keytab, if none. Otherwise get the service key kvno
    # in the existing keytab.
    if not os.path.isfile(keytab):
        create_empty_keytab(keytab)
    try:
        in_keytab = get_key_version_number(keytab, cell, realm, enctype=enctype)
    except:
        in_keytab = None
    # Write the service key, if not already in the keytab.
    if kvno != in_keytab:
        add_entry_to_keytab(keytab, principal, enctype=enctype, salt=salt)

def create_fake_keytab(self, keytab, cell, realm, enctype):
    """Create a test keytab file for akimpersonate.

    This is intended testing OpenAFS without requiring an external kerberos
    server. A dummy service key is created randomly and saved in the MIT krb5
    keytab format. The key is not cryptographically strong; only use this
    for test systems.
    """
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
    num_components = 2
    name_type = KRB_NT_PRINCIPAL
    timestamp = int(time.time())
    vno = 1
    eno = encryption_type_number(enctype)
    if eno in (1, 2, 3):
        key = generate_des_key()
    elif eno == 17:
        key = os.urandom(16)
    elif eno == 18:
        key = os.urandom(32)
    else:
        AssertionError("Cannot create fake keytab for enctype %s" % (enctype))
    fmt = "HH%dsH%dsH%dsLLBHH%ds" % (len(realm), len("afs"), len(cell), len(key))
    size = calcsize("!"+fmt) # get the entry size
    f = open(keytab, "w")
    f.write(pack('!h', KRB_KEYTAB_MAGIC))
    f.write(pack("!l"+fmt,
        size, num_components,
        len(realm), realm, len("afs"), "afs", len(cell), cell, name_type,
        timestamp, vno, eno, len(key), key))
    f.close()

class _KeytabKeywords(object):

    def get_encryption_types(self):
        """Return the list of encyption types."""
        return KRB_ENCTYPE_NUMBERS.keys()

    def get_key_version_number(self, keytab, cell, realm, enctype="des-cbc-crc"):
        """Get the kvno of the AFS service key.

        Returns the kvno of the AFS service key for the given cell, realm and
        enctype pattern. The largest kvno is returned if more than one key matches.
        """
        return get_key_version_number(keytab, cell, realm, enctype)

    def get_encryption_type_number(self, enctype):
        """Get the enctype number of an enctype string."""
        return encryption_type_number(enctype)

    def create_user_keytab(self, keytab, principal, realm):
        """Create test user keys and write them to a keytab.

        Create the test user key using kadmin.local if it does not exist
        and write the key to a keytab if the key version number is not already
        in the keytab.
        """
        principal = "%s@%s" % (principal.replace(".", "/"), realm)
        # Create the key, if needed
        keys = get_principal_keys(principal)
        if not keys:
            add_principal(principal)
            keys = get_principal_keys(principal)
        kvno = [k['kvno'] for k in keys][0]
        # Create an emtpy keytab owned by the current uid, if the keytab does not
        # already exist. See if the kvno is already in the keytab.
        if not os.path.isfile(keytab):
            create_empty_keytab(keytab)
        try:
            keys = get_keytab_keys(keytab)
            kvnos = [k['kvno'] for k in keys if k['principal']==principal]
        except:
            kvnos = []
        # Write the service key, if not already in the keytab.
        if not kvnos:
            add_entry_to_keytab(keytab, principal)
        else:
            # Avoid old kvnos in the keytab.
            old = [k for k in kvnos if k!=kvno]
            if old:
                raise AssertionError("Old kvnos for principal '%s' in keytab '%s'!" % (principal, keytab))

    def create_service_keytab(self, keytab, cell, realm, enctype=None, akimpersonate=True):
        """Create the AFS service key keytab."""
        if akimpersonate:
            create_fake_keytab(self, keytab, cell, realm, enctype)
        else:
            create_afs_service_keytab(self, keytab, cell, realm, enctype)

