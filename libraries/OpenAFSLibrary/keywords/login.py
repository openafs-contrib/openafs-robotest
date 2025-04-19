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

import os
from robot.api import logger

from OpenAFSLibrary.variable import get_var, get_bool
from OpenAFSLibrary.command import run_program


def get_principal(user, realm):
    """Convert OpenAFS k4 style names to k5 style principals."""
    return "%s@%s" %  (user.replace('.', '/'), realm)

def akimpersonate(user):
    """Acquire an AFS token for authenticated access without Kerberos."""
    if not user:
        raise AssertionError("User name is required")
    aklog = get_var('AKLOG')
    cell = get_var('AFS_CELL')
    realm = get_var('KRB_REALM')
    keytab = get_var('KRB_AFS_KEYTAB')
    principal = get_principal(user, realm)
    cmd = "%s -d -c %s -k %s -keytab %s -principal %s" % (aklog, cell, realm, keytab, principal)
    rc,out,err = run_program(cmd)
    if rc:
        raise AssertionError("aklog failed: '%s'; exit code = %d" % (cmd, rc))

def login_with_password(user, password):
    """Acquire a Kerberos ticket and AFS token with a password."""
    if not user:
        raise AssertionError("user is required")
    if not password:
        raise AssertionError("password is required")
    klog_krb5 = get_var('KLOG_KRB5')
    cell = get_var('AFS_CELL')
    realm = get_var('KRB_REALM')
    cmd = "%s -principal %s -password %s -cell %s -k %s" % (klog_krb5, user, password, cell, realm)
    rc,out,err = run_program(cmd)
    if rc:
        raise AssertionError("klog.krb5 failed: '%s'; exit code = %d" % (cmd, rc))

def login_with_keytab(user, keytab):
    """Acquire an AFS token for authenticated access with Kerberos."""
    if not user:
        raise ValueError("User name is required.")
    if not keytab:
        raise ValueError("keytab is required.")
    kinit = get_var('KINIT')
    aklog = get_var('AKLOG')
    cell = get_var('AFS_CELL')
    realm = get_var('KRB_REALM')
    principal = get_principal(user, realm)
    logger.info("keytab: " + keytab)
    if not os.path.exists(keytab):
        raise AssertionError("Keytab file '%s' is missing." % keytab)
    cmd = "%s -k -t %s %s" % (kinit, keytab, principal)
    rc,out,err = run_program(cmd)
    if rc:
        raise AssertionError("kinit failed: '%s'; exit code = %d" % (cmd, rc))
    cmd = "%s -d -c %s -k %s" % (aklog, cell, realm)
    rc,out,err = run_program(cmd)
    if rc:
        raise AssertionError("kinit failed: '%s'; exit code = %d" % (cmd, rc))

class _LoginKeywords(object):

    def login(self, user, password=None, keytab=None):
        """Acquire an AFS token for authenticated access."""
        if get_bool('AFS_AKIMPERSONATE'):
            akimpersonate(user)
        elif password:
            login_with_password(user, password)
        elif keytab:
            login_with_keytab(user, keytab)
        else:
            raise ValueError("password or keytab is required")

    def logout(self):
        """Release the AFS token."""
        if not get_bool('AFS_AKIMPERSONATE'):
            kdestroy = get_var('KDESTROY')
            krb5cc = "/tmp/afsrobot.krb5cc"
            cmd = "KRB5CCNAME=%s %s" % (krb5cc, kdestroy)
            rc,out,err = run_program(cmd)
            if rc:
                raise AssertionError("kdestroy failed: '%s'; exit code = %d" % (cmd, rc))
        unlog = get_var('UNLOG')
        rc,out,err = run_program(unlog)
        if rc:
            raise AssertionError("unlog failed: '%s'; exit code = %d" % (unlog, rc))
