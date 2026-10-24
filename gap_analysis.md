# Viswall Backend Gap Analysis

Last reconciled 2026-10-24 with the executed firewall migration (todo 47).

## 1. API Gateway Routers (`services/api-gateway/routers/`)

**Documentation Mismatch**: `AGENTS.md` lists `auth, firewall, vpn, mail, metrics, routing, audit, assistant`. The directory also contains routers that are not in that line: `dhcp.py`, `dns.py`, `groupware.py`, `instances.py`, `llm_admin.py`, `users.py`, and `firewall_simulation.py`.

**Implementation Status (corrected):**

*   **`firewall.py`**: **REAL dispatch.** `POST /firewall/apply/{id}` queues `reload_firewall`, which calls `apply_firewall_config` and posts the composed payload to the firewall agent at `/firewall/apply`. Rule, NAT and routing mutations trigger the same path. QoS apply/clear/stats, IP block/unblock, stats, agent status and rollback all call the agent over `utils/agent_client.py`; they are no longer mocked. Rollback returns the agent's **409** after `COMMIT` (see `FIREWALL_MIGRATION_PLAN.md` §7.0).
*   **`routing.py`**: **REAL.** `apply_routing` calls `apply_firewall_config`; `RoutingRule` rows ride in the firewall dispatch payload.
*   **`network.py`**: **REAL but fail-closed for the imported inventory.** `GET /interfaces`, refresh and `POST /interfaces/apply` dispatch to the node-agent. Guardrail 4 (`check_wan_guardrails`) refuses any desired interface absent from the host netplan files; the console sends all 65 imported rows (only `enp0s31f6` is in netplan), so "Apply to Host" returns 400 until the payload is filtered or base netplan entries exist. `InterfaceApplyRequest` has no `try_mode` field (the gateway reads `getattr(..., False)`), so the console cannot request the SSH-safe `netplan try` path.
*   **`vpn.py`**: **REAL for server lifecycle.** Start/stop/restart and client disconnect dispatch to the VPN agent; the live stop/start roundtrip and tunnel-carrying proof were verified in todo 42. Some credential helpers remain stubs (e.g. OpenVPN client certificates).
*   **`mail.py`**: Background actions (DKIM generation, config reload, maildir creation) are still queued/no-op; `mail-service` remains a single module without an API server or queue listener.
*   **`assistant.py`**: Conversation management still returns placeholder data ("Would fetch from database"); the LLM-backed analysis endpoints call the configured provider.
*   **`audit.py` / `metrics.py`**: These now query the database. Metrics no longer simulate random data: `metrics_collector.py` reads real host telemetry via psutil (with `/host/proc` bind-mounted read-only), and the dashboard/overview endpoints aggregate stored rows.

## 2. Models and Schemas (`shared/models.py` & `shared/schemas.py`)

*   **Alignment**: Excellent. Both files are comprehensive (`models.py` is 1052 lines, `schemas.py` is 1636 lines).
*   They cover all domains present in the routers, including the undocumented ones (e.g., `DHCPServer`, `DNSZone`, `LLMProvider`, `QoSPolicy`, `Instance`).
*   There are no missing models or schemas for the existing API endpoints.
*   Known schema gap: `InterfaceApplyRequest` exposes only `force`; `try_mode` is read defensively with `getattr`, so the console's SSH-safe netplan path is unreachable until the field is added.

## 3. Service Agents (`firewall-service`, `mail-service`, `vpn-service`, `node-agent`)

**Structure**: `firewall-service` and `vpn-service` are now packages (`viswall_firewall_agent/`, `viswall_vpn_agent/`) with `api.py`, `heartbeat.py` and domain modules; both expose a FastAPI server that the gateway calls. `mail-service` remains a single module without an API server. `node-agent` is a host-network agent (`pid: host`, privileged) with interface discovery, live apply and netplan persistence.

**Implementation State:**

*   **`firewall-service`**: Real nftables apply/rollback, snapshots, QoS, routing, block/unblock and status. `apply_ruleset` validates in a throwaway netns (`unshare -n nft -c -f`), keeps `nftables.conf.last-good`, and returns **409** on rollback after `COMMIT`.
*   **`vpn-service`**: Real WireGuard client management (`wg_client.py`), with `.viswall-backup` before every write and `wg-quick@client` as the single lifecycle owner. The live stop/start roundtrip was verified in todo 42.
*   **`node-agent`**: Real interface discovery and netlink apply. It needs `network_mode: host`, `pid: host`, `privileged: true` (CAP_SYS_ADMIN for `nsenter`/`netplan try`) and `NODE_INSTANCE_ID` / `NODE_API_KEY`; without them `/interfaces` returns 503 (fix merged as PR #79).
*   **`mail-service`**: Core Exim/ClamAV/SpamAssassin logic exists, but LLM classification helpers still `pass` and the service has no API server or message-queue listener.

## 4. Missing Endpoints, Unimplemented Functions, and Design Mismatches

*   **The old communication gap is closed for firewall, VPN and node management.** The gateway dispatches through `utils/agent_client.py` and `Instance.config["agent_endpoints"]` (`firewall`/`vpn`/`node` on `host.docker.internal:8081/8083/8085`). Mail remains the exception: there is no API/queue listener, and gateway mail actions are queued/no-op.
*   **Interface apply is real but unusable from the UI with the imported inventory.** The console sends every row; guardrail 4 refuses the whole plan because Docker-owned and tunnel interfaces are absent from netplan. This is safe (fail-closed) but needs payload filtering or base netplan entries.
*   **Metrics Collection**: Fixed. `metrics_collector.py` reads real host telemetry (psutil, `/host/proc`) instead of random variation.
*   **Documentation Gap**: `AGENTS.md` has been updated for the router list and the production agent topology (firewall/vpn enabled, node-agent host-network, Docker coexistence, post-cutover rollback facts). Keep it in sync with future changes.
