# Implementation Plan: Viswall Remediation & Integration

This document outlines the step-by-step plan to address the functional and architectural gaps identified in the Viswall platform, moving it from a simulated environment to a fully-integrated distributed security appliance.

---

## Phase 1: Frontend Cleanups and Feature Gaps (Low-Risk / High-Value)

### Task 1.1: Centralize Traffic Shaping (QoS) API & Hooks
*   **Objective**: Standardize traffic shaping integration to match the repository's frontend patterns.
*   **Action**: 
    *   Move types from `web-ui/src/pages/TrafficShaping/index.tsx` (or adjacent local files) into `web-ui/src/types/index.ts`.
    *   Move API calls from `web-ui/src/pages/TrafficShaping/api.ts` into centralized TanStack Query hooks in `web-ui/src/hooks/useApi.ts`.
    *   Delete `web-ui/src/pages/TrafficShaping/api.ts` and update imports in the page component.
*   **Verification**: Run `npm run type-check` and `npm run lint` inside `web-ui`.

### Task 1.2: Implement NAT Rules Frontend UI & Hooks
*   **Objective**: Enable users to view, create, and manage network address translation rules.
*   **Action**:
    *   Add TypeScript schemas for NAT Rules to `web-ui/src/types/index.ts` mirroring `shared/schemas.py`.
    *   Add NAT CRUD hooks (`useNatRules`, `useCreateNatRule`, `useDeleteNatRule`) in `web-ui/src/hooks/useApi.ts`.
    *   Add a "NAT Rules" tab or a sub-page under Firewall. Implement a clean `DataTable` for viewing rules and forms/modals for adding/deleting them.
*   **Verification**: Verify UI visually and compile frontend without errors.

### Task 1.3: Add SOGo Groupware Toggle & UI to Mail Domains
*   **Objective**: Expose the backend's Groupware/SOGo capabilities on the frontend.
*   **Action**:
    *   Add Groupware hooks (`useGroupwareStatus`, `useToggleGroupware`, `useGroupwareStats`) to `web-ui/src/hooks/useApi.ts` mapping to `/groupware` routers.
    *   Update `MailDomainDetail.tsx` and `MailDomainCreate.tsx` to display a "Groupware (SOGo)" configuration section with a switch/toggle and a statistics dashboard card.
*   **Verification**: Ensure clean TypeScript compile.

---

## Phase 2: Gateway-to-Agent Integration (Core Backend Pipeline)

### Task 2.1: Establish Actual Agent Communication Channels
*   **Objective**: Replace mock gateway returns with real network calls to the service agents.
*   **Action**:
    *   Create an HTTP client utility (or Redis message queue publisher) inside `services/api-gateway/utils/agent_client.py`.
    *   Wire this client into `api-gateway/routers/firewall.py` to forward actual QoS rules and block/unblock requests to the `firewall-service` running at its configured URL/port.
*   **Verification**: Run gateway integration tests.

### Task 2.2: Add FastAPI Servers to Mail and VPN Agents
*   **Objective**: Enable `mail-service` and `vpn-service` to receive operational commands.
*   **Action**:
    *   Add lightweight FastAPI servers (similar to `firewall_agent.py`) inside `mail_agent.py` and `vpn_agent.py`.
    *   Implement HTTP endpoints for certificate generation, server control, configuration reloading, and queue flushing.
*   **Verification**: Start agents locally and test their HTTP endpoints using curl.

### Task 2.3: Wire Gateway to Mail & VPN Agents
*   **Objective**: Complete the management loop for Mail and VPN services.
*   **Action**:
    *   Refactor `api-gateway/routers/mail.py` and `api-gateway/routers/vpn.py` to forward actions (e.g., config reloads, client certificate creations, server restarts) directly to the newly exposed agent APIs instead of return mock success states.
*   **Verification**: Run suite of backend end-to-end tests.

---

## Phase 3: Client Parity (SDKs & CLI)

### Task 3.1: Complete Python & TypeScript SDKs
*   **Objective**: Achieve full resource parity with all 15 routers.
*   **Action**:
    *   Export updated openapi spec: `python scripts/export_openapi.py`.
    *   Add `dns`, `firewall_simulation`, and `llm_admin` resources to the Python and TS SDKs.
    *   Incorporate missing endpoints (bulk VPN client creation, audit resource logs, mail queue flushes) into SDK resource classes.
*   **Verification**: Run `npm run type-check` for TS SDK, and `pytest` / `mypy` for Python SDK.

### Task 3.2: Expand CLI Tooling
*   **Objective**: Expose all system domains via CLI commands.
*   **Action**:
    *   Add click commands for `vpn`, `mail`, `dns`, `routing`, and `assistant` into `sdk/cli/viswall_cli/commands/`.
    *   Connect commands to the Python SDK resources.
*   **Verification**: Run CLI test suite `pytest tests/` in `sdk/cli`.
