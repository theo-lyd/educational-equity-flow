VENV_PYTHON ?= .venv/bin/python
PYTHON ?= $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),python)

.PHONY: setup-venv setup-venv-req install lint format test ingest profile-phase03 dbt-run dbt-test dbt-snapshot ml-run app

setup-venv:
	(python3 -m venv .venv || virtualenv .venv)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -e ".[dev]"

setup-venv-req:
	(python3 -m venv .venv || virtualenv .venv)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements-dev.txt

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check src tests app

format:
	$(PYTHON) -m black src tests app

test:
	$(PYTHON) -m pytest

ingest:
	$(PYTHON) -m src.ingestion.run --source data/raw --target data/bronze

profile-phase03:
	$(PYTHON) -m src.profiling.profile_raw_sources --raw-dir data/raw --out-dir docs/phase_03/artifacts

dbt-run:
	$(PYTHON) -m src.tools.dbt_runner run

dbt-test:
	$(PYTHON) -m src.tools.dbt_runner test

dbt-snapshot:
	$(PYTHON) -m src.tools.dbt_runner snapshot

ml-run:
	$(PYTHON) -m src.ml.run_all

app:
	streamlit run app/main.py
