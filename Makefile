SHELL := /bin/bash
.SUFFIXES:

TARGET ?= gaesd
TESTS ?= tests
FLAKE8_FORMAT ?= '$${cyan}%(path)s$${reset}:$${yellow_bold}%(row)d$${reset}:$${green_bold}%(col)d$${reset}: $${red_bold}%(code)s$${reset} %(text)s'
PYLINT_FORMAT ?= colorized

SPHINX_DIR ?= 'docs'
# SPHINXOPTS    =
# SPHINXBUILD   = python -msphinx
SPHINXPROJ    = gaesd
SOURCEDIR     = .
# BUILDDIR      = _build

ifdef VIRTUAL_ENV
$(error This Makefile cannot be run from inside a virtualenv)
endif

# This needs to go before we fiddle with paths.
SYSTEM_PYTHON := $(shell which python2.7)

VIRTUAL_ENV := $(abspath .virtualenv)
export VIRTUAL_ENV

PATH := $(abspath .virtualenv/bin):$(PATH)
export PATH

PYTHONPATH := $(abspath app):$(PYTHONPATH)
export PYTHONPATH

PIP := $(VIRTUAL_ENV)/bin/pip
NOSETESTS := $(VIRTUAL_ENV)/bin/nosetests
FLAKE8 := $(VIRTUAL_ENV)/bin/flake8
PYLINT := $(VIRTUAL_ENV)/bin/pylint
VULTURE := $(VIRTUAL_ENV)/bin/vulture
RADON := $(VIRTUAL_ENV)/bin/radon
PYCALLGRAPH := $(VIRTUAL_ENV)/bin/pycallgraph

# First target in a Makefile is used as the default if none is chosen
# explicitly.
.PHONY: default
default: test


# === Building ================================================================

# The virtualenv is supposed to mirror what will already be present on
# app-engine. It also contains test dependencies.
.virtualenv:
	# Building python virtual environment
	$(SYSTEM_PYTHON) -m virtualenv -p $(SYSTEM_PYTHON) .virtualenv
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -r requirements/requirements.txt
	$(PIP) install --upgrade -r requirements/requirements-test.txt
	# Update the last modified date on .virtualenv so that, if nothing has
	# changed, make knows not to rebuild it next time it runs.
	touch .virtualenv

.PHONY: build
build: .virtualenv


# === Testing =================================================================

TESTS_ABS := $(foreach path,$(TESTS),$(abspath $(path)))

# Run all tests.
.PHONY: test
test: build
	# Running tests
	$(NOSETESTS) $(TESTS_ABS) -v --logging-level=INFO \
	        --processes=-1 --process-timeout=240


# === Linting =================================================================

# Flake8 wraps pyflakes, pep8 and McCabe, providing consistent
# output and a way to silence specific warnings.
.PHONY: flake8
flake8: build
	# Running Flake8
	$(FLAKE8) $(TARGET) --format=$(FLAKE8_FORMAT)

# Perform a pass/fail pylint run.  This should always be clean.
.PHONY: pylint
pylint: build
	# Running pylint
	$(PYLINT) -E \
		--output-format=$(PYLINT_FORMAT) \
		$(TARGET)

# Perform a full pylint run, including warnings and report generation.
.PHONY: pylint
pylint-reports: build
	# Running pylint
	$(PYLINT) \
		--output-format=$(PYLINT_FORMAT) \
		$(TARGET)

# Vulture finds unused classes, functions and variables in your code.
# This helps you cleanup and find errors in your programs. If you run
# it on both your library and test suite you can find untested code.
.PHONY: vulture
vulture: build
	# Running vulture
	$(VULTURE) $(TARGET)

# Run all linting steps (currently just flake8)
.PHONY: lint
lint: flake8 pylint vulture


# === Metrics =================================================================

# Radon is a Python tool that computes various metrics from the source code.
# Radon can compute:
# - McCabe's complexity, i.e. cyclomatic complexity
# - raw metrics (these include SLOC, comment lines, blank lines, &c.)
# - Halstead metrics (all of them)
# - Maintainability Index (the one used in Visual Studio)
.PHONY: radon
radon: build
	# Running radon
	$(RADON) cc $(TARGET) -n 50 -s --total-average
	echo -e "\033[0;35m"
	$(RADON) raw $(TARGET) --summary

# Call Graph For Python.
# A call graph is a control flow graph, which represents calling
# relationships between subroutines in a computer program.
# https://github.com/gak/pycallgraph/
.PHONY: pycallgraph
pycallgraph: build
	# Running Static visualizations of the call graph
	$(PYCALLGRAPH) graphviz -- $(TARGET)


# === Documentation ===========================================================

# ==== Sphinx Docs ============================================================

.PHONY: sphinx-html
sphinx-html:
	$(MAKE) -C $(SPHINX_DIR) html

.PHONY: sphinx-clean
sphinx-clean:
	$(MAKE) -C $(SPHINX_DIR) clean
	find doc/source/ -name '*.rst' ! -name 'index.rst' -type f -exec rm -f {} +

.PHONY: sphinx-doc
sphinx-doc: sphinx-html


# === Cleanup =================================================================

.PHONY: clean
clean: sphinx-clean
	# Cleaning
	rm -R .virtualenv











