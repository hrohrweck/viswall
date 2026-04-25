# viswall-cli

Command-line interface for the Viswall distributed security appliance platform.

## Installation

```bash
pip install viswall-cli
```

## Quick Start

```bash
# Login and save credentials
viswall login --url https://viswall.example.com --username admin

# Or use environment variables
export VISWALL_URL=https://viswall.example.com
export VISWALL_TOKEN=your-jwt-token
```

## Commands

### Authentication
```bash
viswall login --url <url> --username <user>          # Interactive login
viswall config-show                                   # Show current config
```

### Instances
```bash
viswall instances list                                # List all instances
viswall instances create <name> <hostname>            # Create instance
viswall instances get <id>                            # Get instance details
viswall instances delete <id> --yes                   # Delete instance
```

### Firewall
```bash
viswall firewall list --instance-id <id>              # List rules
viswall firewall create --instance-id <id> \
  --name "Allow HTTPS" --action accept --dst-port 443  # Create rule
viswall firewall delete <rule-id> --yes               # Delete rule
viswall firewall apply <instance-id>                  # Apply rules
```

### Users
```bash
viswall users list                                    # List users
viswall users create <username> <email> \
  --password <pwd> --role admin                       # Create user
```

### Metrics
```bash
viswall metrics latest <instance-id>                  # Latest metrics
viswall metrics overview                              # Global overview
```

## Global Options

All commands support:
- `--url, -u` — Viswall instance URL
- `--token, -t` — JWT authentication token
- `--format, -f` — Output format: `table` (default) or `json`
- `--config, -c` — Path to config file

## Configuration Priority

1. Command-line flags (`--url`, `--token`)
2. Environment variables (`VISWALL_URL`, `VISWALL_TOKEN`)
3. Config file (`~/.config/viswall/config.yaml`)

## Development

```bash
cd sdk/cli
pip install -e ".[dev]" -e ../python
python -m pytest tests/ -v
python -m ruff check viswall_cli/
python -m mypy viswall_cli/
```

## License

MIT
