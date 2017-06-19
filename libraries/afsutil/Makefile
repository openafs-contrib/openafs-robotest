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
	pyflakes afsutil/*.py test/*.py scripts/*

test:
	python -m unittest discover test

install:
	sudo pip install --upgrade --no-deps --no-index .

remove:
	sudo pip uninstall afsutil

clean:
	-rm -f *.pyc
	-rm -f test/*.pyc
	-rm -f afsutil/*.pyc
	-rm -fr afsutil.egg-info/
