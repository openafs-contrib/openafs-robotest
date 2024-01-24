# Copyright 2024 Sine Nomine Associates

PYTHON3=/usr/bin/python3.12
BIN=.venv/bin
PIP=$(BIN)/pip
ACTIVATE=$(BIN)/activate

.PHONY: help
help:
	@echo "usage: make <target>"
	@echo ""
	@echo "setup targets:"
	@echo "  init       Create the Python virtualenv"
	@echo ""
	@echo "test targets:"
	@echo "  test       Install OpenAFS then run tests on a virtual machine"
	@echo ""
	@echo "documentation targets:"
	@echo "  docs       Generate the html docs"
	@echo "  preview    Local preview of the html docs"
	@echo ""
	@echo "cleanup targets:"
	@echo "  clean      Remove generated files"
	@echo "  distclean  Remove generated files and virtualenv"

$(ACTIVATE): Makefile requirements.txt
	$(PYTHON3) -m venv .venv
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt
	$(BIN)/patch-molecule-schema
	touch $(ACTIVATE)

.PHONY: init
init: $(ACTIVATE)

.PHONY: test
test: init
	. $(ACTIVATE); cd scenarios && molecule test

.PHONY: docs
docs: init
	. $(ACTIVATE); $(MAKE) -C docs html

.PHONY: preview
preview: docs
	xdg-open docs/build/html/index.html

.PHONY: clean
clean:
	rm -rf docs/build
	rm -rf scenarios/reports

.PHONY: reallyclean distclean
reallyclean distclean: clean
	rm -rf .config .venv
