PACKAGE=afsutil
.PHONY: help lint test package version sdist wheel install install-user uninstall clean

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
	@echo "  uninstall    - uninstall package"
	@echo "  clean        - remove generated files"


lint:
	pyflakes $(PACKAGE)/*.py test/*.py scripts/*

test:
	python -m test.test_system -v
	python -m test.test_keytab -v
	#python -m test.test_package -v

package: sdist wheel

version:
	echo "VERSION = '$$(git describe --tags | sed 's/^v//')'" > $(PACKAGE)/__version__.py

sdist: version
	python setup.py sdist

wheel: version
	python setup.py bdist_wheel

install: version
	pip install --upgrade --no-deps --no-index .

install-user: version
	pip install --user --upgrade --no-deps --no-index .

install-dev: version lint
	pip install --user --no-deps --no-index --editable .

uninstall:
	pip uninstall -y $(PACKAGE)

clean:
	-rm -f *.pyc
	-rm -f test/*.pyc
	-rm -f $(PACKAGE)/*.pyc
	-rm -fr $(PACKAGE).egg-info/ build/ dist/
