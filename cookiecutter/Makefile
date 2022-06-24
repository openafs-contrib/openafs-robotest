.PHONY: help init test check clean

help:
	@echo 'usage: make <target>'
	@echo ''
	@echo 'targets:'
	@echo '  init  create virtualenv'
	@echo '  test  run tests'
	@echo ''
	@echo 'environment:'
	@echo '  MOLECULE_DRIVER_NAEME=<name>   driver name for run tests'

.venv/bin/activate: requirements.txt
	python3 -m venv .venv
	.venv/bin/pip install -U pip
	.venv/bin/pip install -r requirements.txt
	touch .venv/bin/activate

init: .venv/bin/activate

test: init
	(. .venv/bin/activate && pytest -v -s tests -k render)

check: init
	(. .venv/bin/activate && pytest -v tests -k render)

clean:
	rm -rf .venv .deps .pytest_cache
