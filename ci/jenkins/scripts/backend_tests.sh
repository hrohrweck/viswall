#!/usr/bin/env bash
# Backend CI suite — runs INSIDE the viswall-ci-python:3.12 container with
# the repo mounted at /repo and PG/Redis sidecars reachable on the network.
# Parity with the retired .github/workflows/ci.yml test-backend job.
set -euo pipefail
cd /repo/services/api-gateway
export PYTHONPATH=/repo
pytest tests/ --asyncio-mode=auto -q
