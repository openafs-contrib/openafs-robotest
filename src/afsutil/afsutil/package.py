# Copyright (c) 2014-2018 Sine Nomine Associates
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

"""Driver to build OpenAFS rpms from git sources

This module provides classes to build OpenAFS srpms, client and server
userspace rpms, and linux kernel module rpms. Mock may be used to build in a
chroot, which is the preferred method since build dependencies will be
contained to the temporary chroot.

The RpmBuilder searches for linux kernel-devel packages installed on the system
and will build an OpenAFS kmod package for each linux version found. Be sure
your system has a kernel-devel package installed and is up to date to build a
kmod for your running kernel version.

The MockRpmBuilder searches for linux kernel-devel packages available in the
chroot by querying all the enabled yum repos inside the chroot. The
MockRpmBuilder will build an OpenAFS kmod package for each available
kernel-devel package. The chroot can be configured to have private yum repos,
which can be used to provide a large number of kernel-devel versions.

Before building the rpms, clone the OpenAFS git repo and check out the tag to
be built. For example:

    $ cd $HOME
    $ git clone https://github.com/openafs/openafs.git
    $ cd openafs
    $ git checkout openafs-stable-1_6_20

Example usage:

    from os.path import expanduser
    from afsutil.package import RpmBuilder

    b = RpmBuilder(srcdir=expanduser("~/openafs"))
    b.prepare_sources()
    b.build_srpm()
    b.build_userspace()
    b.build_kmods()

"""

import os
import sys
import re
import urllib2
import logging
import shutil
import glob
from afsutil.system import sh, mkdirp, which
from afsutil.misc import flatten, trim

logger = logging.getLogger(__name__)

class RpmBuilderError(Exception):
    """Failed to build packages."""

def readfile(path):
    """Read a file into a string."""
    with open(path, 'r') as f:
        return f.read()

def writefile(path, contents):
    """Write string to a file."""
    with open(path, 'w') as f:
        f.write(contents)

class RpmBuilder(object):
    def __init__(self, srcdir=None, pkgdir=None, topdir=None, dstdir=None,
                 version=None, arch=None, spec=None, csdb=None, clobber=False, quiet=False,
                 with_=None, without=None, **kwargs):
        """Initialize the RpmBuilder object

        srcdir:  path of the checked out source tree (default: .)
        pkgdir:  path of the packaging files (default: {srcdir}/src/packaging/RedHat
        topdir:  path of the rpmbuild directories (default: {srcdir}/packaging/rpmbuild)
        dstdir:  path to place rpms (default: None)
        version: target version number (default: check)
        arch:    target architecture (default: check)
        spec:    custom rpmbuild specfile (default: {pkdir}/openafs.spec.in}
        clobber: build and overwrite existing kmod-openafs rpms
        quiet:   less output
        with_:   rpmbuild --with options
        without: rpmbuild --without options
        """
        if srcdir is None:
            srcdir = os.getcwd()
        if pkgdir is None:
            pkgdir = os.path.join(srcdir, "src/packaging/RedHat")
        if topdir is None:
            topdir = os.path.join(srcdir, "packages/rpmbuild")
        if arch is None:
            arch = os.uname()[4]
        if with_ is None:
            with_ = []
        if without is None:
            without = []
        # paths
        self.srcdir = srcdir
        self.pkgdir = pkgdir
        self.topdir = topdir
        self.dstdir = dstdir # may be None
        # options
        self.clobber = clobber
        self.quiet = quiet
        self.custom_spec = spec
        self.custom_csdb = csdb
        self.with_ = flatten(with_)
        self.without = flatten(without)
        # state
        self.version = version
        self.arch = arch
        self.spec = None
        self.csdb = None
        self.sources = {}
        self.srpm = None
        self.count = 0
        self.total = 0
        self.downloaded = []
        self.generated = []
        self.skipped = []
        self.built = []

    def withargs(self):
        """Return a list of optional --with and --without options."""
        args = []
        for with_ in self.with_:
            args.append('--with')
            args.append(with_)
        for without in self.without:
            args.append('--without')
            args.append(without)
        return args

    def rpmbuild(self, *args, **kwargs):
        """Run the rpmbuild commands."""
        return sh(
            'rpmbuild',
            '--define', '_topdir {0}'.format(self.topdir),
            *args, **kwargs)

    def git(self, *args):
        """Helper to run git commands in the source tree."""
        if not self.srcdir or self.srcdir == ".":
            gitdir = None
        else:
            gitdir = os.path.join(self.srcdir, ".git")
        args = list(args)
        args.insert(0, 'git')
        if gitdir:
            args.insert(1, "--git-dir")
            args.insert(2, gitdir)
        return sh(*args, quiet=True)

    def get_version(self):
        """Get the version identifier for the packaging.

        Use the verision given in the .version file if present. Otherwise
        try to use git to find the version number of the checked out tree.
        """
        if self.version:
            return self.version
        dot_version = os.path.join(self.srcdir, ".version")
        version = None
        if os.path.exists(dot_version):
            # Note: If the .version file exists, the value of the working file is
            # used when populating SOURCES, not the one extracted from git.
            logger.debug("getting OpenAFS version number from .version file.")
            version = readfile(dot_version).strip()
        else:
            logger.debug("getting OpenAFS version number with git describe.")
            output = self.git('describe', '--abbrev=4', 'HEAD')
            if output:
                version = output[0]
        if not version:
            raise RpmBuilderError("Failed to find version number.")
        self.version = re.sub(r'^openafs-[^-]*-', '', version).replace('_', '.')
        logger.info("OpenAFS version is {0}".format(self.version))
        return self.version

    def get_package_version(self, version=None):
        """Determine the packaging release info.

        The format of the linux packaging release and version strings depend on
        the type of release. The following variants are supported:

        * stardard release; 1.6.20 => 1.6.20, 1
        * prereleases; 1.6.20pre1 => 1.6.20, 0.pre1
        * development release; 1.8.0dev => 1.8.0, 0.dev
        * not tagged; e.g., 1.6.0-32-gabcdef => 1.6.0, .32.gabcdef
        """
        if version is None:
            version = self.get_version()
        m1 = re.match(r'(.*)(pre[0-9]+)', version) # prerelease
        m2 = re.match(r'(.*)dev', version) # development
        m3 = re.match(r'(.*)-([0-9]+)-(g[a-f0-9]+)$', version) # development
        m4 = re.match(r'(.*)-([a-z]+)([0-9]+)', version) # custom
        if m1:
            linux_pkgver = m1.group(1)
            linux_pkgrel = "0.{0}".format(m1.group(2))
        elif m2:
            linux_pkgver = m2.group(1);
            linux_pkgrel = "0.dev"
        elif m3:
            linux_pkgver = m3.group(1)
            linux_pkgrel = "{0}.{1}".format(m3.group(2),m3.group(3))
        elif m4:
            linux_pkgver = m4.group(1)
            linux_pkgrel = "1.2.{0}.{1}".format(m4.group(3), m4.group(2))
        else:
            linux_pkgver = version # standard release
            linux_pkgrel = "1"     # increment when repackaging this version
        logger.info("Linux version is {0}".format(linux_pkgver))
        logger.info("Linux release is {0}".format(linux_pkgrel))
        return (linux_pkgver, linux_pkgrel)

    def current_kversion(self):
        """Return the verision of the running kernel."""
        version = os.uname()[2]
        arch = os.uname()[4]
        return trim(version, '.'+arch)

    def find_kversions_available(self):
        """Find the linux kernel versions of the kernel-devel packages."""
        kversions = sh(
            'rpm', '-q', '-a',
            '--queryformat=%{VERSION}-%{RELEASE}\n', 'kernel-devel',
            quiet=True)
        logger.debug("Found kernel versions: {0}".format(", ".join(kversions)))
        return kversions

    def find_kversions_existing(self):
        """Find the linux kernel versions of the kmod rpms previously built.

        Find the linux kernel versions of the kmods which have been already
        built for this version of OpenAFS. This allows us to avoid rebuilding
        kmods for a given OpenAFS version when a new kernel-devel version
        becomes available.
        """
        if self.dstdir is None or not os.path.exists(self.dstdir):
            return []
        logger.info("Checking for existing kmods in {0}".format(self.dstdir))
        linux_pkgver,linux_pkgrel = self.get_package_version()
        logger.debug("linux_pkgver={0}, linux_pkgrel={1}".format(linux_pkgver,linux_pkgrel))
        def get_kversion(line):
            # Extract the linux kernel version from the rpm RELEASE tag.
            # e.g. 1.3.10.0_514.10.2.el7 => 3.10.0-514.10.2.el7
            v,r = line.split(' ', 2)
            prefix = linux_pkgrel + '.'
            if v == linux_pkgver and r.startswith(prefix):
                return r.replace(prefix, '', 1).replace('_', '-')
            return None
        kversions = sh(
            'rpm', '-q', '-p', '--queryformat=%{VERSION} %{RELEASE}\n',
            "{dstdir}/kmod-openafs*.rpm".format(dstdir=self.dstdir),
            sed=get_kversion)
        logger.debug("Found kmods: {0}".format(", ".join(kversions)))
        return kversions

    def find_kversions(self):
        logger.debug("clobber is {0}".format(self.clobber))
        available = self.find_kversions_available()
        if self.clobber:
            kversions = available
        else:
            # Remove the ones we have already done, if any.
            existing = self.find_kversions_existing()
            kversions = list(set(available).difference(set(existing)))
            skipping = list(set(available).intersection(set(existing)))
            self.banner([
                "Available linux kernel versions:", available,
                "Found kmods for versions:", existing,
                "Skipping kmod builds for versions:", skipping,
                "Building kmods for versions:", kversions,
            ])
        return kversions

    def generate_spec(self, src):
        """Helper to generate the openafs.spec file."""
        version = self.get_version()
        (linux_pkgver, linux_pkgrel) = self.get_package_version(version)
        dst = os.path.join(self.topdir, "SPECS", "openafs.spec")
        logger.info("Generating spec '{0}' from template '{1}'.".format(dst, src))
        mkdirp(os.path.dirname(dst))
        writefile(dst,
            readfile(src).\
               replace('@VERSION@', version).\
               replace('@LINUX_PKGVER@', linux_pkgver).\
               replace('@LINUX_PKGREL@', linux_pkgrel))
        self.generated.append(dst)
        return dst

    def copy_spec(self, src):
        """Helper to copy the spec file to the SPECS directory."""
        dst = os.path.join(self.topdir, "SPECS", "openafs.spec")
        logger.debug("Copying {0} to {1}".format(src, dst))
        mkdirp(os.path.dirname(dst))
        shutil.copy(src, dst)
        return dst

    def prepare_spec(self):
        """Copy the specfile to the SPECS directory.

        By default, generate the openafs.spec file from the openafs.spec.in
        template found in the packaging files directory in the source tree.
        Otherwise, copy the specfile given to the SPECS directory.

        """
        if self.spec:
            return # already have a specfile
        if self.custom_spec is None:
            spec = os.path.join(self.pkgdir, "openafs.spec.in")
        else:
            spec = self.custom_spec
        if spec.endswith(".in"):
            self.spec = self.generate_spec(spec)
        else:
            self.spec = self.copy_spec(spec)

    def list_sources(self, spec=None):
        """Helper to list the source tags in a specfile."""
        if spec is None:
            if self.spec is None:
                self.prepare_spec()
            spec = self.spec
        sources = []
        if spec is None:
            spec = os.path.join(self.topdir, "SPECS", "openafs.spec")
        for line in readfile(spec).splitlines():
            m = re.match(r'Source([0-9]*): (.*)', line)
            if m:
                n = m.group(1)
                v = m.group(2).replace('%{afsvers}', self.version)
                sources.append((n,v))
        return sources

    def lookup_source(self, pattern, spec=None):
        """Helper to find a source tag in the specfile."""
        for n,source in self.list_sources(spec=spec):
            if re.search(pattern, source):
                return (n,source)
        return (None, None)

    def download_csdb(self, url):
        """Helper to download the CellServDB file to SOURCES."""
        dst = os.path.join(self.topdir, 'SOURCES', os.path.basename(url))
        logger.info("Downloading CellServDB from '{0}' to {1}'".format(url, dst))
        src = urllib2.urlopen(url)
        mkdirp(os.path.dirname(dst))
        writefile(dst, src.read())
        self.downloaded.append(dst)
        return dst

    def copy_csdb(self, src):
        """Helper to copy the CellServDB file to SOURCES."""
        dst = os.path.join(self.topdir, 'SOURCES', os.path.basename(src))
        logger.info("Copying user supplied CellServDB '{0}' to '{1}'.".format(src, dst))
        mkdirp(os.path.dirname(dst))
        shutil.copy(src, dst)
        if self.spec:
            n,v = self.lookup_source('CellServDB')
            old = "Source{0}: {1}".format(n, v)
            new = "Source{0}: {1}".format(n, os.path.basename(src))
            logger.info("Updating spec {0} with new CellServDB name.".format(self.spec))
            writefile(self.spec, readfile(self.spec).replace(old, new))
        return dst

    def prepare_sources_csdb(self):
        """Set the CellServDB file to be packaged.

        Sets the CellServDB file to be packaged. This file will be copied to
        /usr/vice/etc/CellServDB.dist during packaging.  Call this function
        after prepare_spec() and before prepare_sources() to set a custom
        CellServDB file.
        """
        if self.csdb:
            return # already have the CellServDB
        if self.custom_csdb:
            self.csdb = self.copy_csdb(self.custom_csdb)
        else:
            n,url = self.lookup_source(r'^https?://.*CellServDB')
            if url:
                self.csdb = self.download_csdb(url)
            else:
                raise RpmBuilderError("CellServDB url not found in spec file.""")

    def prepare_sources_relnotes(self):
        """Create the release notes to be packaged.

        Extract the changes for this version from the running NEWS file in the
        source tree.
        """
        if 'relnotes' in self.sources:
            return # already have release notes
        version = self.get_version()
        infile = os.path.join(self.srcdir, "NEWS")
        outfile = os.path.join(self.topdir, "SOURCES", "RELNOTES-{0}".format(version))
        news = readfile(infile).splitlines()
        try:
            i = news.index("OpenAFS {0}".format(version))
        except ValueError:
            # NEWS not updated for this release? Provide a file
            # to keep rpmbuild happy since this is a required SOURCE.
            relnotes = []
        else:
            # Extact the news items for just this release.
            relnotes = news[0:i+1] # the preamble
            for line in news[i+1:]:
                if line.startswith("OpenAFS"):
                    break # start of next section
                relnotes.append(line)
        mkdirp(os.path.dirname(outfile))
        writefile(outfile, "\n".join(relnotes))
        self.generated.append(outfile)
        self.sources['relnotes'] = True

    def prepare_sources_changelog(self):
        """Generate the ChangeLog file from git log.

        Use the git log as the ChangeLog.
        """
        if 'changelog' in self.sources:
            return
        dst = "{topdir}/SOURCES/ChangeLog".format(topdir=self.topdir)
        mkdirp(os.path.dirname(dst))
        cmd = "git --git-dir={srcdir}/.git log > {dst}". format(srcdir=self.srcdir, dst=dst)
        logger.info("running {cmd}".format(cmd=cmd))
        os.system(cmd)
        self.generated.append(dst)
        self.sources['changelog'] = True

    def prepare_sources_scripts(self):
        """Copy packaging helper scripts to the SOURCES directory.

        Copy packaging scripts listed in the spec file from the source tree
        into the rpmbuild SOURCES directory.
        """
        if 'scripts' in self.sources:
            return
        if not os.path.isdir(self.pkgdir):
            raise RpmBuilderError("Path to packaging scripts not found: '{0}'.".format(self.pkgdir))
        for n,source in self.list_sources():
            src = os.path.join(self.pkgdir, os.path.basename(source))
            if os.path.isfile(src):
                dst = os.path.join(self.topdir, "SOURCES", os.path.basename(source))
                logger.debug("Copying file '{0}' to '{1}'.".format(src, dst))
                mkdirp(os.path.dirname(dst))
                shutil.copy(src, dst)
                if dst.endswith(".sh"):
                    os.chmod(dst, 0755)
        self.sources['scripts'] = True

    def prepare_sources_tarballs(self):
        """Create the source and doc tarballs from git sources.

        Extract the source tree from the git repo and create the src and doc
        tarball files. The tarballs will be placed into the rpmbuild SOURCES
        directory.
        """
        if 'tarballs' in self.sources:
            return
        version = self.get_version()
        names = dict(
            version=version,
            topdir=self.topdir,
        )
        tarfile = "{topdir}/SOURCES/openafs-{version}.tar".format(**names)

        logger.info("Extracting source tree from git to {0}".format(os.path.dirname(tarfile)))
        mkdirp(os.path.dirname(tarfile))
        self.git('archive', '--format', 'tar',
                 '--prefix', 'openafs-{version}/'.format(**names),
                 '--output', tarfile,
                 'HEAD')
        sh('tar', 'xf', tarfile, '-C', os.path.dirname(tarfile), output=False)
        os.remove(tarfile)

        logger.info("Generating source tree and documents.")
        # Note: Overwrite the extracted version string, if one.
        writefile('{topdir}/SOURCES/openafs-{version}/.version'.format(**names), version)
        sh('/bin/sh', '-c',
            'cd {topdir}/SOURCES/openafs-{version} && ./regen.sh'.format(**names),
            output=False)

        logger.info("Creating doc tarball openafs-{version}-doc.tar.bz2".format(**names))
        sh('tar', 'cjf',
           '{topdir}/SOURCES/openafs-{version}-doc.tar.bz2'.format(**names),
           '-C', '{topdir}/SOURCES'.format(**names),
           'openafs-{version}/doc'.format(**names),
           output=False)
        self.generated.append('{topdir}/SOURCES/openafs-{version}-doc.tar.bz2'.format(**names))

        logger.info("Creating src tarball openafs-{version}-src.tar.bz2".format(**names))
        sh('tar', 'cjf',
           '{topdir}/SOURCES/openafs-{version}-src.tar.bz2'.format(**names),
           '-C', '{topdir}/SOURCES'.format(**names),
           '--exclude', 'doc',
           'openafs-{version}'.format(**names),
           output=False)
        self.generated.append('{topdir}/SOURCES/openafs-{version}-src.tar.bz2'.format(**names))
        # Clean up the temporary tree.
        shutil.rmtree('{topdir}/SOURCES/openafs-{version}'.format(**names))
        self.sources['tarballs'] = True

    def prepare_sources(self):
        """Prepare the rpmbuild SOURCES directory.

        arguments:
        spec: custom rpmbuild specfile
        csdb: custom CellServDB file to package
        """
        if 'all' in self.sources:
            return
        self.banner(["Preparing sources"])
        self.prepare_spec()
        self.prepare_sources_csdb()
        self.prepare_sources_relnotes()
        self.prepare_sources_changelog()
        self.prepare_sources_scripts()
        self.prepare_sources_tarballs()
        self.sources['all'] = True

    def build_srpm(self):
        """Build the source rpm.

        Run rpmbuild to build the source rpm from the source tarball and other
        files in SOURCES. The rpmbuild SOURCE and SPEC directories must be
        populated with the prepare_* functions before calling build_srpm.
        """
        self.prepare_spec()
        self.prepare_sources()
        self.banner(["Building srpm"])
        def name_written(line):
            m = re.match(r'Wrote: (.*\.src\.rpm)$', line)
            return m.group(1) if m else None
        args = self.withargs()
        args.append(self.spec)
        output = self.rpmbuild(
            '-bs', '--nodeps',
            '--define', 'build_userspace 1',
            '--define', 'build_modules 0',
            *args,
            sed=name_written)
        if len(output) < 1:
            raise RpmBuilderError("Failed to get srpm name.")
        self.srpm = output[0]
        self.built.append(self.srpm)
        logger.info("srpm is {0}".format(self.srpm))

    def build_userspace(self, srpm=None):
        """Build the userspace rpms.

        Run rpmbuild to build the userspace biniary rpms from the source rpm.

        srpm: path of the srpm. defaults to the srpm created by the
              previous build_srpm()
        """
        if srpm is None:
            if self.srpm is None:
                self.build_srpm()
            srpm = self.srpm

        self.banner(["Building rpms"])
        def get_wrote(line):
            m = re.match(r'Wrote: (.*\.rpm)$', line)
            return m.group(1) if m else None
        args = self.withargs()
        args.append(srpm)
        output = self.rpmbuild(
            '--rebuild', '-bb',
            '--target', self.arch,
            '--define', 'build_userspace 1',
            '--define', 'build_modules 0',
            *args,
            sed=get_wrote)
        self.built.extend(output)

    def build_kmod(self, srpm=None, kversion=None):
        """Build the a kmod rpm for the given kernel version.

        srpm:     path of the source rpm file
                  defaults to the srpm from the previous build_srpm()
        kversion: target linux kernel version, e.g., 3.10.0-514.16.1.el7
                  defaults to the currently running linux kernel version.

        A kernel-devel package for `kversion` must been installed to supply the
        required linux kernel header files.
        """
        if srpm is None:
            if self.srpm is None:
                self.build_srpm()
            srpm = self.srpm

        if kversion is None:
            kversion = self.current_kversion()

        info = ["Building module for {kversion}".format(kversion=kversion)]
        if self.count and self.total:
            info.append("Number {count} of {total}.".format(count=self.count, total=self.total))
        self.banner(info)

        logger.info("Building kmod for linux version {0}.".format(kversion))
        def name_written(line):
            m = re.match(r'Wrote: (.*\.rpm)$', line)
            return m.group(1) if m else None
        output = self.rpmbuild(
            '--rebuild', '-bb',
            '--target', self.arch,
            '--define', 'kernvers {0}'.format(kversion),
            '--define', 'build_userspace 0',
            '--define', 'build_modules 1',
            srpm,
            sed=name_written)
        self.built.extend(output)

    def build_kmods(self, srpm=None, kversions=None):
        """Build kmods for each kernel versions.

        srpm:      path of the source rpm file
                   defaults to the srpm from the previous build_srpm()
        kversions: list of target kernel versions
                   defaults to the list of versions of currently
                   installed kernel-devel packages.
        """
        if not kversions:
            kversions = self.find_kversions()
        self.banner(["Building modules for versions:", kversions])
        self.total = len(kversions)
        for i,kversion in enumerate(kversions):
            self.count = i + 1
            self.build_kmod(srpm=srpm, kversion=kversion)

    def createrepo(self):
        """Run createrepo in the destination directory."""
        if self.dstdir and os.path.exists(self.dstdir):
            createrepo = which('createrepo')
            if not createrepo:
                logger.warning("createrepo is not installed.")
            else:
                sh('createrepo', self.dstdir, output=False)

    def banner(self, lines):
        """Print a banner."""
        if not self.quiet:
            bar = "=" * 80 + "\n"
            sys.stdout.write(bar)
            for line in flatten(lines):
                sys.stdout.write("=  {0}\n".format(line))
            sys.stdout.write(bar)

    def summary(self):
        """Display summary of results."""
        summary = [
            "Summary", "",
            "Downloaded:", self.downloaded, "",
            "Generated:", self.generated, "",
            "Skipped:", self.skipped, "",
            "Built:", self.built, "",
        ]
        self.banner(summary)

class MockRpmBuilder(RpmBuilder):
    def __init__(self, chroot, autoclean=True, **kwargs):
        """Initialize the MockRpmBuilder object.

        chroot: name of the chroot (mock --root)
        """
        if chroot is None:
            raise ValueError("chroot argument is required.")
        self.chroot = chroot
        self.autoclean = autoclean
        self.inited = False
        RpmBuilder.__init__(self, **kwargs)

    def mock(self, *args, **kwargs):
        return sh('mock', '--root', self.chroot, *args, **kwargs)

    def init_chroot(self):
        """Initialize the chroot."""
        if not self.inited:
            logger.info("Initializing chroot {0}.".format(self.chroot))
            self.mock('--init', '--quiet', output=False)
            self.inited = True

    def __del__(self):
        """Remove the chroot."""
        if self.inited and self.autoclean:
            logger.info("Removing chroot {0}.".format(self.chroot))
            self.mock('--clean', '--quiet', output=False)
            self.inited = False

    def find_kversions_available(self):
        """List the linux kernel versions of the available kernel header packages in the chroot."""
        self.init_chroot()
        self.mock('--install', 'yum-utils', '--quiet', output=False) # for repoquery
        cmd = "repoquery --show-dupes --queryformat='%{VERSION}-%{RELEASE}' kernel-devel"
        output = self.mock('--quiet', '--chroot', cmd, quiet=True)
        logger.debug("kernel versions: {0}".format(" ".join(output)))
        return output

    def build_srpm(self):
        """Build the source rpm with mock."""
        self.prepare_spec()
        self.prepare_sources()
        self.banner(["Building srpm"])
        resultdir = "/var/lib/mock/{chroot}/result".format(chroot=self.chroot)
        self.mock(
            '--buildsrpm',
            '--resultdir', resultdir,
            '--spec', self.spec,
            '--sources', '{topdir}/SOURCES'.format(topdir=self.topdir),
            output=False)
        rpms = glob.glob("{resultdir}/*.src.rpm".format(resultdir=resultdir))
        if len(rpms) < 1:
            raise RpmBuilderError("Failed to get srpm name.")
        src = rpms[0]
        v = dict(
            topdir=self.topdir,
            dstdir=self.dstdir,
            rpm=os.path.basename(src),
        )
        if self.dstdir:
            dst = "{dstdir}/{rpm}".format(**v)
        else:
            dst = "{topdir}/SRPMS/{rpm}".format(**v)
        mkdirp(os.path.dirname(dst))
        shutil.copy(src, dst)
        self.srpm = dst
        self.built.append(self.srpm)

    def build_userspace(self, srpm=None):
        """Build the userspace rpms using mock."""
        if srpm is None:
            if self.srpm is None:
                self.build_srpm()
            srpm = self.srpm

        self.banner(["Building rpms"])
        self.init_chroot()
        logger.info("Building userspace rpms in chroot {chroot}".format(chroot=self.chroot))
        resultdir = "/var/lib/mock/{chroot}/result".format(chroot=self.chroot)
        args = self.withargs()
        args.append(srpm)
        self.mock(
            '--rebuild',
            '--arch', self.arch,
            '--resultdir', resultdir,
            '--define', 'build_userspace 1',
            '--define', 'build_modules 0',
            output=False)
        if self.dstdir:
            mkdirp(self.dstdir)
            for rpm in glob.glob("{resultdir}/*.rpm".format(resultdir=resultdir)):
                dst = "{dstdir}/{rpm}".format(dstdir=self.dstdir, rpm=os.path.basename(rpm))
                self.built.append(dst)
                shutil.copy(rpm, dst)
                logger.info("Wrote: {dst}".format(dst=dst))

    def build_kmod(self, srpm=None, kversion=None):
        """Build the a kmod rpm for the given kernel version.

        srpm:     path of the source rpm file
                  defaults to the srpm from the previous build_srpm()
        kversion: target linux kernel version, e.g., 3.10.0-514.16.1.el7
                  defaults to the currently running linux kernel version.

        A kernel-devel package for `kversion` must been installed to supply the
        required linux kernel header files.
        """
        if srpm is None:
            if self.srpm is None:
                self.build_srpm()
            srpm = self.srpm
        if kversion is None:
            kversion = self.current_kversion()

        info = ["Building module for {kversion}".format(kversion=kversion)]
        if self.count and self.total:
            info.append("Number {count} of {total}.".format(count=self.count, total=self.total))
        self.banner(info)

        self.init_chroot()
        logger.info("Building kmod for linux version {0}.".format(kversion))
        resultdir = "/var/lib/mock/{chroot}/result".format(chroot=self.chroot)
        args = self.withargs()
        args.append(srpm)
        self.mock(
            '--rebuild',
            '--arch', self.arch,
            '--resultdir', resultdir,
            '--define', 'kernvers {0}'.format(kversion),
            '--define', 'build_userspace 0',
            '--define', 'build_modules 1',
            *args,
            output=False)
        if self.dstdir:
            mkdirp(self.dstdir)
            for rpm in glob.glob("{resultdir}/*.rpm".format(resultdir=resultdir)):
                if rpm.endswith(".src.rpm"):
                    continue
                dst = "{dstdir}/{rpm}".format(dstdir=self.dstdir, rpm=os.path.basename(rpm))
                self.built.append(dst)
                shutil.copy(rpm, dst)
                logger.info("Wrote: {dst}".format(dst=dst))

def package(**kwargs):
    """Build OpenAFS rpms.

    keyword arguments:
    chroot: name of the mock chroot (default: dont use mock)
    build: what to build: 'all', 'srpm', 'userspace', 'kmods' (default: 'all')
    spec: custom rpmbuild specfile (default: in-tree openafs.spec.in)
    csdb: custom CellServDB file (default: download from url in specfile)
    srcdir: path of the checked out source tree (default: .)
    pkgdir: path of the packaging files (default: {srcdir}/src/packaging/RedHat
    topdir: path of the rpmbuild directories (default: {srcdir}/packaging/rpmbuild)
    dstdir: path to place rpms (default: None)
    arch: target arch (default: None)
    clobber: build and overwrite existing kmod-openafs rpms
    quiet:   less output
    """
    chroot = kwargs.pop('chroot', None)
    build = kwargs.pop('build', 'all')

    kversions = flatten(kwargs.pop('kversions', None)) # argparse gives a list of lists
    if chroot:
        b = MockRpmBuilder(chroot, **kwargs)
    else:
        b = RpmBuilder(**kwargs)

    # Note: It could be possible no kmods need to be built, in which case it it
    # not neccessary to build the srpm. So we defer prepare_sources until we
    # know it is needed.
    if build == 'srpm':
        b.build_srpm()
    elif build == 'userspace':
        b.build_userspace()
    elif build == 'kmod' or build == 'kmods':
        b.build_kmods(kversions=kversions)
    else:
        b.build_userspace()
        b.build_kmods(kversions=kversions)
    b.createrepo()
    b.summary()

