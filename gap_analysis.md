# Viswall Backend Gap Analysis

## 1. API Gateway Routers (`services/api-gateway/routers/`)
**Documentation Mismatch**: `AGENTS.md` lists `auth, firewall, vpn, mail, metrics, routing, audit, assistant`. However, the directory contains several additional routers that are not documented: `dhcp.py`, `dns.py`, `groupware.py`, `instances.py`, `llm_admin.py`, `users.py`, and `firewall_simulation.py`.

**Implementation Status**:
While CRUD operations (database interactions) are generally well-implemented across the routers, the actual operational endpoints that should communicate with the service agents are heavily mocked or unimplemented:
*   **`firewall.py`**: QoS endpoints (`apply_qos_policy`, `clear_qos_on_interface`, `fetch_qos_stats_from_agent`), IP blocking (`block_ip`, `unblock_ip`), stats (`get_firewall_stats`), and background tasks (`reload_firewall`) return mocked data or use `pass`.
*   **`mail.py`**: Background tasks (`generate_dkim_keys`, `reload_mail_config`, `create_maildir`) use `pass`.
*   **`vpn.py`**: Server actions (`start_server`, `stop_server`, `restart_server`), client actions (`regenerate_client_credentials`, `disconnect_client`), and `initialize_site_to_site` return mocked success responses.
*   **`assistant.py`**: Conversation management (`list_conversations`, `get_conversation`, `delete_conversation`) and `get_assistant_capabilities` return mocked data.
*   **`audit.py`**: `get_audit_summary` returns mocked data.
*   **`metrics.py`**: `get_dashboard_data` and `get_global_overview` return mocked data.
*   **`routing.py`**: `apply_routing` returns a mocked response.
*   **`dhcp.py` & `dns.py`**: `server_action`, `sign_zone`, and `unsign_zone` return mocked responses.
*   **`groupware.py`**: `get_groupware_status` and `get_groupware_stats` return mocked responses.
*   **`llm_admin.py`**: `test_llm_provider` returns a mocked response.

## 2. Models and Schemas (`shared/models.py` & `shared/schemas.py`)
*   **Alignment**: Excellent. Both files are comprehensive (`models.py` is 1052 lines, `schemas.py` is 1636 lines).
*   They cover all domains present in the routers, including the undocumented ones (e.g., `DHCPServer`, `DNSZone`, `LLMProvider`, `QoSPolicy`, `Instance`).
*   There are no missing models or schemas for the existing API endpoints.

## 3. Service Agents (`firewall-service`, `mail-service`, `vpn-service`)
**Line Counts**: `AGENTS.md` claims 1,223 lines for firewall, 902 for mail, and 573 for vpn. Actual counts are slightly higher: 1306, 904, and 612 respectively.

**Implementation State**:
*   **`firewall-service`**: Mostly functional core logic (nftables, tc). It **does** expose a FastAPI server (`app = FastAPI(...)`) at the bottom of the file to receive commands, but the API gateway does not currently call it.
*   **`mail-service`**: Mostly functional core logic (Exim, ClamAV, SpamAssassin). However, LLM classification methods (`_classify_anthropic`, `_classify_local`) use `pass`. **Crucially, it lacks an API server or message queue listener**; the `main()` function is just a dummy stub.
*   **`vpn-service`**: Mostly functional core logic (WireGuard, IPsec, OpenVPN). However, some methods like `generate_client_certificate` for OpenVPN are stubs returning dummy strings. Like the mail service, **it lacks an API server or message queue listener**; the `main()` function is a dummy stub.

## 4. Missing Endpoints, Unimplemented Functions, and Design Mismatches
*   **The Communication Gap (Major Design Mismatch)**: The biggest architectural gap is the lack of actual communication between the API gateway and the service agents. The API gateway mocks the agent calls or uses `pass`, and the mail/vpn agents don't even have a mechanism (API/queue) to receive commands.
*   **Metrics Collection**: `services/api-gateway/metrics_collector.py` simulates metrics with random variation instead of querying the agents via HTTP/gRPC as intended.
*   **Documentation Gap**: `AGENTS.md` needs to be updated to reflect the additional routers (DHCP, DNS, etc.) and the actual state of the service agents (that they are not fully wired up to the gateway yet).
