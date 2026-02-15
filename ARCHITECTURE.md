# Viswall - Modern Distributed Security Platform

A complete rewrite of the legacy viswall security appliance into a modern, distributed, containerized platform.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CENTRAL MANAGEMENT                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Web UI    │◄──►│  API Gateway │◄──►│   Auth      │◄──►│  Metrics    │  │
│  │  (React)    │    │  (FastAPI)   │    │  Service    │    │  (Prometheus)│  │
│  └─────────────┘    └──────┬──────┘    └─────────────┘    └─────────────┘  │
│                            │                                                │
└────────────────────────────┼────────────────────────────────────────────────┘
                             │  gRPC/REST
         ┌───────────────────┼───────────────────┐
         │                   │                   │
┌────────▼────────┐ ┌────────▼────────┐ ┌────────▼────────┐
│  MAIL SERVICE   │ │ FIREWALL SERVICE│ │  VPN SERVICE    │
│  (Modular)      │ │   (Modular)     │ │   (Modular)     │
│  - Exim/Postfix │ │  - nftables/ipt │ │  - WireGuard    │
│  - SpamAssassin │ │  - Traffic Ctrl │ │  - OpenVPN      │
│  - ClamAV       │ │  - Content Scan │ │  - IPsec        │
│  - LLM Classify │ │                 │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Project Structure

```
viswall/
├── services/
│   ├── api-gateway/          # Central API management
│   ├── auth-service/         # Authentication (LDAP/AD/Local)
│   ├── mail-service/         # Email infrastructure
│   ├── firewall-service/     # Network/firewall management
│   ├── metrics-service/      # Prometheus/Grafana stack
│   └── llm-service/          # LLM-based classification
├── web-ui/                   # React frontend
├── shared/                   # Shared libraries/models
├── deployments/
│   ├── docker/               # Docker Compose stacks
│   └── ansible/              # Native deployment
└── tests/                    # Automated tests
```

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, Alembic
- **Frontend**: React 18, TypeScript, TanStack Query, Tailwind
- **Database**: PostgreSQL (primary), Redis (cache/queues)
- **Message Queue**: Redis/RabbitMQ
- **Monitoring**: Prometheus, Grafana, Loki
- **Testing**: pytest, Playwright, GitHub Actions
- **Deployment**: Docker Compose, Ansible

## Quick Start

```bash
# Docker deployment
cd deployments/docker
docker-compose up -d

# Native deployment
cd deployments/ansible
ansible-playbook -i inventory/hosts.ini site.yml
```

## Features

- [x] Centralized multi-instance management
- [x] Modular service architecture
- [x] Multi-backend authentication (LDAP/AD/Local)
- [x] Role-based access control
- [x] Email with virus/spam scanning
- [x] Firewall with traffic shaping
- [x] Real-time metrics & monitoring
- [ ] LLM-based email classification
- [ ] Full groupware integration
