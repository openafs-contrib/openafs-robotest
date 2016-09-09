
Notable changes.

## [Unreleased]

### Setup/Teardown

* Support RPM installations for RHEL and Centos.
* Support for systemd for rhel/centos 7.x.
* New `afsrobot` package: Convert the largish `afs-robotest` script into a proper python package with a small front-end.
* Automatically add new configuration options with default values when upgrading.
* New `host:$HOSTNAME.use` option to indicate which hosts are in use.
* New `options.dafs` option to specify when DAFS is to be setup.
* New `afsd` and `bosserver` options to speficy command line arguments.
* Provide usable "transarc-style" init scripts for solaris and for linux, based on the examples in OpenAFS.
* Support the modern style `openafs.ko` kernel module naming, even with transarc-style binaries.
* Make `afs-robotest teardown` safer.  Remove volume data only on partitions which have the `PURGE_VOLUMES` file.  The `PURGE_VOLUMES` is automatically added to the vicepa and vicepb partitions if they are created by `afs-robotest setup`.  When using pre-existing test partitions, the tester may create the `PURGE_VOLUMES` file in the partitions to be purged by `afs-robtest teardown`.
* Set the correct `rxkad.keytab` file permissions.
* Use the same random fake key for akimpersonate on each server.
* Fix the handling of non-dynroot setups so the cache manager is not started until the root volumes are online to avoid the cm from hanging in the non-dynroot environment.
* More robust cell host address detection.
* Better error messages for command not found errors.
* Print a warning and continue if akimpersonate is enabled but the path to a usable `aklog` is not specified.
* The `AFS_ROBOTEST_CONF` environment variable now gives the fully qualified filename of the configuration file. This value can be overridden with the `--config` option.
* Require a configuration file, instead of attempting to use default values if not present.
* Add the `afs-robotest config copy` and `afs-robotest config unset` subcommands.
* Removed the per host configuration options: `build`,`builddir`,`setclock`,`nuke`,`auto_*`.
* Use the actual hostname in the configuration section name instead of the hard-coded `[host:localhost]`.
* Renamed `afs-robotest sshkeys` subcommand to `afs-robotest ssh`.
* Add the `afs-robotest ssh exec` subcommand to run remote commands hosts listed in the configuration file.
* Add the `afs-robotest version` subcommand to print version information.

### Tests

* `afs-robotest run`: Add `--include` option to allow tests to be included by tag.
* Add `afs-robotest run` as an alias for `afs-robotest test`
* `echo -n` is not portable; avoid it in the tests.

### Keyword Library

* Always run `fs checkvolumes` after creating, removing, and releasing volumes to avoid stale volume cache entries and resulting ENODEV errors.
* Log stdout and stderr from commands issued via keywords `Command Should Succeed` and `Command Should Not Succeed`.
* When a command fails, it's helpful to see what the arguments were, so log them too.

### Building/Development

* Support building RPM packages for RHEL and CentOS.
* Support modern kernel module naming standards on linux (`openafs.ko`), even for transarc-style builds.
* Avoid `git clean` of the wrong directory. Do additional checks and check the `afsutil.clean` git config before running git clean.
* Add `--cf` option for transarc-style builds. Do not add extra configure options when `--cf` is given.
* New `afsutil reload` command to reload the kernel module after rebuilding it.
* `afsutil login`: Add the `--user` option to specify the username.
* `afsutil build --jobs` option for parallel builds. `nproc` determines the default number.

## [v0.4.0] 2016-02-23

* Support multi-server AFS Cell setup.

## [v0.3.0] 2016-01-08

* New `afsutil` package: New python package and script to install and setup OpenAFS before running tests. This package is independent of Robotframework.

## [v0.2.0] 2015-04-13

* New `OpenAFSLibary` Robotframework keyword library for writing tests.

## [v0.1.0] 2013-05-23

* Initial
