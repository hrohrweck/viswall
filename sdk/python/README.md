# Viswall Python SDK

A resource-oriented Python SDK for the [Viswall](https://github.com/hrohrweck/viswall) distributed security appliance platform.

## Installation

```bash
pip install viswall-sdk
```

## Quick Start

```python
from viswall import ViswallClient

# Initialize client
client = ViswallClient(
    base_url="https://viswall.example.com",
    token="your-jwt-token"
)

# Or login first
result = client.auth.login("admin", "password")
client.token = result["access_token"]

# List instances
instances = client.instances.list()
for instance in instances:
    print(f"{instance['name']}: {instance['status']}")

# Create a firewall rule
client.firewall.create_rule(
    instance_id=1,
    name="Allow HTTPS",
    action="accept",
    protocol="tcp",
    dst_port=443
)

# Create a mail domain
domain = client.mail.create_domain(
    instance_id=1,
    domain="example.com",
    llm_enabled=True
)

# Close connection
client.close()
```

## Resource API

The SDK provides resource-oriented access to all Viswall APIs:

### Auth
```python
client.auth.me()
client.auth.login(username, password)
```

### Instances
```python
client.instances.list()
client.instances.create(name="edge-01", hostname="10.0.0.10")
client.instances.get(instance_id)
client.instances.update(instance_id, status="maintenance")
client.instances.delete(instance_id)
```

### Firewall
```python
client.firewall.list_rules(instance_id)
client.firewall.create_rule(instance_id, name="Allow SSH", action="accept", dst_port=22)
client.firewall.apply_rules(instance_id)
client.firewall.list_interfaces(instance_id)
```

### Mail
```python
client.mail.list_domains(instance_id)
client.mail.create_domain(instance_id, domain="example.com")
client.mail.list_users(domain_id)
client.mail.create_user(domain_id, username="john")
```

### VPN
```python
client.vpn.list_servers(instance_id)
client.vpn.create_server(instance_id, protocol="wireguard")
client.vpn.list_clients(server_id)
client.vpn.get_client_config(client_id)
```

### Routing
```python
client.routing.list_rules(instance_id)
client.routing.create_rule(instance_id, ...)
```

### Metrics
```python
client.metrics.get_latest(instance_id)
client.metrics.query(instance_id, metric_type="cpu_percent")
```

### Audit
```python
client.audit.list_logs(limit=100)
client.audit.get_instance_logs(instance_id)
```

### Users
```python
client.users.list()
client.users.create(username, email, password)
```

### Assistant
```python
client.assistant.chat("How do I block port 22?")
client.assistant.suggest_firewall_rule("Allow HTTPS traffic")
```

### Groupware
```python
client.groupware.get_status(domain_id)
client.groupware.enable(domain_id)
```

## Error Handling

```python
from viswall import ViswallClient, AuthenticationError, NotFoundError, ViswallAPIError

client = ViswallClient(base_url="https://viswall.example.com", token="jwt")

try:
    client.instances.get(999)
except NotFoundError:
    print("Instance not found")
except AuthenticationError:
    print("Invalid or expired token")
except ViswallAPIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `base_url` | Viswall instance URL | Required |
| `token` | JWT authentication token | None |
| `timeout` | Request timeout in seconds | 30.0 |

## Development

```bash
cd sdk/python
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
