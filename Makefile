# Copyright (c) 2020-2021 Sine Nomine Associates

.PHONY: help venv init reset

help:
	@echo "usage: make <target>"
	@echo "targets:"
	@echo "  venv   install virtualenv"
	@echo "  init   initialize molecule scenarios"

.venv/bin/activate: requirements.txt
	test -d .venv || /usr/bin/python3 -m venv .venv
	. .venv/bin/activate && pip install wheel
	. .venv/bin/activate && pip install -r requirements.txt
	touch .venv/bin/activate

venv: .venv/bin/activate

init:
	afs-scenario init

reset:
	ls molecule | grep -v '^__' | while read s; do molecule reset -s $$s; done
