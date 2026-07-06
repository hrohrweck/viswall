# Ansible Deployment

Ansible playbooks for deploying Viswall across one or more hosts.

## Quick Start

1. Install Ansible on your control node:
   ```bash
   pip install ansible
   ```

2. Copy and customize the inventory:
   ```bash
   cd deployments/ansible
   cp inventory.yml inventory.production.yml
   # Edit inventory.production.yml with your host IPs and roles
   ```

3. Create a vault for secrets (recommended):
   ```bash
   ansible-vault create group_vars/vault.yml
   ```

4. Deploy the manager stack:
   ```bash
   ansible-playbook -i inventory.production.yml playbook.yml --tags manager
   ```

5. Deploy edge agents:
   ```bash
   ansible-playbook -i inventory.production.yml playbook.yml --tags agent
   ```

## Architecture

- **Manager nodes** (`viswall_role: manager`) run the central docker-compose stack:
  - PostgreSQL, Redis
  - API Gateway
  - Web UI
  - Prometheus + Grafana

- **Agent nodes** (`viswall_role: agent`) run a single service agent container:
  - `viswall_agent_type: firewall` — nftables, traffic shaping, policy routing
  - `viswall_agent_type: mail` — Exim, Courier, SpamAssassin, ClamAV
  - `viswall_agent_type: vpn` — WireGuard, IPsec, OpenVPN

## Inventory Example

```yaml
production:
  children:
    managers:
      hosts:
        viswall-manager-01:
          ansible_host: 192.168.1.10
          viswall_role: manager
    agents:
      hosts:
        viswall-edge-01:
          ansible_host: 192.168.1.20
          viswall_role: agent
          viswall_agent_type: firewall
```

## Variables

See `group_vars/all.yml` for common defaults. Override per-host or per-group as needed.

| Variable | Default | Description |
|----------|---------|-------------|
| `viswall_version` | `main` | Git branch/tag to deploy |
| `viswall_install_dir` | `/opt/viswall` | Installation path on target |
| `viswall_db_password` | _(set via ansible-vault)_ | PostgreSQL password |
| `viswall_jwt_secret` | _(set via ansible-vault)_ | JWT signing key |
| `viswall_gateway_url` | `http://manager-01:8000` | API gateway URL for agents |
| `viswall_instance_api_key` | _(set via ansible-vault)_ | Agent authentication key |
