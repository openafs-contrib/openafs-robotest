# Copyright (c) 2021 Sine Nomine Associates

.PHONY: help
help:
	@echo "make <target>"
	@echo ""
	@echo "targets:"
	@echo "  init                 to create python virtual environment"
	@echo "  install-collection   to install openafs ansible collection"
	@echo "  build-scenario       to create a new build scenario"
	@echo "  testcell-scenario    to create a new testcell scenario"

.venv/bin/activate:
	python3 -m venv .venv
	.venv/bin/pip install -U pip
	.venv/bin/pip install wheel
	.venv/bin/pip install -r requirements.txt
	touch .venv/bin/activate
	@echo "Run 'source .venv/bin/activate' to activate your virtual environment."

.PHONY: init
init: .venv/bin/activate

.PHONY: install-collection
install-collection: init
	ansible-galaxy collection install --pre openafs_contrib.openafs

.PHONY: build-scenario
build-scenario:
	cookiecutter -o scenarios/build/molecule --directory cookiecutter/build-scenario {{ cookiecutter._template }}

.PHONY: testcell-scenario
testcell-scenario:
	cookiecutter -o scenarios/testcell --directory cookiecutter/testcell-scenario {{ cookiecutter._template }}
