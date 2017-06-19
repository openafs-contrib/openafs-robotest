.PHONY: help lint test install remove clean

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
	(cd libraries/afsutil && $(MAKE) lint)
	(cd libraries/afsrobot && $(MAKE) lint)
	(cd libraries/OpenAFSLibrary && $(MAKE) lint)

test:
	(cd libraries/afsutil && $(MAKE) test)
	(cd libraries/afsrobot && $(MAKE) test)
	(cd libraries/OpenAFSLibrary && $(MAKE) test)

install:
	sudo ./install.sh

remove:
	sudo ./uninstall.sh

clean:
	(cd libraries/afsutil && $(MAKE) clean)
	(cd libraries/afsrobot && $(MAKE) clean)
	(cd libraries/OpenAFSLibrary && $(MAKE) clean)
