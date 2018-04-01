.PHONY: help lint test preinstall install uninstall clean

MODULES=\
	src/OpenAFSLibrary \
	src/afsrobot

help:
	@echo "usage: make <target> [<target> ...]"
	@echo "targets:"
	@echo "  help            display targets"
	@echo "  lint            lint code"
	@echo "  test            run unit tests"
	@echo "  preinstall      install prereqs and system setup (requires root)"
	@echo "  install         install packages and tests"
	@echo "  uninstall       uninstall packages and tests"
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
	@afsutil check --quiet || { echo "Try: sudo afsutil check --fix-hosts"; exit 1; }

install:
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
	@echo "Post-install steps:"
	@echo ""
	@echo "    sudo usermod -a -G testers <username>"
	@echo "    afsrobot init"
	@echo ""
	@echo "Happy robotesting."

uninstall:
	for mod in $(MODULES); do (cd $$mod && $(MAKE) uninstall); done
	rm -fr $(PREFIX)/afsrobot

clean:
	for mod in $(MODULES); do (cd $$mod && $(MAKE) clean); done
	rm -f Makefile.config

include Makefile.config
