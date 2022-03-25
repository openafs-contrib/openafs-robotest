.PHONY: help init test check clean

help:
	@echo 'usage: make <target>'
	@echo ''
	@echo 'targets:'
	@echo '  init  create virtualenv'
	@echo '  test  run tests'
	@echo ''
	@echo 'environment:'
	@echo '  TCS_LINT=<yes|no>            Check yamllint and ansible-lint (default: yes)'
	@echo '  TCS_RUN=<yes|no>             Run molecule test (default: no)'
	@echo '  TCS_ENABLE_DKMS=<yes|no>     Use dkms when installing with rpms (default: yes)'
	@echo '  TCS_ENABLE_BUILDS=<yes|no>   Run build tasks (default: yes)'
	@echo '  TCS_COLLECTION_REPO=<name>   Where to get the openafs collection; galaxy, github, local'
	@echo '  TCS_COLLECTIONS_PATHS=<path> Path to ansible_collections when TCS_COLLECTION_REPO is "local".'

.venv/bin/activate: requirements.txt
	python3 -m venv .venv
	.venv/bin/pip install -U pip
	.venv/bin/pip install -r requirements.txt
	touch .venv/bin/activate

init: .venv/bin/activate

test: init
	(. .venv/bin/activate && pytest -v -s tests)

check: init
	(. .venv/bin/activate && pytest -v tests)

clean:
	rm -rf .venv .deps .pytest_cache
