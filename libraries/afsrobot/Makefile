.PHONY: help lint test package sdist wheel install install-user remove clean

help:
	@echo "usage: make <target> [<target> ...]"
	@echo "targets:"
	@echo "  help         - display targets"
	@echo "  lint         - run python linter"
	@echo "  test         - run unit tests"
	@echo "  package      - build distribution files"
	@echo "  sdist        - create source distribution file"
	@echo "  wheel        - create wheel distribution file"
	@echo "  install      - install package, global (requires root)"
	@echo "  install-user - install package, user"
	@echo "  install-dev  - install package, development"
	@echo "  remove       - uninstall package"
	@echo "  clean        - remove generated files"

lint:
	pyflakes afsrobot/*.py test/*.py scripts/*

test:
	python -m unittest discover test

package: sdist wheel

sdist:
	python setup.py sdist

wheel:
	python setup.py bdist_wheel

install:
	pip install --upgrade --no-deps --no-index .

install-user:
	pip install --user --upgrade --no-deps --no-index .

install-dev: lint
	pip install --user --no-deps --no-index --editable .

remove:
	pip uninstall -y afsrobot

clean:
	-rm -f *.pyc
	-rm -f test/*.pyc
	-rm -f afsrobot/*.pyc
	-rm -fr afsrobot.egg-info/ build/ dist/
