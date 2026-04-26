# Viswall

Viswall is a modern, distributed security appliance platform for managing firewall, VPN, mail, and routing infrastructure across multiple edge instances from a single control plane. It replaces legacy monolithic security appliances with a containerized microservices architecture built on FastAPI, React, and PostgreSQL.

## What Viswall Does

Viswall provides a centralized management layer for security-critical network services. Instead of configuring each firewall or mail server individually through SSH and text files, administrators use a web dashboard or API to define policies once and push them to any number of managed instances.

### Core Capabilities

**Multi-Instance Management.** A single Viswall manager can control dozens of edge instances. Each instance represents a physical or virtual appliance running firewall, VPN, or mail services. The manager tracks instance health through periodic heartbeats, collects metrics, and maintains a configuration version for each node so agents know when to pull updated rules.

**Firewall Rules and NAT.** Define accept, drop, and reject rules across input, output, and forward chains. Rules support protocol filtering, source and destination IP ranges, and port specifications. NAT rules handle address translation. Rules are authored in the web UI or via API, stored in the manager's database, and applied to instances through a dedicated firewall agent.

**VPN Servers and Clients.** Deploy WireGuard, IPsec, OpenVPN, L2TP, and PPTP servers across instances. Client configurations are generated automatically, including QR codes and downloadable profiles. Site-to-site tunnels bridge networks between instances.

**Mail Domains and Users.** Host email for multiple domains with per-domain toggles for spam filtering, virus scanning, DKIM signing, DMARC policies, and SPF records. LLM-based email classification categorizes incoming mail using OpenAI, Anthropic Claude, or local Ollama models, with configurable per-domain categories. SOGo groupware provides CalDAV, CardDAV, and ActiveSync for mail users.

**Policy Routing.** Direct traffic across specific gateways based on source or destination criteria, enabling multi-WAN failover and traffic segmentation.

**Metrics and Monitoring.** A background metrics collector gathers CPU, memory, disk, network, and mail activity from every instance. Data is stored in PostgreSQL and visualized through Grafana dashboards backed by Prometheus.

**Audit Logging.** Every create, update, delete, and deploy operation is logged with the user, timestamp, instance, and before/after state. Audit logs are queryable through the API and web UI.

**Authentication.** Local JWT-based authentication supports role-based access control with admin, superadmin, user, and readonly roles. LDAP and Active Directory integration provides auto-provisioning for enterprise environments.

**SDKs and Automation.** Resource-oriented Python and TypeScript SDKs wrap the entire REST API. A command-line tool (`viswall-cli`) enables scripting of instance provisioning, rule deployment, and metrics retrieval.

---

## Architecture

Viswall separates the control plane (manager) from the data plane (agents). This architecture lets you run the manager in a central data center while agents operate on edge hardware close to the traffic they protect.

```
                               ┌─────────────────────────────────────────┐
                               │           Manager Node                  │
                               │  ┌──────────┐  ┌──────────┐  ┌──────┐ │
                               │  │ Web UI   │  │ API      │  │ Nginx│ │
                               │  │ (React)  │  │ Gateway  │  │(TLS) │ │
                               │  └──────────┘  │ (FastAPI)│  └──────┘ │
                               │                └────┬─────┘           │
                               │                     │                  │
                               │  ┌──────────────────┼────────────────┐│
                               │  │ PostgreSQL       │ Redis          ││
                               │  │ (state)          │ (cache/queues) ││
                               │  └──────────────────┘────────────────┘│
                               │         Prometheus + Grafana           │
                               └──────────────────┬─────────────────────┘
                                                  │ HTTPS / API
                         ┌────────────────────────┼────────────────────────┐
                         │                        │                        │
                  ┌──────▼──────┐          ┌──────▼──────┐          ┌──────▼──────┐
                  │  Instance 1 │          │  Instance 2 │          │  Instance N │
                  │ ┌─────────┐ │          │ ┌─────────┐ │          │ ┌─────────┐ │
                  │ │Firewall │ │          │ │  Mail   │ │          │ │   VPN   │ │
                  │ │ Agent   │ │          │ │ Agent   │ │          │ │ Agent   │ │
                  │ └─────────┘ │          │ └─────────┘ │          │ └─────────┘ │
                  └─────────────┘          └─────────────┘          └─────────────┘
```

### Component Responsibilities

**API Gateway** (`services/api-gateway/`). The central FastAPI application exposes the REST API used by the web UI, SDKs, and CLI. It owns the database schema, handles authentication, routes requests to domain-specific modules (auth, firewall, VPN, mail, metrics, routing, audit), and runs the background metrics collector. On startup, it applies any pending Alembic database migrations automatically.

**Web UI** (`web-ui/`). A React 18 single-page application built with TypeScript, Vite, TanStack Query, Zustand, and Tailwind CSS. It provides pages for instance management, firewall rules, VPN configuration, mail domains, routing policies, metrics dashboards, audit logs, settings, and LLM classification review. The UI communicates exclusively with the API Gateway over HTTPS.

**Nginx** (`deployments/docker/nginx/`). Acts as a reverse proxy in front of the API Gateway and Web UI containers. Handles TLS termination using either self-signed certificates or Let's Encrypt. Also proxies `/sogo` to the SOGo groupware container.

**Agents** (`services/firewall-service/`, `mail-service/`, `vpn-service/`). Lightweight Python services that run on each managed instance. They poll the manager for configuration changes (via heartbeat responses that include a config version) and apply rules locally using iptables/nftables, Postfix/Dovecot, or WireGuard/IPsec tools. Agents are wired into the Docker Compose stack but commented out by default; in production they run on bare-metal or VM instances with `privileged: true` and `network_mode: host`.

**PostgreSQL** (primary database). Stores all persistent state: users, instances, firewall rules, VPN servers and clients, mail domains and users, metrics snapshots, audit logs, and routing policies. SQLAlchemy 2.0 async models live in `shared/models.py`.

**Redis** (cache and queues). Caches session data and acts as a lightweight message broker for background tasks.

**Prometheus** (metrics scraping). Scrapes the `/metrics` endpoint on the API Gateway for application-level metrics.

**Grafana** (visualization). Pre-provisioned with a Prometheus data source and a Viswall Overview dashboard showing instance health, resource utilization, and mail activity.

**SOGo** (groupware). Provides CalDAV, CardDAV, and ActiveSync for mail users. Authenticates against the existing PostgreSQL `users` table via a database VIEW. Enabled per-domain in mail settings.

---

## Production Deployment

### Docker Compose (Single Node)

The simplest production deployment runs the entire control plane on a single Docker host.

```bash
cd deployments/docker
cp .env.example .env
# Edit .env to set:
#   DOMAIN=viswall.example.com
#   ACME_EMAIL=admin@example.com  (for Let's Encrypt)
#   JWT_SECRET_KEY=<strong-random-key>
#   DATABASE_URL=postgresql+asyncpg://viswall:<password>@postgres/viswall

docker-compose up -d
```

This starts PostgreSQL, Redis, the API Gateway, Web UI, Nginx (with TLS), Prometheus, Grafana, and SOGo on a single machine. Nginx handles TLS termination and routes traffic to the appropriate backend.

Access points after deployment:
- Web UI: `https://viswall.example.com`
- API: `https://viswall.example.com/api/v1`
- Grafana: `https://viswall.example.com/grafana`
- SOGo: `https://viswall.example.com/sogo`

### Manager and Agent Nodes (Distributed)

For production networks with multiple edge locations, deploy the manager separately from the agents.

**Manager Node.** Deploy only the control plane services:
- PostgreSQL + Redis
- API Gateway + Web UI + Nginx
- Prometheus + Grafana

The manager node requires only standard Docker networking. No privileged containers or host networking mode is needed.

**Agent Nodes.** Each edge instance runs one or more agents:
- `firewall-service` — applies iptables/nftables rules
- `mail-service` — manages Postfix/Dovecot configuration
- `vpn-service` — configures WireGuard/IPsec/OpenVPN

Agents need:
- `privileged: true` (for iptables/netfilter access)
- `network_mode: host` (for direct network interface manipulation)
- Reachability to the manager's API endpoint over HTTPS
- A unique API key per instance, stored in the manager database

Agents register with the manager through the heartbeat endpoint. The manager responds with the current configuration version; if the version differs from what the agent has applied, the agent pulls the full configuration and applies it locally.

**Ansible Playbooks.** For organizations managing many instances, Ansible playbooks in `deployments/ansible/` automate manager and agent node deployment. The playbooks install Docker, generate TLS certificates, configure Nginx, and start the appropriate services based on the target node's role (`manager` or `agent`).

### Scaling Considerations

**Database.** PostgreSQL can be replaced with a managed instance (AWS RDS, Google Cloud SQL, Azure Database) by updating `DATABASE_URL`. Run migrations from any host with network access to the database:

```bash
cd services/api-gateway
python -m alembic upgrade head
```

**API Gateway.** The API Gateway is stateless except for database connections. Scale horizontally by running multiple API Gateway containers behind Nginx and using a shared PostgreSQL instance.

**Metrics Storage.** Metrics snapshots accumulate over time. For long-term retention, configure PostgreSQL partitioning on the `metric_snapshots` table or export Prometheus data to an external time-series database.

**Agent Resilience.** Agents cache their last-applied configuration locally. If the manager is temporarily unreachable, agents continue enforcing the last known ruleset and retry heartbeats with exponential backoff.

---

## Selective Component Deployment

You do not need to run the entire stack. The manager services are stateless except for PostgreSQL and Redis, and agents are optional depending on which capabilities you need. Use explicit service names with `docker-compose up -d` or create an override file (`docker-compose.override.yml`) to customize the deployment.

### Manager Only (No Agents, No Monitoring)

Run just the control plane — API, web UI, database, and reverse proxy. Use this when you will deploy agents on separate edge nodes.

```bash
cd deployments/docker
docker-compose up -d postgres redis api-gateway web-ui nginx
```

Services started: PostgreSQL, Redis, API Gateway, Web UI, Nginx.

### Minimal Firewall Appliance

Run the manager plus the firewall agent on a single host. The firewall agent requires `privileged: true` and `network_mode: host`.

Uncomment the `firewall-service` block in `docker-compose.yml`, then start:

```bash
docker-compose up -d postgres redis api-gateway web-ui nginx firewall-service
```

> **Note:** The firewall agent manipulates the host's netfilter tables. Only run this on a dedicated appliance or VM.

### Mail Server with Groupware

Run the manager, SOGo groupware, Ollama (for LLM email classification), and the mail agent on a single host.

Uncomment the `mail-service` block in `docker-compose.yml`, then start:

```bash
docker-compose up -d postgres redis api-gateway web-ui nginx sogo ollama ollama-pull mail-service
```

Exposed ports: `25`, `465`, `587` (SMTP), `143`, `993` (IMAP). SOGo is available at `/sogo`.

### VPN Server

Run the manager plus the VPN agent on a single host. The VPN agent requires `privileged: true` and `network_mode: host`.

Uncomment the `vpn-service` block in `docker-compose.yml`, then start:

```bash
docker-compose up -d postgres redis api-gateway web-ui nginx vpn-service
```

> **Note:** The VPN agent creates WireGuard/IPsec interfaces on the host network namespace.

### Full Stack (Single Node)

Run everything on one machine — manager, all agents, monitoring, and LLM inference. This is useful for homelabs and small offices.

Uncomment all agent blocks in `docker-compose.yml`, then start the full stack:

```bash
docker-compose up -d
```

### Using Compose Override Files

For cleaner selective deployments, create a `docker-compose.override.yml` instead of editing the main file. For example, to deploy a mail-only node:

```yaml
# deployments/docker/docker-compose.override.yml
services:
  mail-service:
    build:
      context: ../..
      dockerfile: services/mail-service/Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://viswall:${DB_PASSWORD:-viswall}@postgres/viswall
      REDIS_URL: redis://redis:6379/1
    privileged: true
    ports:
      - "25:25"
      - "465:465"
      - "587:587"
      - "143:143"
      - "993:993"
    networks:
      - viswall
```

Then run:

```bash
docker-compose up -d
```

Docker Compose automatically merges `docker-compose.yml` and `docker-compose.override.yml`.

---

## IPv6 Support

Viswall is designed for dual-stack (IPv4 + IPv6) operation. The Docker Compose stack enables IPv6 by default on a ULA subnet (`fd00:42::/64`), and all major components have been updated to handle IPv6 addresses and traffic.

### Support Matrix

| Component | IPv6 Status | Notes |
|-----------|------------|-------|
| Docker Networking | Enabled by default | ULA subnet via `IPV6_SUBNET` env var |
| Nginx | Dual-stack listeners | `listen [::]:80` and `listen [::]:443` |
| API Gateway | Dual-stack bind | Uvicorn bound to `::` |
| Firewall Agent | Full dual-stack | Parallel `ip`/`ip6` nftables sets and rules; IPv6 `tc flower` filters |
| VPN — WireGuard | Full dual-stack | `ip6tables` FORWARD + optional NAT via `ipv6_nat_enabled` |
| VPN — IPsec | IPv6 client pools | `rightsourceip` supports IPv6 when `ipv6_tunnel_network` is set |
| VPN — OpenVPN | IPv6 server directive | `server-ipv6` added when `ipv6_tunnel_network` is set |
| Mail — Exim | Dual-stack listeners | `local_interfaces = 0.0.0.0 : ::`; IPv6 HELO validation |
| Mail — SOGo | Dual-stack localhost | Memcached host set to `localhost` (resolves to `::1`) |
| Monitoring | Hostname-based | Prometheus/Grafana use Docker DNS; works when IPv6 is enabled |

### Prerequisites

Your Docker daemon must have IPv6 support enabled. On most modern Linux distributions this is automatic when `enable_ipv6: true` is present in the Compose file. If you encounter issues, ensure `/etc/docker/daemon.json` contains:

```json
{
  "ipv6": true,
  "fixed-cidr-v6": "fd00::/64"
}
```

### VPN IPv6 Tunnels

When creating a VPN server, set `ipv6_tunnel_network` to allocate an IPv6 client pool:

- **WireGuard**: `ipv6_tunnel_network: fd00:200::/64` — clients get dual-stack `AllowedIPs`. Enable `ipv6_nat_enabled` only if you need NAT66 (routed IPv6 is the default).
- **OpenVPN**: `ipv6_tunnel_network: fd00:201::/64` — adds `server-ipv6` to the config.
- **IPsec**: `ipv6_tunnel_network: fd00:202::/64` — used as IPv6 `rightsourceip` in road-warrior mode.

---

## Quick Start

```bash
cd deployments/docker
cp .env.example .env
# Edit .env with your domain and secrets
docker-compose up -d
```

Then open `https://localhost` (or your configured domain) and log in with the default admin credentials.

---

## Project Structure

```
viswall/
├── services/
│   ├── api-gateway/          # FastAPI management API
│   ├── firewall-service/     # Firewall agent (edge node)
│   ├── mail-service/         # Mail agent (edge node)
│   ├── vpn-service/          # VPN agent (edge node)
│   └── sogo-service/         # SOGo groupware
├── web-ui/                   # React 18 + TypeScript frontend
├── shared/                   # Shared Python modules (models, schemas, auth)
├── sdk/
│   ├── python/               # Python SDK (viswall-sdk)
│   ├── typescript/           # TypeScript SDK (@viswall/sdk)
│   └── cli/                  # CLI tool (viswall-cli)
├── deployments/
│   ├── docker/               # Docker Compose stack
│   └── ansible/              # Ansible playbooks
└── .github/workflows/        # CI/CD pipelines
```

---

## SDKs & CLI

Viswall provides official SDKs and a command-line tool for automation.

**Python SDK**

```bash
pip install viswall-sdk
```

```python
from viswall import ViswallClient
client = ViswallClient(base_url="https://viswall.example.com", token="jwt")
instances = client.instances.list()
client.firewall.create_rule(instance_id=1, name="Allow HTTPS", action="accept", dst_port=443)
```

**TypeScript SDK**

```bash
npm install @viswall/sdk
```

```typescript
import { ViswallClient } from '@viswall/sdk';
const client = new ViswallClient({ baseURL: 'https://viswall.example.com', token: 'jwt' });
const rules = await client.firewall.listRules(1);
```

**CLI**

```bash
pip install viswall-cli
viswall login --url https://viswall.example.com --username admin
viswall instances list
viswall firewall create --instance-id 1 --name "Allow HTTPS" --action accept --dst-port 443
```

---

## Development

### Backend

```bash
cd services/api-gateway
pip install -r requirements.txt
export DATABASE_URL="postgresql+asyncpg://viswall:viswall@localhost/viswall"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET_KEY="dev-secret-key"
uvicorn main:app --reload --host :: --port 8000
```

### Frontend

```bash
cd web-ui
npm install
npm run dev
```

### Testing

```bash
# Backend
cd services/api-gateway && python -m pytest tests/ -v --asyncio-mode=auto

# Frontend
cd web-ui && npm run type-check && npm run lint && npm run test:ci && npm run build

# Python SDK
cd sdk/python && python -m pytest tests/ -v && python -m ruff check viswall/ && python -m mypy viswall/

# TypeScript SDK
cd sdk/typescript && npm run type-check && npm run test && npm run build

# CLI
cd sdk/cli && python -m pytest tests/ -v && python -m ruff check viswall_cli/ && python -m mypy viswall_cli/
```

---

## License

MIT License

---

**Note**: The `source/` and `files/` directories contain the legacy PHP/Perl/C++ codebase from the original appliance. They are preserved for reference but are not used in the modern architecture.
