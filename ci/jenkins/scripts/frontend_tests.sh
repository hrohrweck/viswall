#!/usr/bin/env bash
# Frontend CI suite — runs INSIDE node:20 with the repo at /repo.
# Parity with the retired .github/workflows/ci.yml test-frontend job.
set -euo pipefail
cd /repo/web-ui
npm ci --no-audit --no-fund
npm run lint
npm run type-check
npm run test:ci
npm run build
