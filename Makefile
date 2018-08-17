
help:
	@echo "usage: make <target> [<target> ...]"
	@echo "targets:"
	@echo "  lint            lint code"
	@echo "  test            run unit tests"
	@echo "  install         install tests"
	@echo "  uninstall       uninstall tests"
	@echo "  clean           remove generated files"

Makefile.config: configure.py
	python configure.py > $@

include Makefile.config

lint:
	cd src/afsrobot && $(MAKE) lint

test:
	cd src/afsrobot && $(MAKE) test

install:
	#cd src/afsrobot && $(MAKE) install
	install -m 755 -d $(DESTDIR)$(PREFIX)/afsrobot
	cp -r tests/ $(DESTDIR)$(PREFIX)/afsrobot
	cp -r resources/ $(DESTDIR)$(PREFIX)/afsrobot

uninstall:
	cd src/afsrobot && $(MAKE) uninstall
	rm -rf $(DESTDIR)$(PREFIX)/afsrobot/tests
	rm -rf $(DESTDIR)$(PREFIX)/afsrobot/resources

clean:
	cd src/afsrobot && $(MAKE) clean

distclean: clean
	cd src/afsrobot && $(MAKE) distclean
	rm -f Makefile.config
