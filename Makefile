
help:
	@echo "usage: make <target> [<target> ...]"
	@echo "targets:"
	@echo "  lint            lint code"
	@echo "  test            run unit tests"
	@echo "  install         install packages, docs, and tests"
	@echo "  uninstall       uninstall packages, docs, and tests"
	@echo "  clean           remove generated files"

Makefile.config: configure.py
	python configure.py > $@

include Makefile.config

lint:
	cd src/afsrobot && $(MAKE) lint

test:
	cd src/afsrobot && $(MAKE) test

install:
	cd src/afsrobot && $(MAKE) install
	mkdir -p $(PREFIX)/afsrobot
	cp -r tests/ $(PREFIX)/afsrobot
	cp -r resources/ $(PREFIX)/afsrobot

uninstall:
	cd src/afsrobot && $(MAKE) uninstall
	rm -fr $(PREFIX)/afsrobot/tests
	rm -fr $(PREFIX)/afsrobot/resources

clean:
	cd src/afsrobot && $(MAKE) clean

distclean: clean
	rm -f Makefile.config
