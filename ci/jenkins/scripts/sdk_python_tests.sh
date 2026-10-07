#!/usr/bin/env bash
# SDK validation suite (Python side) — runs INSIDE the viswall-ci-python:3.12
# container with the repo at /repo. Parity with the retired
# .github/workflows/sdk.yml jobs: export-openapi, test-python-sdk,
# lint-python-sdk, test-cli.
set -euo pipefail
cd /repo

# OpenAPI export + validation
python scripts/export_openapi.py
python -m openapi_spec_validator services/api-gateway/openapi.json

# Python SDK: tests + ruff + mypy
cd sdk/python
pip install -q -e ".[dev]"
python -m pytest tests/ -q
python -m ruff check viswall/
python -m mypy viswall/

# CLI: tests + ruff + mypy
cd /repo/sdk/cli
pip install -q -e ".[dev]"
python -m pytest tests/ -q
python -m ruff check viswall_cli/
python -m mypy viswall_cli/
