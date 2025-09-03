.PHONY: help venv install run start freeze clean

VENV_DIR := .venv
PYTHON := python3
PIP := $(VENV_DIR)/bin/pip
PY := $(VENV_DIR)/bin/python

help:
	@echo "Targets:"
	@echo "  make venv     - Create virtualenv in $(VENV_DIR)"
	@echo "  make install  - Install Python deps into venv"
	@echo "  make run      - Run Flask server (server.py)"
	@echo "  make start    - Alias for run"
	@echo "  make freeze   - Export locked deps to requirements.txt"
	@echo "  make clean    - Remove venv and Python caches"

venv:
	@test -d $(VENV_DIR) || $(PYTHON) -m venv $(VENV_DIR)

install: venv
	$(PIP) install -r requirements.txt

run: venv
	$(PY) server.py

start: run

freeze: venv
	$(PIP) freeze > requirements.txt

clean:
	rm -rf $(VENV_DIR) **/__pycache__ **/.pytest_cache
