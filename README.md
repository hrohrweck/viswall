# Viswall Modern Rewrite

This is a complete rewrite of the legacy viswall security appliance into a modern, distributed, containerized platform.

## 🏗️ Architecture

The new architecture follows microservices principles with:

- **API Gateway**: Central FastAPI-based management layer
- **Web UI**: Modern React frontend
- **Modular Services**: Mail, Firewall, VPN, Metrics as independent services
- **Multi-instance Support**: Single UI managing multiple viswall instances
- **Flexible Deployment**: Docker containers or native Ubuntu installation

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
# - Grafana: http://localhost:3001 (admin/admin)
# - Prometheus: http://localhost:9090
```

### Native Deployment

```bash
cd deployments/ansible

# Edit inventory
vim inventory/production.ini

# Deploy
ansible-playbook -i inventory/production.ini site.yml
```

## 📁 Project Structure

```
viswall/
├── services/
│   ├── api-gateway/      # Central management API (FastAPI)
│   ├── auth-service/     # Authentication service (LDAP/AD/Local)
│   ├── mail-service/     # Mail infrastructure (Exim/Postfix + ClamAV + SpamAssassin)
│   ├── firewall-service/ # Firewall agent (nftables/iptables)
│   ├── metrics-service/  # Metrics collection (Prometheus/Grafana)
│   └── llm-service/      # LLM-based email classification
├── web-ui/               # React frontend
├── shared/               # Shared models, schemas, utilities
├── deployments/
│   ├── docker/           # Docker Compose configurations
│   └── ansible/          # Native deployment playbooks
└── tests/                # Automated tests
```

## ✅ Features

### Implemented
- [x] Multi-instance management architecture
- [x] RBAC with LDAP/AD/Local auth backends
- [x] FastAPI-based REST API with automatic OpenAPI docs
- [x] Docker deployment with PostgreSQL, Redis, Prometheus, Grafana
- [x] GitHub Actions CI/CD pipeline
- [x] Database models for instances, users, firewall rules, mail domains

### In Progress
- [ ] Mail service containerization
- [ ] Firewall agent for rule deployment
- [ ] React web UI implementation
- [ ] Real-time metrics collection

### Planned
- [ ] LLM-based email classification
- [ ] Full groupware integration (Calendar, Contacts)
- [ ] Policy-based routing
- [ ] Traffic shaping (QoS)
- [ ] VPN management (WireGuard, OpenVPN, IPsec)
- [ ] Native Ansible deployment
- [ ] API client SDKs

## 🔧 Development

### Backend

```bash
cd services/api-gateway
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with auto-reload
uvicorn services.api-gateway.main:app --reload
```

### Frontend

```bash
cd web-ui
npm install
npm run dev
```

## 🧪 Testing

```bash
# Backend tests
pytest services/api-gateway/tests/ -v

# Frontend tests
npm run test --prefix web-ui

# Integration tests
docker-compose -f deployments/docker/docker-compose.test.yml up --abort-on-container-exit
```

## 📄 License

MIT License - See LICENSE file for details.

---

**Note**: This is a complete rewrite. The legacy PHP codebase in `source/` is preserved for reference but not used in the new architecture.
