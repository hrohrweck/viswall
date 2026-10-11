# Viswall Node Agent

Runs on the appliance host in a container that **shares the host network
namespace** and holds `NET_ADMIN`, so it can discover and reconfigure the
host's real interfaces. Used by the viswall console for host interface
management (Metrics are collected separately by the api-gateway).

## Endpoints

| Method | Path                | Auth              | Purpose                                        |
| ------ | ------------------- | ----------------- | ---------------------------------------------- |
| GET    | `/health`           | none              | liveness probe                                 |
| GET    | `/interfaces`       | `X-Instance-Key`  | live interface + default-route state           |
| POST   | `/interfaces/apply` | `X-Instance-Key`  | apply desired interface config (live + netplan) |

## Apply semantics

- Changes are **planned first**; only differences to live state run.
- A plan that touches the interface carrying the default route (usually
  the management connection) or the default route itself is refused with
  HTTP 409 unless `force: true`.
- Live changes use iproute2 (`ip addr/link/route`). Static addresses,
  MTU, link state and the default route apply immediately; DHCP
  interfaces are rendered as `dhcp4: true` and take effect at next boot
  or `netplan apply`.
- Desired state is persisted to `/etc/netplan/60-viswall.yaml`
  (atomic write, mode 0600) so it survives reboots. If the mount is
  missing, the apply still succeeds live and reports persistence as
  skipped.

## Configuration (environment)

| Variable            | Default             | Purpose                                   |
| ------------------- | ------------------- | ----------------------------------------- |
| `GATEWAY_URL`       | —                   | gateway base URL (enables heartbeat)      |
| `INSTANCE_ID`       | —                   | viswall instance id (enables heartbeat)   |
| `INSTANCE_API_KEY`  | —                   | instance API key (auth + heartbeat)       |
| `HEARTBEAT_INTERVAL`| `30`                | heartbeat cadence (seconds)               |
| `AGENT_PORT`        | `8085`              | control API port                          |
| `NETPLAN_DIR`       | `/etc/netplan`      | host netplan dir (rw mount); empty disables persistence |
| `NETPLAN_FILE`      | `60-viswall.yaml`   | file name used inside `NETPLAN_DIR`       |
| `IP_BINARY`         | `ip`                | iproute2 binary path                      |

## Running (docker-compose)

See the `node-agent` service in `deployments/docker/docker-compose.yml`.
`GATEWAY_URL` must point at the host-published gateway port
(`http://127.0.0.1:8010` in the default compose stack) because a
host-network container cannot resolve compose service names.

> **Note**: netplan file conflicts — make sure no other netplan file on
> the host configures the same interfaces; the viswall file wins by
> lexicographic order for duplicated keys.
