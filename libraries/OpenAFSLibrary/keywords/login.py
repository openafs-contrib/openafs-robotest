# Copyright (c) 2014-2015, Sine Nomine Associates
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

from robot.api import logger
from OpenAFSLibrary.util import _get_var,_run_program

def _principal(user, realm):
    """Convert OpenAFS k4 style names to k5 style principals."""
    return "%s@%s" %  (user.replace('.', '/'), realm)

class _LoginKeywords(object):

    def login(self, user=None):
        if user is None:
            user = _get_var('AFS_ADMIN')
        if _get_var('AFS_AKIMPERSONATE'):
            self.akimpersonate(user)
        else:
            self.login_with_keytab(user)

    def logout(self):
        if not _get_var('AFS_AKIMPERSONATE'):
            site = _get_var('SITE')
            kdestroy = _get_var('KDESTROY')
            krb5cc = os.path.join(site, "krb5cc")
            cmd = "KRB5CCNAME=%s %s" % (krb5cc, kdestroy)
            rc,out,err = _run_program(cmd)
            if rc:
                raise AssertionError("kdestroy failed: '%s'; exit code = %d" % (cmd, rc))
        unlog = _get_var('UNLOG')
        rc,out,err = _run_program(unlog)
        if rc:
            raise AssertionError("unlog failed: '%s'; exit code = %d" % (unlog, rc))

    def akimpersonate(self, user):
        if not user:
            raise AsseritionError("User name is required")
        aklog = _get_var('AKLOG')
        cell = _get_var('AFS_CELL')
        realm = _get_var('KRB_REALM')
        keytab = _get_var('KRB_AFS_KEYTAB')
        principal = _principal(user, realm)
        cmd = "%s -d -c %s -k %s -keytab %s -principal %s" % (aklog, cell, realm, keytab, principal)
        rc,out,err = _run_program(cmd)
        if rc:
            raise AssertionError("aklog failed: '%s'; exit code = %d" % (cmd, rc))

    def login_with_keytab(self, user):
        if not user:
            raise AsseritionError("User name is required")
        site = _get_var('SITE')
        kinit = _get_var('KINIT')
        aklog = _get_var('AKLOG')
        cell = _get_var('AFS_CELL')
        realm = _get_var('KRB_REALM')
        principal = _principal(user, realm)
        if user == _get_var('AFS_USER'):
            keytab = _get_var('KRB_USER_KEYTAB')
        elif user == _get_var('AFS_ADMIN'):
            keytab = _get_var('KRB_ADMIN_KEYTAB')
        else:
            raise AssertionError("No keytab found for user '%s'." % user)
        if not keytab:
            raise AssertionError("Keytab not set for user '%s'." % user)
        logger.info("keytab: " + keytab)
        if not os.path.exists(keytab):
            raise AsseritionError("Keytab file '%s' is missing." % keytab)
        if not os.path.isdir(site):
            raise AsseritionError("SITE directory '%s' is missing." % site)
        krb5cc = os.path.join(site, "krb5cc")
        cmd = "KRB5CCNAME=%s %s -5 -k -t %s %s" % (krb5cc, kinit, keytab, principal)
        rc,out,err = _run_program(cmd)
        if rc:
            raise AssertionError("kinit failed: '%s'; exit code = %d" % (cmd, rc))
        cmd = "KRB5CCNAME=%s %s -d -c %s -k %s" % (krb5cc, aklog, cell, realm)
        rc,out,err = _run_program(cmd)
        if rc:
            raise AssertionError("kinit failed: '%s'; exit code = %d" % (cmd, rc))

