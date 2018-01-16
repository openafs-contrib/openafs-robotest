# Copyright (c) 2017 Sine Nomine Associates
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
#-------------------------------------------------------------------------------
#
#   usage: python -m test.test_package -v
#          python -m test.test_package PackageTest.<method> -v
#

import unittest
import os
import sys
import shutil
import glob
import tempfile
import subprocess

from afsutil.package import RpmBuilder
from afsutil.package import MockRpmBuilder

#REPO = os.path.expanduser("~/src/openafs")
REPO = "https://github.com/openafs/openafs.git"
TAG = "openafs-stable-1_6_20"
SRCDIR = tempfile.mkdtemp()

# Test mode
SKIP_BUILDS = True
SKIP_TEARDOWN = False

def readfile(path):
    with open(path, 'r') as f:
        return f.read()

def writefile(path, contents):
    with open(path, 'w') as f:
        f.write(contents)

def setup_srcdir():
    """Clone the source tree."""
    script = """
        mkdir -p {srcdir}
        cd {srcdir}
        git init
        git remote add origin {repo}
        git fetch origin
        git checkout {tag}""".\
        format(srcdir=SRCDIR, repo=REPO, tag=TAG)
    rc = os.system("/bin/bash -x -e -c '{script}'".format(script=script))
    if rc != 0:
        shutil.rmtree(SRCDIR)
        raise Exception("Unable to create srcdir.")

def kdevel():
    """Get list of installed kernel-devel packages."""
    return subprocess.check_output([
        "rpm", "-q", "-a", "kernel-devel"]).splitlines()

class PackageTest(unittest.TestCase):

    srcdir = SRCDIR
    topdir = None
    dstdir = None

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    @classmethod
    def setUpClass(cls):
        setup_srcdir()
        if not SKIP_BUILDS:
            sys.stdout.write("Note: These test will take a long, long time.\n")
            sys.stdout.write("      Set SKIP_BUILDS to True to skip long running tests.\n")

    @classmethod
    def tearDownClass(cls):
        if SKIP_TEARDOWN:
            sys.stdout.write("Warning: Teardown skipped; remove test dirs manually")
            return
        if os.path.isdir(SRCDIR):
             shutil.rmtree(SRCDIR)
        if cls.topdir is not None and os.path.isdir(cls.topdir):
            shutil.rmtree(cls.topdir)
        if cls.dstdir is not None and os.path.isdir(cls.dstdir):
            shutil.rmtree(cls.dstdir)

    def setUp(self):
        self.topdir = tempfile.mkdtemp()
        self.dstdir = tempfile.mkdtemp()

    def tearDown(self):
        if self.topdir is not None and os.path.isdir(self.topdir):
            shutil.rmtree(self.topdir)
        if self.dstdir is not None and os.path.isdir(self.dstdir):
            shutil.rmtree(self.dstdir)

    def assertExists(self, path):
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path),
            msg="path {0} does not exist".format(path))

    def assertNotExists(self, path):
        self.assertIsNotNone(path)
        self.assertFalse(os.path.exists(path),
            msg="path {0} exists".format(path))

    def assertGlobExists(self, g):
        files = glob.glob(g)
        self.assertTrue(len(files) > 0, msg="No files found for glob {0}".format(g))

    def test_01_get_package_version(self):
        testcases = [
            ('1.6.0', '1.6.0', '1'),
            ('1.6.0pre1', '1.6.0', '0.pre1'),
            ('1.8.0dev', '1.8.0', '0.dev'),
            ('1.6.20-32-gabcdef', '1.6.20', '32.gabcdef'),
            ('1.6.18.3-foo3', '1.6.18.3', '1.2.3.foo'),
        ]
        b = RpmBuilder()
        for tc in testcases:
            (v, r) = b.get_package_version(version=tc[0])
            self.assertEquals(v, tc[1])
            self.assertEquals(r, tc[2])

    def test_02_get_version(self):
        b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir)
        version = b.get_version()
        self.assertIsNotNone(version)
        self.assertRegexpMatches(version, r'^[1-9]\.[0-9]+\.[0-9]+.*')

    def test_03_get_version__from_dot_version(self):
        dot_version = os.path.join(self.srcdir, ".version")
        writefile(dot_version, "1.2.3")
        try:
            b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir)
            version = b.get_version()
            self.assertIsNotNone(version)
            self.assertEquals(version, "1.2.3")
        finally:
            os.remove(dot_version)

    def test_04_generate_spec(self):
        b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir)
        infile = "{srcdir}/src/packaging/RedHat/openafs.spec.in".format(srcdir=self.srcdir)
        spec = b.generate_spec(infile)
        self.assertEquals(spec, "{topdir}/SPECS/openafs.spec".format(topdir=self.topdir))
        self.assertExists("{topdir}/SPECS/openafs.spec".format(topdir=self.topdir))

    def test_05_copy_spec(self):
        spec = "/tmp/openafs.spec"
        writefile(spec, "example")
        try:
            b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir)
            b.copy_spec(spec)
            self.assertExists("{topdir}/SPECS/openafs.spec".format(topdir=self.topdir))
        finally:
            os.remove(spec)

    def test_06_prepare_spec(self):
        b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir)
        b.prepare_spec()
        self.assertExists("{topdir}/SPECS/openafs.spec".format(topdir=self.topdir))

    def test_07_prepare_spec__external_spec(self):
        spec = "/tmp/openafs.spec"
        writefile(spec, "example")
        try:
            b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir, spec=spec)
            b.prepare_spec()
            self.assertExists("{topdir}/SPECS/openafs.spec".format(topdir=self.topdir))
            contents = readfile("{topdir}/SPECS/openafs.spec".format(topdir=self.topdir))
            self.assertEquals(contents, "example")
        finally:
            os.remove(spec)

    def test_08_list_sources(self):
        b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir)
        s = b.list_sources()
        self.assertIsNotNone(s)

    def test_09_lookup_source(self):
        b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir)
        s = b.lookup_source('CellServDB')
        self.assertIsNotNone(s)

    def test_10_download_csdb(self):
        url = "https://www.central.org/dl/cellservdb/CellServDB.2016-01-01"
        b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir)
        b.download_csdb(url)
        self.assertExists("{topdir}/SOURCES/CellServDB.2016-01-01".format(topdir=self.topdir))

    def test_11_copy_csdb(self):
        csdb = "/tmp/CellServDB"
        writefile(csdb, "example")
        try:
            b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir)
            b.copy_csdb(csdb)
            self.assertExists("{topdir}/SOURCES/CellServDB".format(topdir=self.topdir))
        finally:
            os.remove(csdb)

    def test_12_prepare_sources_csdb(self):
        csdb = "/tmp/CellServDB"
        writefile(csdb, "example")
        try:
            b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir, csdb=csdb)
            b.prepare_sources_csdb()
            self.assertExists("{topdir}/SOURCES/CellServDB".format(topdir=self.topdir))
        finally:
            os.remove(csdb)

    def test_13_prepare_sources_relnotes(self):
        b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir)
        b.prepare_sources_relnotes()
        version = b.get_version()
        self.assertExists("{topdir}/SOURCES/RELNOTES-{version}".format(topdir=self.topdir,version=version))

    def test_14_prepare_sources_changelog(self):
        b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir)
        b.prepare_sources_changelog()
        self.assertExists("{topdir}/SOURCES/ChangeLog".format(topdir=self.topdir))

    def test_15_prepare_sources_scripts(self):
        b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir)
        b.prepare_sources_scripts()
        self.assertGlobExists("{topdir}/SOURCES/*".format(topdir=self.topdir))

    def test_16_prepare_sources_tarballs(self):
        b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir)
        b.prepare_sources_tarballs()
        self.assertGlobExists("{topdir}/SOURCES/*.tar.*".format(topdir=self.topdir))

    def test_17_prepare_sources(self):
        b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir, quiet=True)
        b.prepare_sources()
        self.assertGlobExists("{topdir}/SOURCES/*".format(topdir=self.topdir))

    def test_18_build_srpm(self):
        b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir, quiet=True)
        b.build_srpm()
        self.assertGlobExists("{topdir}/SRPMS/*".format(topdir=self.topdir))

    @unittest.skipIf(SKIP_BUILDS, "quick mode")
    def test_19_build_userspace(self):
        b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir, quiet=True)
        b.build_userspace()
        self.assertGlobExists("{topdir}/RPMS/*".format(topdir=self.topdir))

    @unittest.skipIf(SKIP_BUILDS, "quick mode")
    @unittest.skipUnless(len(kdevel()) > 0, "requires kernel-devel packages")
    def test_20_build_kmods(self):
        b = RpmBuilder(srcdir=self.srcdir, topdir=self.topdir, quiet=True)
        b.build_kmods()
        self.assertGlobExists("{topdir}/RPMS/*".format(topdir=self.topdir))

    @unittest.skipIf(SKIP_BUILDS, "quick mode")
    def test_21_build_userspace_with_mock(self):
        b = MockRpmBuilder(
                'epel-7-x86_64',
                srcdir=self.srcdir,
                dstdir=self.dstdir,
                autoclean=True, quiet=True)
        b.build_userspace()
        self.assertGlobExists("{dstdir}/openafs*.rpm".format(dstdir=self.dstdir))

    @unittest.skipIf(SKIP_BUILDS, "quick mode")
    def test_21_build_kmods_with_mock(self):
        b = MockRpmBuilder(
                'epel-7-x86_64',
                srcdir=self.srcdir,
                dstdir=self.dstdir,
                autoclean=True, quiet=True)
        b.build_kmods()
        self.assertGlobExists("{dstdir}/kmod-openafs*.rpm".format(dstdir=self.dstdir))

if __name__ == "__main__":
     unittest.main()

