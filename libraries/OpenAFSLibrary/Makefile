PACKAGE=OpenAFSLibrary
.PHONY: help lint test package version sdist wheel install install-user uninstall clean

help:
	@echo "usage: make <target> [<target> ...]"
	@echo "targets:"
	@echo "  help         - display targets"
	@echo "  lint         - run python linter"
	@echo "  package      - build distribution files"
	@echo "  sdist        - create source distribution file"
	@echo "  wheel        - create wheel distribution file"
	@echo "  install      - install package, global (requires root)"
	@echo "  install-user - install package, user"
	@echo "  install-dev  - install package, development"
	@echo "  uninstall    - uninstall package"
	@echo "  clean        - remove generated files"

lint:
	pyflakes $(PACKAGE)/*.py $(PACKAGE)/keywords/*.py

package: sdist wheel

version:
	echo "VERSION = '$$(git describe --tags | sed 's/^v//')'" > $(PACKAGE)/__version__.py

sdist: version
	python setup.py sdist

wheel: version
	python setup.py bdist_wheel

install: version
	pip install --upgrade .

install-user: version
	pip install --user --upgrade .

install-dev: version lint
	pip install --user --editable .

uninstall:
	pip uninstall -y $(PACKAGE)

clean:
	-rm -f *.pyc
	-rm -f $(PACKAGE)/*.pyc
	-rm -f $(PACKAGE)/keywords/*.pyc
	-rm -f $(PACKAGE)/__version__.py
	-rm -fr $(PACKAGE).egg-info/ build/ dist/
