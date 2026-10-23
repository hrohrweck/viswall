#!/usr/bin/env python3
"""Set instance-1 capabilities and agent endpoints for the firewall/vpn rollout.

PATCHes ``/api/v1/instances/{id}`` with an admin JWT (``VISWALL_TOKEN``).  The
payload is a merge, never a replace: unknown capabilities and config keys
(notably ``version``) survive, ``agent_endpoints`` gains firewall/vpn/node
while keeping dns, and ``api_key`` is never read or written.  The PATCH route
exists in ``routers/instances.py``; 404/405/501 falls back to one transactional
SQL read-modify-write via ``DATABASE_URL``.

``--dry-run`` renders the payload from the todo-5 snapshot (no network);
``--self-test`` checks the merge invariants.  Live write::

  VISWALL_TOKEN=... python3 scripts/update_instance_1.py
"""
from __future__ import annotations

import argparse
import asyncio
import copy
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Mapping, Sequence

DESIRED_CAPABILITIES = ("mail", "dns", "firewall", "vpn")
# The gateway runs in the viswall bridge netns: 127.0.0.1 there is the
# container's own loopback, so dispatch targets the host via
# host.docker.internal (api-gateway has the host-gateway extra_host; the
# agents bind the host loopback unless the deployment overrides AGENT_HOST).
DESIRED_ENDPOINTS = {
    "firewall": "http://host.docker.internal:8081",
    "vpn": "http://host.docker.internal:8083",
    "node": "http://host.docker.internal:8085",
}

# Exact instance-1 row observed read-only in todo 5.  Used by --dry-run only.
FAKE_CAPABILITIES = ["mail", "firewall", "vpn", "dns"]
FAKE_CONFIG = {"agent_endpoints": {"dns": "http://dns-service:8082"}}

DEFAULT_API_URL = "https://viswall.webmasters.co.at/api/v1"


class UpdateError(RuntimeError):
    """Failure that must abort before or instead of a partial write."""


def build_patch(
    current_capabilities: Sequence[str],
    current_config: Mapping[str, Any],
) -> dict[str, Any]:
    """Merge the desired capabilities/endpoints into the current instance state.

    Pure function: neither argument is mutated.  Returns exactly the PATCH
    body (``{"capabilities": [...], "config": {...}}``), never ``api_key``.
    """
    if not isinstance(current_capabilities, list) or not all(
        isinstance(item, str) for item in current_capabilities
    ):
        raise UpdateError("instance.capabilities is not a JSON array of strings")
    if not isinstance(current_config, Mapping):
        raise UpdateError("instance.config is not a JSON object")

    capabilities = list(current_capabilities)
    for capability in DESIRED_CAPABILITIES:
        if capability not in capabilities:
            capabilities.append(capability)

    config = copy.deepcopy(dict(current_config))
    endpoints = config.get("agent_endpoints", {})
    if not isinstance(endpoints, Mapping):
        raise UpdateError("instance.config.agent_endpoints is not a JSON object")
    merged_endpoints = dict(endpoints)
    merged_endpoints.update(DESIRED_ENDPOINTS)
    config["agent_endpoints"] = merged_endpoints

    return {"capabilities": capabilities, "config": config}


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_self_test() -> None:
    """Tiny literal assertions for the merge contract (no network, no DB)."""
    capabilities = ["mail", "firewall", "vpn", "dns", "custom"]
    config: dict[str, Any] = {
        "version": 7,
        "agent_endpoints": {
            "dns": "http://dns-service:8082",
            "legacy": "http://old:9999",
        },
        "feature_flags": {"keep": True},
    }
    original_capabilities = list(capabilities)
    original_config = copy.deepcopy(config)

    patch = build_patch(capabilities, config)

    _check(set(patch) == {"capabilities", "config"}, "PATCH body keys changed")
    _check("api_key" not in patch, "PATCH body must not carry api_key")
    _check(patch["capabilities"][: len(capabilities)] == capabilities, "capability order/reuse broken")
    _check(patch["capabilities"] == capabilities, "no capability may be added or dropped")
    _check(patch["config"]["version"] == 7, "config.version was not preserved")
    _check(patch["config"]["feature_flags"] == {"keep": True}, "unknown config key was dropped")
    endpoints = patch["config"]["agent_endpoints"]
    _check(endpoints["dns"] == "http://dns-service:8082", "existing dns endpoint was replaced")
    _check(endpoints["legacy"] == "http://old:9999", "unknown endpoint was dropped")
    for name, url in DESIRED_ENDPOINTS.items():
        _check(endpoints[name] == url, f"{name} endpoint missing")
        _check(
            url.startswith("http://host.docker.internal:"),
            f"{name} endpoint must target the host via host.docker.internal",
        )
    _check(capabilities == original_capabilities, "input capabilities were mutated")
    _check(config == original_config, "input config was mutated")

    missing = build_patch(["custom"], {})
    _check(
        missing["capabilities"] == ["custom", "mail", "dns", "firewall", "vpn"],
        "missing capabilities were not appended in order",
    )
    _check(
        missing["config"] == {"agent_endpoints": dict(DESIRED_ENDPOINTS)},
        "endpoints were not created when config was empty",
    )

    second = build_patch(patch["capabilities"], patch["config"])
    _check(second == patch, "second run is not idempotent")
    third = build_patch(second["capabilities"], second["config"])
    _check(third == second, "third run is not idempotent")
    print(
        "self-test: version kept; dns+unknown keys kept; firewall/vpn/node added "
        "via host.docker.internal; rerun idempotent"
    )


class GatewayClient:
    """Minimal admin-JWT client for the two instance routes this script needs."""

    def __init__(self, base_url: str, token: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        """HTTP JSON request; returns (status, parsed-body) for HTTP errors too."""
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header("Authorization", f"Bearer {self.token}")
        request.add_header("Accept", "application/json")
        if data is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                return response.status, json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                parsed = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                parsed = raw.decode("utf-8", errors="replace")
            return exc.code, parsed
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise UpdateError(f"{method} {url} failed: {exc}") from exc

    def get_instance(self, instance_id: int) -> tuple[int, Any]:
        return self._request("GET", f"/instances/{instance_id}")

    def patch_instance(self, instance_id: int, payload: dict[str, Any]) -> tuple[int, Any]:
        return self._request("PATCH", f"/instances/{instance_id}", payload)


def _patch_via_sql(instance_id: int, database_url: str) -> bool:
    """Transactional read-modify-write fallback. Returns True when a row changed."""
    try:
        import asyncpg
    except ImportError as exc:  # pragma: no cover - only on a broken install
        raise UpdateError(
            "PATCH route unusable and asyncpg is not installed for the DATABASE_URL fallback"
        ) from exc

    dsn = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    async def _run() -> bool:
        conn = await asyncpg.connect(dsn, timeout=30)
        try:
            async with conn.transaction():
                row = await conn.fetchrow(
                    "SELECT capabilities, config FROM instances WHERE id = $1 FOR UPDATE",
                    instance_id,
                )
                if row is None:
                    raise UpdateError(f"instance {instance_id} not found")
                raw = row["capabilities"]
                capabilities = json.loads(raw) if isinstance(raw, str) else raw
                raw = row["config"]
                config = json.loads(raw) if isinstance(raw, str) else raw
                patch = build_patch(capabilities, config)
                if patch["capabilities"] == capabilities and patch["config"] == config:
                    return False
                await conn.execute(
                    "UPDATE instances"
                    " SET capabilities = $2::json, config = $3::json, updated_at = now()"
                    " WHERE id = $1",
                    instance_id,
                    json.dumps(patch["capabilities"]),
                    json.dumps(patch["config"]),
                )
                return True
        finally:
            await conn.close()

    return asyncio.run(_run())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance-id", type=int, default=1)
    parser.add_argument(
        "--api-url",
        default=os.environ.get("VISWALL_API_URL", DEFAULT_API_URL),
        help="api-gateway base URL including /api/v1 (default: %(default)s)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the exact PATCH body for the todo-5 snapshot; no network/write",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="assert merge invariants in-process and exit",
    )
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        print("SELF-TEST PASSED")
        return 0

    if args.dry_run:
        patch = build_patch(FAKE_CAPABILITIES, FAKE_CONFIG)
        print(f"DRY RUN: PATCH {args.api_url.rstrip('/')}/instances/{args.instance_id}")
        print(json.dumps(patch, indent=2))
        return 0

    token = os.environ.get("VISWALL_TOKEN", "").strip()
    if not token:
        print("error: VISWALL_TOKEN is not set (admin JWT required)", file=sys.stderr)
        return 2

    client = GatewayClient(args.api_url, token)
    try:
        status, current = client.get_instance(args.instance_id)
        if status in (401, 403):
            print(f"error: authentication failed (HTTP {status}); check VISWALL_TOKEN", file=sys.stderr)
            return 2
        if status != 200:
            print(
                f"error: GET {client.base_url}/instances/{args.instance_id} returned {status}: {current}",
                file=sys.stderr,
            )
            return 1
        if not isinstance(current, dict):
            raise UpdateError("instance GET did not return a JSON object")

        current_capabilities = current.get("capabilities", [])
        current_config = current.get("config", {})
        patch = build_patch(current_capabilities, current_config)
        if patch["capabilities"] == current_capabilities and patch["config"] == current_config:
            print(f"instance {args.instance_id} already up to date; no write performed")
            return 0

        status, body = client.patch_instance(args.instance_id, patch)
        if status == 200:
            print(f"updated instance {args.instance_id}: capabilities={patch['capabilities']}")
            print(f"agent_endpoints={patch['config']['agent_endpoints']}")
            return 0
        if status in (404, 405, 501):
            database_url = os.environ.get("DATABASE_URL", "").strip()
            if not database_url:
                raise UpdateError(
                    f"PATCH route unusable (HTTP {status}) and DATABASE_URL is not set"
                )
            changed = _patch_via_sql(args.instance_id, database_url)
            outcome = "updated" if changed else "already up to date (no change)"
            print(f"API PATCH unusable (HTTP {status}); SQL fallback: instance {args.instance_id} {outcome}")
            return 0
        print(f"error: PATCH returned {status}: {body}", file=sys.stderr)
        return 1
    except UpdateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
