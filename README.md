# Viswall Modern Rewrite

This is a complete rewrite of the legacy viswall security appliance into a modern, distributed, containerized platform.

## 🏗️ Architecture

The new architecture follows microservices principles with:

- **API Gateway**: Central FastAPI-based management layer
- **Web UI**: Modern React 18 + TypeScript SPA
- **Modular Services**: Mail, Firewall, VPN as independent agent services
- **Multi-instance Support**: Single UI managing multiple viswall instances
- **Flexible Deployment**: Docker containers

## 🚀 Quick Start

### Docker Deployment

```bash
cd deployments/docker

# Copy environment file
cp .env.example .env

# Start services
docker-compose up -d

# Access:
# - Web UI: http://localhost:3000
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Grafana: http://localhost:3001 (admin/admin)
# - Prometheus: http://localhost:9090
```

## 📁 Project Structure

```
viswall/
├── services/
│   ├── api-gateway/      # Central management API (FastAPI)
│   │   ├── routers/      # API routes per domain
│   │   ├── metrics_collector.py  # Background metrics collection task
│   │   ├── migrations/   # Alembic database migrations
│   │   └── tests/        # pytest test suite
│   ├── firewall-service/ # Firewall agent (wired into docker-compose, commented by default)
│   ├── mail-service/     # Mail agent (wired into docker-compose, commented by default)
│   └── vpn-service/      # VPN agent (wired into docker-compose, commented by default)
├── web-ui/               # React 18 + TypeScript frontend
│   ├── src/pages/        # Page components
│   ├── src/components/   # Reusable UI components
│   ├── src/hooks/        # TanStack Query API hooks
│   └── src/types/        # TypeScript type definitions
├── shared/               # Shared Python modules
│   ├── models.py         # SQLAlchemy ORM models (all tables)
│   ├── schemas.py        # Pydantic schemas (all schemas)
│   ├── database.py       # Async engine + Alembic integration
│   ├── security.py       # JWT auth utilities
│   └── audit_logger.py   # Audit logging helper
├── deployments/
│   └── docker/           # Docker Compose configurations
└── .github/workflows/    # GitHub Actions CI/CD
```

## ✅ Features

### Implemented

- [x] Multi-instance management architecture
- [x] RBAC with local authentication (admin, superadmin, user, readonly)
- [x] FastAPI-based REST API with automatic OpenAPI docs
- [x] Docker deployment with PostgreSQL, Redis, Prometheus, Grafana
- [x] GitHub Actions CI/CD pipeline (backend + frontend + integration tests)
- [x] React 18 SPA with full routing
- [x] Firewall rules CRUD + simulator + test suites
- [x] Traffic shaping / QoS policies and classes
- [x] VPN management (WireGuard, IPsec, OpenVPN, L2TP, PPTP) with client configs
- [x] Mail domain and user management with DKIM/DMARC/SPF toggles
- [x] Metrics dashboard with Recharts (CPU, memory, disk, mail activity)
- [x] Metrics collector background job (auto-inserts MetricSnapshot rows)
- [x] Routing rules (policy-based routing)
- [x] Audit logging for all CRUD and deploy operations
- [x] Database migrations with Alembic
- [x] Settings page with LLM config and theme toggle
- [x] LDAP/AD authentication with auto-provisioning
- [x] Service agents wired into docker-compose (firewall, mail, VPN)
- [x] Grafana provisioned dashboards with Prometheus metrics endpoint
- [x] Ansible deployment playbooks for manager and agent nodes
- [x] LLM-based email classification with editable categories (OpenAI/Anthropic/local)
- [x] Groupware integration (SOGo with CalDAV/CardDAV/ActiveSync via nginx reverse proxy)

### Planned

- [ ] API client SDKs

## 🔧 Development

### Backend

```bash
cd services/api-gateway
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database migrations
cd services/api-gateway
python -m alembic upgrade head        # Apply migrations
python -m alembic revision --autogenerate -m "Description"  # Create new migration

# Run with auto-reload
export DATABASE_URL="postgresql+asyncpg://viswall:viswall@localhost/viswall"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET_KEY="dev-secret-key"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd web-ui
npm install
npm run dev         # Vite dev server on :5173
npm run type-check  # TypeScript check
npm run lint        # ESLint
npm run test:ci     # Vitest
npm run build       # Production build
```

## 🧪 Testing

```bash
# Backend tests
cd services/api-gateway
python -m pytest tests/ -v --asyncio-mode=auto

# Frontend tests
cd web-ui
npm run test:ci

# Full checks (run before committing)
cd services/api-gateway && python -m pytest tests/ -v
cd web-ui && npm run type-check && npm run lint && npm run test:ci && npm run build
```

## 📄 License

MIT License - See LICENSE file for details.

---

**Note**: This is a complete rewrite. The legacy PHP codebase in `source/` and `files/` is preserved for reference but not used in the new architecture.
