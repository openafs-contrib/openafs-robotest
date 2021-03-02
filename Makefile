# Copyright (c) 2020-2021 Sine Nomine Associates

.PHONY: help venv init

BUILDS=.builds.txt
MOLECULE_ENV_FILES=.molecule

help:
	@echo "usage: make <target>"
	@echo "targets:"
	@echo "  venv          install virtualenv"

.venv/bin/activate: requirements.txt
	test -d .venv || /usr/bin/python3 -m venv .venv
	. .venv/bin/activate && pip install wheel
	. .venv/bin/activate && pip install -r requirements.txt
	touch .venv/bin/activate

venv: .venv/bin/activate

init:
	afs-scenario init

builds: init
	@grep -v '^#' $(BUILDS) | while read s e; do \
		echo "Running build $$s on with vars $$e"; \
		molecule --env-file $(MOLECULE_ENV_FILES)/$${e}.yml test -s $$s || \
		(echo "FAIL: scenario $$s vars $$e"; exit 1); \
		echo "PASS: scenario $$s vars $$e"; \
	done

reset:
	ls molecule | grep -v '^__' | while read s; do molecule reset -s $$s; done
