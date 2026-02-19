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

## VPN Architecture

### Supported Protocols (in priority order)

| Protocol | Security | Performance | Compatibility | Recommendation |
|----------|----------|-------------|---------------|----------------|
| **WireGuard** | 95/100 | 98/100 | 75/100 | ⭐ Primary - Modern, fast, secure |
| **IPsec/IKEv2** | 90/100 | 85/100 | 90/100 | Enterprise, native OS support |
| **OpenVPN** | 88/100 | 75/100 | 95/100 | Legacy support, flexible |
| **L2TP/IPsec** | 60/100 | 70/100 | 98/100 | Compatibility only |
| **PPTP** | 20/100 | 80/100 | 100/100 | ⚠️ Deprecated, not recommended |

### WireGuard (Recommended)
- **Crypto**: Curve25519, ChaCha20, Poly1305, BLAKE2s
- **Codebase**: ~4,000 lines vs 400,000+ in IPsec/OpenVPN
- **Performance**: Kernel-space implementation, minimal overhead
- **Roaming**: Seamlessly handles IP changes
- **Use cases**: Road warriors, site-to-site, containers, mobile

### IPsec/IKEv2 (strongSwan)
- **Crypto**: AES-GCM-256, SHA-384, ECDH P-384
- **Features**: MOBIKE for mobile clients, EAP authentication
- **Native support**: iOS, Android, Windows, macOS
- **Use cases**: Enterprise, mobile VPN, BYOD

### OpenVPN
- **Crypto**: AES-256-GCM, TLS 1.2+
- **Features**: Bridge mode, complex routing, plugin architecture
- **Compatibility**: Universal client support
- **Use cases**: Legacy systems, complex network setups

### VPN Service Components

```
┌────────────────────────────────────────────────────────────┐
│                     VPN SERVICE AGENT                       │
├────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  WireGuard   │  │   IPsec/     │  │   OpenVPN    │     │
│  │   Manager    │  │   IKEv2      │  │   Manager    │     │
│  │              │  │   Manager    │  │              │     │
│  │ • Key gen    │  │              │  │ • PKI/Certs  │     │
│  │ • Interface  │  │ • strongSwan │  │ • Config     │     │
│  │ • Peers      │  │ • Certs      │  │ • Clients    │     │
│  │ • NAT/fw     │  │ • Roadwarrior│  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
├────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   L2TP/      │  │  Connection  │  │    Route     │     │
│  │    PPTP      │  │   Tracker    │  │   Manager    │     │
│  │              │  │              │  │              │     │
│  │ • Legacy     │  │ • Stats      │  │ • Split      │     │
│  │ • xl2tpd     │  │ • History    │  │   tunneling  │     │
│  │ • pptpd      │  │ • Billing    │  │ • Push       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────────────────────────────────────────┘
```

### Site-to-Site VPN

Two modes supported:
1. **Mesh**: Each site connects to multiple others
2. **Hub-and-Spoke**: Central hub with satellite sites

Configuration wizard generates:
- Public key exchange
- Pre-shared keys (optional)
- Network ACLs
- Routing tables

### Client Management Features

- **Bulk generation**: Create 100+ client configs at once
- **QR codes**: Mobile device onboarding
- **Config formats**: WG Quick, OVPN, .mobileconfig
- **Revocation**: Instant cert/key invalidation
- **Bandwidth limits**: Per-client QoS
- **Split tunneling**: Route only specific traffic through VPN
