.PHONY: help lint test install remove clean

help:
	@echo "usage: make <target> [<target> ...]"
	@echo "targets:"
	@echo "  help    - display targets"
	@echo "  lint    - lint code"
	@echo "  test    - run unit tests"
	@echo "  install - install local files"
	@echo "  remove  - remove package"
	@echo "  clean   - remove generated files"

lint:
	pyflakes OpenAFSLibrary/*.py OpenAFSLibrary/keywords/*.py

test:
	@echo todo

install:
	sudo pip install --upgrade --no-deps --no-index .

remove:
	sudo pip uninstall OpenAFSLibrary

clean:
	-rm -f *.pyc
	-rm -f OpenAFSLibrary/*.pyc
	-rm -f OpenAFSLibrary/keywords/*.pyc
