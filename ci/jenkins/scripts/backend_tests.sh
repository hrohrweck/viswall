#!/usr/bin/env bash
# Backend CI suite — runs INSIDE the viswall-ci-python:3.12 container with
# the repo mounted at /repo and PG/Redis sidecars reachable on the network.
# Parity with the retired .github/workflows/ci.yml test-backend job.
set -euo pipefail
cd /repo/services/api-gateway
export PYTHONPATH=/repo

# Migration graph must stay linear: two heads break `alembic upgrade head`
# in production (happened when two PRs with migrations merged in parallel).
HEADS=$(python -m alembic heads 2>/dev/null | grep -cE "^[0-9a-f]{6,}" || true)
if [ "$HEADS" != "1" ]; then
  echo "FAIL: alembic reports $HEADS head revisions — merge them (alembic merge) or re-parent before merging:"
  python -m alembic heads
  exit 1
fi

pytest tests/ --asyncio-mode=auto -q
