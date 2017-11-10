.PHONY: help lint test install remove clean

LIBS=\
	libraries/afsutil \
	libraries/afsrobot \
	libraries/OpenAFSLibrary

help:
	@echo "usage: make <target> [<target> ...]"
	@echo "targets:"
	@echo "  help    - display targets"
	@echo "  lint    - lint code"
	@echo "  test    - run unit tests"
	@echo "  install - install packages and tests"
	@echo "  remove  - remove packages"
	@echo "  clean   - remove generated files"

lint:
	for lib in $(LIBS); do $(MAKE) -C $$lib lint; done
	@echo ok

test:
	for lib in $(LIBS); do $(MAKE) -C $$lib test; done
	@echo ok

install-dev:
	for lib in $(LIBS); do $(MAKE) -C $$lib install-dev; done

install:
	./install.sh

remove:
	./uninstall.sh

clean:
	for lib in $(LIBS); do $(MAKE) -C $$lib clean; done
