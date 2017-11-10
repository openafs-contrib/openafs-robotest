.PHONY: help lint test install install-user install-dev \
		uninstall uninstall-user uninstall-dev clean

include Makefile.config

LIBS=\
	libraries/afsutil \
	libraries/OpenAFSLibrary \
	libraries/afsrobot

help:
	@echo "usage: make <target> [<target> ...]"
	@echo "targets:"
	@echo "  help            display targets"
	@echo "  lint            lint code"
	@echo "  test            run unit tests"
	@echo "  install         install packages and tests (global)"
	@echo "  install-user    install packages and tests (user)"
	@echo "  install-dev     install packages and tests (developer mode)"
	@echo "  uninstall       uninstall packages and tests"
	@echo "  uninstall-user  uninstall packages and tests (user)"
	@echo "  uninstall-dev   uninstall packages and tests (developer mode)"
	@echo "  clean           remove generated files"

Makefile.config:
	if [ "$(PREFIX)" != "" ]; then \
		echo PREFIX=$(PREFIX) >Makefile.config; \
	elif [ -d /usr/local ]; then \
		echo PREFIX=/usr/local >Makefile.config; \
	elif [ -d "/opt" ]; then \
		echo PREFIX=/opt >Makefile.config; \
	fi

lint:
	for lib in $(LIBS); do $(MAKE) -C $$lib lint; done
	@echo ok

test:
	for lib in $(LIBS); do $(MAKE) -C $$lib test; done
	@echo ok

install:
	for lib in $(LIBS); do $(MAKE) -C $$lib install; done
	mkdir -p $(PREFIX)/afsrobot
	cp -r tests/ $(PREFIX)/afsrobot
	cp -r resources/ $(PREFIX)/afsrobot
	input=libraries/OpenAFSLibrary/OpenAFSLibrary; \
	output=$(PREFIX)/afsrobot/doc/OpenAFSLibary.html; \
	mkdir -p $(PREFIX)/afsrobot/doc && \
	python -m robot.libdoc --format HTML --pythonpath $$input $$input $$output
	@afsutil check --quiet || echo "Try: sudo afsutil check --fix-hosts"
	os_id=`/bin/sh -c '. preq/functions.sh; detect_os'`; \
	if [ -f preq/postinstall.$$os_id ]; then preq/postinstall.$$os_id; fi

install-user:
	for lib in $(LIBS); do $(MAKE) -C $$lib install-user; done
	mkdir -p ~/afsrobot
	cp -r tests/ ~/afsrobot
	cp -r resources/ ~/afsrobot
	input=libraries/OpenAFSLibrary/OpenAFSLibrary; \
	output=~/afsrobot/doc/OpenAFSLibary.html; \
	mkdir -p ~/afsrobot/doc && \
	python -m robot.libdoc --format HTML --pythonpath $$input $$input $$output
	afsrobot config init
	@afsutil check --quiet || echo "Try: sudo afsutil check --fix-hosts"

install-dev:
	for lib in $(LIBS); do $(MAKE) -C $$lib install-dev; done

uninstall:
	for lib in $(LIBS); do $(MAKE) -C $$lib uninstall; done
	rm -fr $(PREFIX)/afsrobot

uninstall-user:
	for lib in $(LIBS); do $(MAKE) -C $$lib uninstall; done
	rm -fr ~/afsrobot

uninstall-dev:
	for lib in $(LIBS); do $(MAKE) -C $$lib uninstall; done
	rm -fr ~/afsrobot

clean:
	for lib in $(LIBS); do $(MAKE) -C $$lib clean; done
	rm -f Makefile.config
