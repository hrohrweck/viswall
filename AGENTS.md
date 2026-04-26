# AGENTS.md — Coding Agent Context for Viswall

This file provides essential context for AI coding agents (Cursor, Claude, Goose, etc.) working on the viswall project.

## Project Overview

Viswall is a modern distributed security appliance platform. It's a complete rewrite of a legacy PHP security appliance into a microservices-based architecture with a React frontend and FastAPI backend.

**Key repos/orgs**: `hrohrweck/viswall` on GitHub

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend API** | Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| **Frontend** | React 18, TypeScript, Vite, TanStack Query, Zustand, Tailwind CSS, Recharts |
| **Database** | PostgreSQL 16 (primary), Redis 7 (cache/queues) |
| **Monitoring** | Prometheus, Grafana |
| **Testing** | pytest (backend), vitest (frontend), GitHub Actions CI/CD |
| **Deployment** | Docker Compose |

---

## Project Structure

```
viswall/
├── services/
│   ├── api-gateway/          # FastAPI app — central management API
│   │   ├── main.py           # FastAPI app entrypoint
│   │   ├── routers/          # API route modules (auth, firewall, vpn, mail, metrics, routing, audit, assistant)
│   │   ├── metrics_collector.py  # Background task that collects instance metrics
│   │   ├── tests/            # pytest tests
│   │   ├── migrations/       # Alembic migrations
│   │   ├── alembic.ini       # Alembic config
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── firewall-service/     # Agent code (1,223 lines) — wired into docker-compose (commented by default)
│   ├── mail-service/         # Agent code (902 lines) — wired into docker-compose (commented by default)
│   ├── vpn-service/          # Agent code (573 lines) — wired into docker-compose (commented by default)
│   └── sogo-service/         # SOGo groupware (CalDAV/CardDAV/ActiveSync) — wired into docker-compose
├── web-ui/                   # React + TypeScript SPA
│   ├── src/
│   │   ├── pages/            # Page components
│   │   ├── components/       # Reusable UI components
│   │   ├── components/forms/ # Form components
│   │   ├── components/ui/    # UI primitives (DataTable, Modal, etc.)
│   │   ├── hooks/useApi.ts   # All TanStack Query hooks
│   │   ├── stores/           # Zustand stores
│   │   ├── types/index.ts    # TypeScript types (mirror of Pydantic schemas)
│   │   ├── router.tsx        # React Router config
│   │   └── utils/api.ts      # Axios instance
│   ├── package.json
│   └── Dockerfile
├── shared/                   # Shared Python modules
│   ├── models.py             # SQLAlchemy ORM models (single file, all tables)
│   ├── schemas.py            # Pydantic schemas (single file, all schemas)
│   ├── database.py           # Async engine + session factory
│   ├── security.py           # JWT auth, password hashing
│   └── audit_logger.py       # Audit log helper
├── deployments/docker/       # Docker Compose stack
│   ├── docker-compose.yml    # postgres, redis, api-gateway, web-ui, nginx, sogo, prometheus, grafana
│   ├── nginx/                # nginx reverse proxy with TLS termination (self-signed or Let's Encrypt)
│   └── .env.example
└── .github/workflows/ci.yml  # GitHub Actions: test-backend, test-frontend, test-integration
```

**Note**: The `source/` directory contains legacy PHP code from the original appliance. It is preserved for reference but NOT used in the modern architecture.

---

## Important Conventions

### Backend

- **All DB operations are async**. Use `AsyncSession`, `await db.execute(...)`, `await db.commit()`.
- **Single-file models**: All SQLAlchemy models live in `shared/models.py`. Do NOT create new model files.
- **Single-file schemas**: All Pydantic schemas live in `shared/schemas.py`.
- **Routers go in `services/api-gateway/routers/`**. Each domain gets its own module.
- **Auth**: JWT via `shared/security.py`. Endpoints use `Depends(require_auth)` or `Depends(require_admin)`.
- **Audit logging**: Use `shared/audit_logger.log_audit()` after create/update/delete/deploy operations.

### Frontend

- **All API hooks in `src/hooks/useApi.ts`**. Add new `useQuery` / `useMutation` hooks here.
- **Types in `src/types/index.ts`**. Mirror the Pydantic schemas from the backend.
- **Pages in `src/pages/`**. Use kebab-case subdirectories for domain groupings (e.g., `pages/Firewall/`).
- **UI components in `src/components/ui/`**. Export from `src/components/ui/index.ts`.
- **Instance selector pattern**: Pages that operate per-instance check `selectedInstanceId` from `useInstanceStore()` and show an `EmptyState` + `InstanceSelector` if none is selected.
- **Recharts** is available for charts. Already imported in Metrics page.

### Database Migrations

Alembic is configured in `services/api-gateway/`.

```bash
cd services/api-gateway

# Generate migration from model changes
python -m alembic revision --autogenerate -m "Description"

# Apply migrations
python -m alembic upgrade head

# Rollback one
python -m alembic downgrade -1
```

- `migrations/env.py` imports `shared.models.Base` for autogenerate.
- `shared/database.py:init_db()` runs `alembic upgrade head` on startup.
- The initial migration `e1580e735101` covers all 18 tables.

### Metrics Collector

A background task (`metrics_collector.py`) runs on startup and periodically inserts `MetricSnapshot` rows for all active instances.

```bash
# Configurable via environment variables
export METRICS_COLLECTOR_ENABLED=true   # default: true
export METRICS_INTERVAL=60              # seconds, default: 60
```

- Starts automatically with the FastAPI app lifespan.
- Cancels cleanly on shutdown.
- Currently simulates realistic metrics (agents are not yet deployed).

---

## Adding a New Feature

Typical workflow:

1. **Backend**:
   - Add/modify SQLAlchemy models in `shared/models.py`.
   - Add/modify Pydantic schemas in `shared/schemas.py`.
   - Add router endpoints in `services/api-gateway/routers/<domain>.py`.
   - Run `python -m alembic revision --autogenerate -m "Description"` if models changed.
   - Add audit logging hooks for CRUD operations.

2. **Frontend**:
   - Add TypeScript types in `web-ui/src/types/index.ts`.
   - Add API hooks in `web-ui/src/hooks/useApi.ts`.
   - Build page component in `web-ui/src/pages/<PageName>.tsx`.
   - Add route in `web-ui/src/router.tsx`.
   - Add sidebar link in `web-ui/src/components/Sidebar.tsx` if needed.

3. **SDKs & CLI**:
   - Any API change (new endpoints, modified schemas, removed fields) must be reflected in the SDKs and CLI.
   - Export the updated OpenAPI spec: `python scripts/export_openapi.py`
   - Update the **Python SDK** (`sdk/python/viswall/`) resource classes and tests.
   - Regenerate **TypeScript SDK** types: `cd sdk/typescript && npm run generate-types`
   - Update the **CLI** (`sdk/cli/viswall_cli/`) commands if new operations are exposed.
   - Run SDK tests:
     - Python SDK: `cd sdk/python && python -m pytest tests/ -v && python -m ruff check viswall/ && python -m mypy viswall/`
     - TypeScript SDK: `cd sdk/typescript && npm run type-check && npm run test`
     - CLI: `cd sdk/cli && python -m pytest tests/ -v && python -m ruff check viswall_cli/ && python -m mypy viswall_cli/`

4. **Tests**:
   - Run backend tests: `cd services/api-gateway && python -m pytest tests/ -v --asyncio-mode=auto`
   - Run frontend checks: `cd web-ui && npm run type-check && npm run lint && npm run test:ci && npm run build`
   - **All relevant tests must pass locally before creating a pull request.** Do not rely solely on CI to catch failures.

5. **Commit & PR**:
    - Create feature branch from `main`.
    - One meaningful commit with clear message.
    - Push and create PR. All CI must pass.

---

## Running Locally

### Full Stack (Docker)

```bash
cd deployments/docker
cp .env.example .env
docker-compose up -d
```

- Web UI: http://localhost:3000
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Grafana: http://localhost:3001 (admin/admin)

### Backend Only

```bash
cd services/api-gateway
pip install -r requirements.txt
export DATABASE_URL="postgresql+asyncpg://viswall:viswall@localhost/viswall"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET_KEY="dev-secret-key"
uvicorn main:app --reload --host :: --port 8000
```

### Frontend Only

```bash
cd web-ui
npm install
npm run dev        # Vite dev server on :5173
npm run type-check # TypeScript check
npm run lint       # ESLint
npm run test:ci    # Vitest
npm run build      # Production build
```

---

## CI/CD Pipeline

GitHub Actions runs on every push to `main`, `develop`, or `feature/*` branches:

- `test-backend` — pytest with PostgreSQL + Redis services
- `test-frontend` — lint, type-check, vitest
- `test-integration` — integration tests
- `GitGuardian Security Checks`

All checks must pass before merging.

### PR Test Observation Rule

When a PR is filed, the agent **must** monitor CI check results until completion. If any checks are failing:

1. **Investigate immediately** — fetch logs, reproduce locally, identify root cause.
2. **Fix automatically** — commit corrections directly to the PR branch and re-push.
3. **Never leave a PR with failing checks** unless the failure is from an upstream/main branch issue outside the PR's scope (document the exception in a PR comment).
4. **Common CI pitfalls to watch for**:
   - Docker Compose IPv6 subnets must use valid hex-only ULA addresses (e.g., `fd00:42::/64`, not `fd00:viswall::/64`).
   - `docker compose up` in GitHub Actions requires the runner's Docker daemon to support the network options used.
   - Backend pytest and frontend vitest must both pass locally before pushing.

---

## Known Gaps / TODO

These are intentional or known areas needing future work. Agents should be aware:

1. **LDAP/AD auth**: Implemented with auto-provisioning. Configure via Settings page (admin only) or `POST /auth/ldap-config`.
2. **Service agents**: `firewall-service/`, `mail-service/`, `vpn-service/` agents are now wired into docker-compose (commented out by default). Uncomment in `deployments/docker/docker-compose.yml` to enable for dev/testing. They require `privileged: true` and `network_mode: host`.
3. **Ansible deployment**: Playbooks in `deployments/ansible/` support manager and agent node deployment.
4. **Grafana dashboards**: Provisioned with Prometheus datasource and a Viswall Overview dashboard. Add more dashboards to `deployments/docker/grafana/dashboards/`.
5. **LLM email classification**: Implemented with editable per-domain categories. Supports OpenAI, Anthropic Claude, and local (Ollama) models. Classification view in Mail Domain Detail page.
6. **Groupware (SOGo)**: Integrated via nginx reverse proxy. Provides CalDAV/CardDAV/ActiveSync. Authenticates against existing `users` table via PostgreSQL VIEW. Access SOGo at `/sogo`. Enable per-domain in Mail Domain settings.
7. **Legacy code**: `source/` and `files/` contain the old PHP/Perl/C++ codebase. Not used.

---

## Contact / Ownership

- **Repository**: https://github.com/hrohrweck/viswall
- **Main branch**: `main`
- **CI**: GitHub Actions (`.github/workflows/ci.yml`)
