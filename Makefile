.PHONY: help lint test install uninstall clean

MODULES=\
	src/OpenAFSLibrary \
	src/afsrobot

help:
	@echo "usage: make <target> [<target> ...]"
	@echo "targets:"
	@echo "  lint            lint code"
	@echo "  test            run unit tests"
	@echo "  install         install packages, docs, and tests"
	@echo "  uninstall       uninstall packages, docs, and tests"
	@echo "  clean           remove generated files"

Makefile.config:
	if [ "x$(PREFIX)" != "x" ]; then \
		echo PREFIX=$(PREFIX); \
	elif test -d /usr/local; then \
		echo PREFIX=/usr/local; \
	elif test -d /opt; then \
		echo PREFIX=/opt; \
	fi >Makefile.config

lint:
	for mod in $(MODULES); do (cd $$mod && $(MAKE) lint) || exit 1; done
	@echo ok

test:
	for mod in $(MODULES); do (cd $$mod && $(MAKE) test) || exit 1; done
	@echo ok

install:
	@echo Installing modules...
	for mod in $(MODULES); do (cd $$mod && $(MAKE) install); done
	@echo Installing tests...
	mkdir -p $(PREFIX)/afsrobot
	cp -r tests/ $(PREFIX)/afsrobot
	cp -r resources/ $(PREFIX)/afsrobot
	@echo Generating docs...
	input=src/OpenAFSLibrary/OpenAFSLibrary; \
	output=$(PREFIX)/afsrobot/doc/OpenAFSLibary.html; \
	mkdir -p $(PREFIX)/afsrobot/doc && \
	python -m robot.libdoc --format HTML --pythonpath $$input $$input $$output
	@echo "Post-install steps..."
	afsrobot init
	# sudo usermod -a -G testers <username>"
	@echo "Happy robotesting."

uninstall:
	for mod in $(MODULES); do (cd $$mod && $(MAKE) uninstall || true); done
	rm -fr $(PREFIX)/afsrobot

clean:
	for mod in $(MODULES); do (cd $$mod && $(MAKE) clean || true); done
	rm -f Makefile.config

include Makefile.config
