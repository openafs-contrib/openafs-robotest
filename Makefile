# Copyright (c) 2020-2021 Sine Nomine Associates

.PHONY: help venv init

S=default
CONFIG=~/.config/openafs-robotest
BUILDS=$(CONFIG)/builds.d
TESTS=$(CONFIG)/tests.d

help:
	@echo "usage: make <target>"
	@echo "targets:"
	@echo "  venv   install virtualenv"
	@echo "  init   initialize molecule scenarios"
	@echo "  builds run build scenarios in $(BUILDS)"
	@echo "  tests  run test scenarios in $(TESTS)"

.venv/bin/activate: requirements.txt
	test -d .venv || /usr/bin/python3 -m venv .venv
	. .venv/bin/activate && pip install wheel
	. .venv/bin/activate && pip install -r requirements.txt
	touch .venv/bin/activate

venv: .venv/bin/activate

init:
	afs-scenario init

builds: init
	@for e in $(BUILDS)/*.yml; do \
		cmd=`molecule --env-file $$e test -s build` || \
		echo "Running: $$cmd"; $$cmd || \
		(echo "FAIL: build $$e"; exit 1); \
		echo "PASS: build $$e"; \
	done

tests: init
	@for e in $(TESTS)/*.yml; do \
		cmd=`molecule --env-file $$e test -s $(S)`; \
		echo "Running: $$cmd"; $$cmd || \
		(echo "FAIL: scenario $(S) vars $$e"; exit 1); \
		echo "PASS: scenario $(S) vars $$e"; \
	done

reset:
	ls molecule | grep -v '^__' | while read s; do molecule reset -s $$s; done
