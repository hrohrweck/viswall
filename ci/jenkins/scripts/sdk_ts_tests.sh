#!/usr/bin/env bash
# SDK validation suite (TypeScript side) — runs INSIDE node:20 with the repo
# at /repo. Parity with the retired .github/workflows/sdk.yml
# test-typescript-sdk job.
set -euo pipefail
cd /repo/sdk/typescript
npm ci --no-audit --no-fund
npx tsc --noEmit
npx vitest run
npx tsc
