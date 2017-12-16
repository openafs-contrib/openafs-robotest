.PHONY: help lint test preinstall postinstall install install-user \
		install-dev uninstall uninstall-user uninstall-dev clean

MODULES=\
	src/afsutil \
	src/OpenAFSLibrary \
	src/afsrobot

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
	if [ "x$(PREFIX)" != "x" ]; then \
		echo PREFIX=$(PREFIX); \
	elif test -d /usr/local; then \
		echo PREFIX=/usr/local; \
	elif test -d /opt; then \
		echo PREFIX=/opt; \
	fi >Makefile.config
	echo "OSID=`install/detect-os.sh`" >>Makefile.config

lint:
	for mod in $(MODULES); do (cd $$mod && $(MAKE) lint) || exit 1; done
	@echo ok

test:
	for mod in $(MODULES); do (cd $$mod && $(MAKE) test) || exit 1; done
	@echo ok

preinstall:
	install/preinstall.$(OSID)

postinstall:
	test -x install/postinstall.$(OSID) && install/postinstall.$(OSID)

install-afsutil:
	(cd src/afsutil && make install)

install: preinstall install-afsutil
	@afsutil check --quiet || { echo "Try: sudo afsutil check --fix-hosts"; exit 1; }
	@echo installing modules...
	for mod in $(MODULES); do (cd $$mod && $(MAKE) install); done
	@echo installing tests...
	mkdir -p $(PREFIX)/afsrobot
	cp -r tests/ $(PREFIX)/afsrobot
	cp -r resources/ $(PREFIX)/afsrobot
	@echo generating docs...
	input=src/OpenAFSLibrary/OpenAFSLibrary; \
	output=$(PREFIX)/afsrobot/doc/OpenAFSLibary.html; \
	mkdir -p $(PREFIX)/afsrobot/doc && \
	python -m robot.libdoc --format HTML --pythonpath $$input $$input $$output
	@echo checking...
	if test -x install/postinstall.$(OSID); then install/postinstall.$(OSID); fi
	@echo ""
	@echo "Post-install steps:"
	@echo ""
	@echo "    sudo usermod -a -G testers <username>"
	@echo "    afsrobot init"
	@echo ""
	@echo "Happy robotesting."

install-user:
	@afsutil check --quiet || echo "Try: sudo afsutil check --fix-hosts"
	(cd src/OpenAFSLibrary && make install-user)
	(cd src/afsrobot && make install-user)
	mkdir -p ~/afsrobot
	cp -r tests/ ~/afsrobot
	cp -r resources/ ~/afsrobot
	input=src/OpenAFSLibrary/OpenAFSLibrary; \
	output=~/afsrobot/doc/OpenAFSLibary.html; \
	mkdir -p ~/afsrobot/doc && \
	python -m robot.libdoc --format HTML --pythonpath $$input $$input $$output
	afsrobot config init

install-dev:
	@afsutil check --quiet || echo "Try: sudo afsutil check --fix-hosts"
	(cd src/OpenAFSLibrary && make install-dev)
	(cd src/afsrobot && make install-dev)
	afsrobot config init

uninstall:
	for mod in $(MODULES); do (cd $$mod && $(MAKE) uninstall); done
	rm -fr $(PREFIX)/afsrobot

uninstall-user:
	for mod in $(MODULES); do (cd $$mod && $(MAKE) uninstall); done
	rm -fr ~/afsrobot

uninstall-dev:
	for mod in $(MODULES); do (cd $$mod && $(MAKE) uninstall); done
	rm -fr ~/afsrobot

clean:
	for mod in $(MODULES); do (cd $$mod && $(MAKE) clean); done
	rm -f Makefile.config

include Makefile.config
