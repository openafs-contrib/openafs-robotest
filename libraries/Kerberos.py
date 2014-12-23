# Copyright (c) 2014, Sine Nomine Associates
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
from struct import pack
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn

_KRB_KEYTAB_MAGIC = 0x0502

# IANA Kerberos Encryption Type Numbers
_KRB_ENCTYPE_NUMBERS = {
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


class Kerberos:
    """Keywords for reading Kerberos keytabs."""

    def __init__(self):
        self._settings = None

    def _set_settings(self, _settings):
        """Settings to be used when running outside of RF.

        The _settings dictionary is provided by the interactive setup tool
        so this class can be used outside of the robotframework.
        """
        self._settings = _settings

    def _set_logger(self, _logger):
        """Logger to be used when running outside of RF."""
        global logger
        logger = _logger

    def _get_setting_value(self, name):
        """Get a setting value."""
        if self._settings and name in self._settings:
            value = self._settings[name]
        else:
            value = BuiltIn().get_variable_value("${%s}" % (name))
        if value is None or value == "":
            raise AssertionError("%s not set." % (name))
        return value

    def _get_keytab_keys(self, keytab):
        """Read the list of (kvno,principal,enctype) tuples from a keytab."""
        entries = []
        klist = self._get_setting_value('KLIST')
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
            fields = [x.strip() for x in line.split()]
            kvno = int(fields[0])
            if len(fields) == 5:  # newer versions of klist emit a timestamp
               principal = fields[3]
               enctype = fields[4].strip('(').strip(')')
            elif len(fields) == 3:
               principal = fields[1]
               enctype = fields[3].strip('(').strip(')')
            else:
               raise AssertionError("Unexpected number of fields: %s" % (line))
            entries.append({'kvno':kvno, 'principal':principal, 'enctype':enctype})
        rc = pipe.close()
        if rc:
            raise AssertionError("klist failed: exit code=%d" % (rc))
        return entries

    def _get_principal_keys(self, principal):
        keys = []
        kadmin = self._get_setting_value('KADMIN_LOCAL')
        if "'" in principal:
            raise AssertionError("Invalid principal string: %s" % (principal))
        command = "sudo -n %s -q 'get_principal %s'" % (kadmin, principal)
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

    def get_encryption_types(self):
        return _KRB_ENCTYPE_NUMBERS.keys()

    def add_principal(self, principal):
        kadmin = self._get_setting_value('KADMIN_LOCAL')
        if "'" in principal:
            raise AssertionError("Invalid principal string: %s" % (principal))
        command = "sudo -n %s -q 'add_principal -randkey %s'" % (kadmin, principal)
        logger.info("Running: %s" % command)
        pipe = os.popen(command)
        for line in pipe.readlines():
            logger.info(line.rstrip())
        rc = pipe.close()
        if rc:
            raise AssertionError("kadmin.local failed: exit code=%d" % (rc))

    def get_key_version_number(self, keytab, cell, realm, enctype="des-cbc-crc"):
        """Get the kvno of an AFS service key.

        Returns the kvno of the AFS service key for the given cell, realm and
        enctype pattern. The largest kvno is returned if more than one key matches.
        """
        logger.info("Searching for afs/%s@%s (or afs@%s) with enctype %s in %s" % \
            (cell, realm, realm, enctype, keytab))
        p = re.compile(r'afs(/%s)?@%s$' % (cell, realm))
        e = re.compile(r'%s$' % (enctype))
        kvnos = [k['kvno'] for k in self._get_keytab_keys(keytab) if p.match(k['principal']) and e.match(k['enctype'])]
        if len(kvnos) == 0:
            raise AssertionError("Failed to find a kvno in keytab '%s'." % (keytab))
        kvno = sorted(kvnos, reverse=True)[0]
        return kvno

    def get_encryption_type_number(self, enctype):
        """Get the enctype number of an enctype string."""
        if not enctype in _KRB_ENCTYPE_NUMBERS:
            raise AssertionError("Unknown enctype: %s" % (enctype))
        return _KRB_ENCTYPE_NUMBERS[enctype]

    def encryption_type_is_des(self, enctype):
        """Returns true if the enctype uses the single DES cipher."""
        eno = self.get_encryption_type_number(enctype)
        return (eno in [1, 2, 3, 15])

    def _create_empty_keytab(self, keytab):
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
        f.write(pack('!h', _KRB_KEYTAB_MAGIC))  # requried by kadmin
        f.close()

    def add_entry_to_keytab(self, keytab, principal, enctype=None, salt='normal'):
        """Write an entry to a keytab."""
        if principal and "'" in principal:
            raise AssertionError("Invalid principal string: %s" % (principal))
        if enctype and "'" in enctype:
            raise AssertionError("Invalid enctype string: %s" % (enctype))
        if salt and "'" in salt:
            raise AssertionError("Invalid salt string: %s" % (salt))

        kadmin = self._get_setting_value('KADMIN_LOCAL')
        if enctype:
            query = "ktadd -k %s -e %s:%s %s" % (keytab, enctype, salt, principal)
        else:
            query = "ktadd -k %s %s" % (keytab, principal)
        command = "sudo -n %s -q '%s'" % (kadmin, query)
        logger.info("Running: %s " % (command))
        pipe = os.popen(command)
        for line in pipe.readlines():
            logger.info(line.rstrip())
        rc = pipe.close()
        if rc:
            raise AssertionError("kadmin.local failed: exit code=%d" % (rc))

    def create_afs_service_keytab(self, keytab, cell, realm, enctype):
        """Create the AFS service key and write it to a keytab.

        Create the afs service key using kadmin.local if it does not
        exist and write the key to a keytab if the key version number is
        not already in the keytab.
        """
        principal = "afs/%s@%s" % (cell, realm)
        if self.encryption_type_is_des(enctype):
            salt = 'afs3'
        else:
            salt = 'normal'
        # Create the key, if needed
        keys = self._get_principal_keys(principal)
        if not keys:
            self.add_principal(principal)
            keys = self._get_principal_keys(principal)
        kvno = [k['kvno'] for k in keys][0]
        # Create an empty keytab, if none. Otherwise get the service key kvno
        # in the existing keytab.
        if not os.path.isfile(keytab):
            self._create_empty_keytab(keytab)
        try:
            in_keytab = self.get_key_version_number(keytab, cell, realm, enctype=enctype)
        except:
            in_keytab = None
        # Write the service key, if not already in the keytab.
        if kvno != in_keytab:
            self.add_entry_to_keytab(keytab, principal, enctype=enctype, salt=salt)


    def create_keytab(self, keytab, principal, realm):
        """Create test user keys and write them to a keytab.

        Create the test user key using kadmin.local if it does not exist
        and write the key to a keytab if the key version number is not already
        in the keytab.
        """
        principal = "%s@%s" % (principal.replace(".", "/"), realm)
        # Create the key, if needed
        keys = self._get_principal_keys(principal)
        if not keys:
            self.add_principal(principal)
            keys = self._get_principal_keys(principal)
        kvno = [k['kvno'] for k in keys][0]
        # Create an emtpy keytab owned by the current uid, if the keytab does not
        # already exist. See if the kvno is already in the keytab.
        if not os.path.isfile(keytab):
            self._create_empty_keytab(keytab)
        try:
            keys = self._get_keytab_keys(keytab)
            kvnos = [k['kvno'] for k in keys if k['principal']==principal]
        except:
            kvnos = []
        # Write the service key, if not already in the keytab.
        if not kvnos:
            self.add_entry_to_keytab(keytab, principal)
        else:
            # Avoid old kvnos in the keytab.
            old = [k for k in kvnos if k!=kvno]
            if old:
                raise AssertionError("Old kvnos for principal '%s' in keytab '%s'!" % (principal, keytab))

