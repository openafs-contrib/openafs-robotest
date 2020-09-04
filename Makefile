# Copyright (c) 2020 Sine Nomine Associates

.PHONY: help
help:
	@echo "usage: make <target>"
	@echo "targets:"
	@echo "  venv          install virtualenv"

.venv/bin/activate: requirements.txt
	test -d .venv || /usr/bin/python3 -m venv .venv
	. .venv/bin/activate && pip install -Ur requirements.txt
	touch .venv/bin/activate

.PHONY: venv
venv: .venv/bin/activate
