"""FastAPI control surface for the Viswall firewall agent.

Ported from the former single-file agent with one behavioral change: every
endpoint except ``/health`` now requires the ``X-Instance-Key`` header to
match ``INSTANCE_API_KEY`` (constant-time compare) — this closes the
previously unauthenticated :8081 hole. ``main.py`` refuses to start the
process when the key is unset; if this module is imported directly without the
env var, the middleware answers 401 on everything except /health instead of
serving unauthenticated requests.

Todo 8 endpoint set (all behind the auth middleware; amended: no ``/interfaces``
here — the upstream node-agent owns interface management):

* ``POST /firewall/apply`` — body ``{interfaces, rules, nat_rules,
  routing_rules, qos}`` in the gateway contract
  (``utils/firewall_dispatch.py``). Pipeline: snapshot (todo 10, FIRST — the
  pre-apply undo point) → render + apply nft via the todo-7 renderer (its
  ``apply_ruleset`` validates with ``nft -c -f`` BEFORE deleting the table, so
  a failed render leaves the live table untouched) → idempotent policy routing
  (todo 13 ``apply_routing``) → per-interface QoS incl. classes (todo 11
  ``setup_qos``). Returns ``{applied, validation_mode, errors}``; an nft
  failure is a 500 carrying the exact ``nft -c`` error text.
* ``GET /firewall/status`` → ``{validation_mode, table_present,
  last_applied_at, nft_dump}`` where ``nft_dump`` is the parsed
  ``nft -j list table inet viswall`` output; an absent table is tolerated.
* ``POST /firewall/rollback`` → restores the newest todo-10 snapshot.
* ``/block`` + ``/unblock`` (todo-20 carryover) take a Pydantic **body**
  (``{ip, reason, timeout}`` / ``{ip}``) — the gateway sends a JSON body today
  and the old query-param signature 422'd.

Payload conversion (gateway row shape → renderer dataclasses): the gateway
emits DB-column names (``source_type/source_value``, ``service_ports`` …) and
no ``chain``; console rules are host-filter rules, so they land in the input
chain's user-rule section (after the mandatory accepts, per the todo-7
ordering invariant). ``service_ports`` ranges expand to one rule per port (up
to a documented cap) because the renderer takes a single ``destination_port``.
Rules tagged ``anti-spoof``/``internal-port`` in their name are forward-chain
concepts and get ``chain="forward"`` so the todo-7 tagged sections pick them
up instead of the built-in defaults.

Rollback mechanism (documented choice): if ``restore_firewall.sh`` is on PATH
the agent invokes it with ``--no-restart-docker`` (the agent runs inside
docker — restarting docker would kill the request mid-flight; the host-native
watchdog path is the one that restarts docker). Otherwise the agent restores
the snapshot's captured files directly: ``nft delete table inet viswall``
first (the -200 input hook must go before iptables-restore re-applies), then
``iptables-restore < rules.v4`` + ``ip6tables-restore < rules.v6`` — never an
``nft -f`` of the snapshot's full ruleset dump (that would duplicate docker's
tables) and never a docker/wg restart from inside the agent.

``ContentFilterManager`` from the old file was intentionally not ported: no
endpoint in the old agent and no later todo (7-14) references it — unreachable
dead code (squid config generation), documented here so the omission is
deliberate, not accidental.
"""

# allow: SIZE_OK — todo 8 mandates a single-file edit (api.py only, parallel
# workers own every other module); the payload conversion, the
# apply/status/rollback pipeline and the block-body models are all facets of
# the one endpoint contract this module owns.

from __future__ import annotations

import asyncio
import json
import os
import secrets
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from viswall_firewall_agent.nft import (
    NATRule,
    NFTablesManager,
    FirewallAction,
    FirewallRule,
)
from viswall_firewall_agent.qos import QoSValidationError, TrafficControlManager
from viswall_firewall_agent.routing import RoutingManager
from viswall_firewall_agent.snapshots import snapshot_state

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    from typing import List as TypingList

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

#: Agent state root (runtime state only — never firewall semantics).
STATE_DIR = os.getenv("STATE_DIR", "/var/lib/viswall-firewall")

#: Host-native restore script (todo 10). Rollback prefers it when on PATH.
RESTORE_SCRIPT = "restore_firewall.sh"

#: ``service_ports`` ranges expand to one rule per port up to this many ports;
#: a wider range renders protocol-only rather than exploding the ruleset.
_PORT_EXPANSION_CAP = 256

_SOURCE_TYPES = {"host", "network", "range"}


class FirewallApplyError(RuntimeError):
    """An /firewall/apply (or rollback) step failed; carries the exact text."""


def _validation_mode() -> bool:
    """Whether the renderer ran in pass-through validation mode."""
    return os.environ.get("VALIDATION_MODE") == "1"


# ---------------------------------------------------------------------------
# Gateway payload -> renderer dataclass conversion
# ---------------------------------------------------------------------------


def _parse_service_ports(raw: Any) -> List[int]:
    """Parse a gateway ``service_ports`` string into a port list.

    ``"22"`` → ``[22]``; ``"8000-8100"`` → 8000..8100; ``"22,443"`` → [22,
    443]. Empty/unparsable → ``[]``. Range expansion is capped at
    ``_PORT_EXPANSION_CAP`` ports: an entry that would expand further yields
    ``[]`` (the rule renders protocol-only instead of exploding the ruleset).
    """
    if raw is None:
        return []
    ports: List[int] = []
    for token in str(raw).split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            low_text, _, high_text = token.partition("-")
            try:
                low, high = int(low_text), int(high_text)
            except ValueError:
                continue
            if not (1 <= low <= high <= 65535):
                continue
            if high - low + 1 > _PORT_EXPANSION_CAP:
                return []
            ports.extend(range(low, high + 1))
            continue
        try:
            port = int(token)
        except ValueError:
            continue
        if 1 <= port <= 65535:
            ports.append(port)
    return ports


def _rule_chain(name: str) -> str:
    """Console rules default to the input chain; the forward-chain tags get
    placed in forward so the todo-7 tagged sections apply to them."""
    lowered = (name or "").lower()
    if "anti-spoof" in lowered or "internal-port" in lowered:
        return "forward"
    return "input"


def _rules_from_payload(entry: Dict[str, Any], index: int) -> List[FirewallRule]:
    """Convert one gateway FirewallRule payload dict into renderer objects.

    The gateway names differ from the agent dataclass (DB columns vs renderer
    fields) and carry no ``chain``. ``service_ports`` ranges expand to one
    rule per port so the single-``destination_port`` renderer stays exact.
    """
    try:
        name = entry["name"]
        base = {
            "id": entry.get("id", 0),
            "name": name,
            "chain": _rule_chain(name),
            "source": (
                entry.get("source_value")
                if entry.get("source_type") in _SOURCE_TYPES
                else None
            ),
            "destination": (
                entry.get("dest_value")
                if entry.get("dest_type") in _SOURCE_TYPES
                else None
            ),
            "protocol": entry.get("service_protocol") or None,
            "interface_in": entry.get("interface_in"),
            "interface_out": entry.get("interface_out"),
            "action": FirewallAction((entry.get("action") or "accept").lower()),
            "log": bool(entry.get("log_enabled")),
            "limit": entry.get("limit"),
            "order": int(entry.get("order_index") or 0),
            "anti_spoof": "anti-spoof" in (name or "").lower(),
        }
    except (TypeError, KeyError, ValueError) as exc:
        raise FirewallApplyError(f"invalid rule at index {index}: {exc}") from exc

    ports = _parse_service_ports(entry.get("service_ports"))
    if not ports:
        return [FirewallRule(**base, destination_port=None)]
    return [FirewallRule(**base, destination_port=port) for port in ports]


def _nat_from_payload(entry: Dict[str, Any], index: int) -> NATRule:
    """Convert one gateway NATRule payload dict into a renderer object.

    The renderer places rules by ``type`` (dnat → prerouting, snat →
    postrouting), so the missing ``chain`` is derived from the type. The
    single-``port`` renderer takes a lone port; a range/multi-port
    ``service_ports`` drops the port constraint (viswall NAT is unused in v1 —
    docker owns NAT — so this is a documented edge, not a correctness loss).
    """
    try:
        nat_type = (entry.get("type") or "snat").lower()
        ports = _parse_service_ports(entry.get("service_ports"))
        return NATRule(
            id=entry.get("id", 0),
            name=entry["name"],
            type=nat_type,
            chain="postrouting" if nat_type in ("snat", "masquerade") else "prerouting",
            source=entry.get("source_network"),
            destination=entry.get("dest_network"),
            to_source=entry.get("to_source"),
            to_destination=entry.get("to_destination"),
            protocol=entry.get("service_protocol") or None,
            port=ports[0] if len(ports) == 1 else None,
            interface=entry.get("interface"),
        )
    except (TypeError, KeyError, ValueError) as exc:
        raise FirewallApplyError(f"invalid nat rule at index {index}: {exc}") from exc


# ---------------------------------------------------------------------------
# Apply-state marker + nft error recovery
# ---------------------------------------------------------------------------


def _last_applied_path() -> Path:
    return Path(STATE_DIR) / "last_applied_at"


def _write_last_applied_at() -> None:
    """Record the successful-apply timestamp (best effort: the apply already
    succeeded; a lost marker must not turn success into failure)."""
    try:
        Path(STATE_DIR).mkdir(parents=True, exist_ok=True)
        _last_applied_path().write_text(
            datetime.now(timezone.utc).isoformat(), encoding="utf-8"
        )
    except OSError:
        pass


def _read_last_applied_at() -> Optional[str]:
    try:
        value = _last_applied_path().read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


async def _run_capture(
    binary: str, *args: str, input_bytes: Optional[bytes] = None
) -> Tuple[int, str, str]:
    """Run one subprocess; return (returncode, stdout, stderr) as text."""
    proc = await asyncio.create_subprocess_exec(
        binary,
        *args,
        stdin=asyncio.subprocess.PIPE if input_bytes is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate(input_bytes)
    return proc.returncode, stdout.decode(errors="replace"), stderr.decode(errors="replace")


async def _nft_validation_error() -> str:
    """Recover the exact nft error after a failed apply.

    ``NFTablesManager.apply_ruleset`` writes its config path before validating
    and only reports a bool, so re-running the check against that file is the
    only way to surface the exact ``nft -c`` stderr without editing nft.py.
    """
    try:
        rc, _, stderr = await _run_capture("nft", "-c", "-f", NFTablesManager.CONFIG_PATH)
    except OSError:
        return "nftables apply failed (nft unavailable)"
    if rc != 0 and stderr.strip():
        return f"nftables validation failed: {stderr.strip()}"
    return "nftables apply failed"


# ---------------------------------------------------------------------------
# Rollback helpers
# ---------------------------------------------------------------------------


def _newest_snapshot_dir() -> Optional[Path]:
    """Newest todo-10 snapshot dir (UTC timestamps sort lexicographically)."""
    root = Path(STATE_DIR) / "snapshots"
    if not root.is_dir():
        return None
    dirs = sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.name)
    return dirs[-1] if dirs else None


async def _rollback_via_script(snapshot: Path) -> None:
    """Restore via the host-native script, never restarting docker from the
    agent (the agent runs inside docker)."""
    rc, stdout, stderr = await _run_capture(
        RESTORE_SCRIPT, "--no-restart-docker", str(snapshot)
    )
    if rc != 0:
        raise FirewallApplyError(
            f"{RESTORE_SCRIPT} failed ({rc}): {(stderr or stdout).strip()}"
        )


async def _rollback_direct(snapshot: Path) -> List[str]:
    """Restore from the snapshot dir's captured files (no script on PATH).

    Order matches scripts/restore_firewall.sh: remove the viswall layer first
    (its -200 input hook would shadow iptables-restore), then re-apply the
    captured v4/v6 rules. Docker/wg restarts are intentionally absent — the
    agent must never restart docker mid-request; the host-native script owns
    those.
    """
    await _run_capture("nft", "delete", "table", "inet", "viswall")  # missing table tolerated
    restored: List[str] = []
    for name, binary in (("rules.v4", "iptables-restore"), ("rules.v6", "ip6tables-restore")):
        path = snapshot / name
        if not path.is_file():
            raise FirewallApplyError(f"snapshot artifact missing: {name}")
        rc, _, stderr = await _run_capture(binary, input_bytes=path.read_bytes())
        if rc != 0:
            raise FirewallApplyError(f"{binary} failed ({rc}): {stderr.strip()}")
        restored.append(name)
    return restored


class FirewallAgent:
    """Main firewall agent coordinating all components"""

    def __init__(self):
        self.nftables = NFTablesManager()
        self.tc = TrafficControlManager()
        self.routing = RoutingManager()

    async def deploy_firewall_config(
        self,
        interfaces: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
        nat_rules: List[Dict[str, Any]],
        routing_rules: List[Dict[str, Any]],
        qos_config: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Snapshot → render+apply nft → routing → QoS.

        Raises :class:`FirewallApplyError` (with the exact failure text) when
        the snapshot, the payload conversion or the nft apply fails — the nft
        failure mode is validate-before-apply: ``apply_ruleset`` returns False
        before ever touching the live table, so a bad render leaves the
        previous table intact. Routing/QoS failures are reported in the
        returned ``errors`` list instead.
        """
        # 1. Snapshot FIRST — the pre-apply undo point. snapshot_state blocks
        #    on subprocesses; run it off the event loop.
        try:
            await asyncio.to_thread(snapshot_state, STATE_DIR)
        except OSError as exc:
            raise FirewallApplyError(f"snapshot failed: {exc}") from exc

        # 2. Convert the gateway row payloads to renderer objects.
        try:
            fw_rules: List[FirewallRule] = []
            for index, raw in enumerate(rules or []):
                fw_rules.extend(_rules_from_payload(raw, index))
            nat = [_nat_from_payload(raw, index) for index, raw in enumerate(nat_rules or [])]
            ruleset = self.nftables.generate_ruleset(
                interfaces=interfaces or [], firewall_rules=fw_rules, nat_rules=nat
            )
        except FirewallApplyError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise FirewallApplyError(f"payload conversion failed: {exc}") from exc

        # 3. Render + apply (validate-before-apply lives in apply_ruleset).
        if not await self.nftables.apply_ruleset(ruleset):
            raise FirewallApplyError(await _nft_validation_error())
        _write_last_applied_at()

        # 4. Routing (todo 13 idempotent diff).
        errors: List[str] = []
        if not await self.routing.apply_routing(routing_rules or []):
            errors.extend(self.routing.errors)

        # 5. QoS per interface incl. classes (todo 11).
        for policy in qos_config or []:
            interface = str(policy.get("interface") or "?")
            try:
                ok = await self.tc.setup_qos(
                    interface=interface,
                    download_rate=policy["download_kbps"],
                    upload_rate=policy["upload_kbps"],
                    algorithm=policy.get("algorithm") or "cake",
                    classes=policy.get("classes"),
                )
            except QoSValidationError as exc:
                errors.append(f"qos {interface}: {exc}")
                continue
            except (KeyError, TypeError) as exc:
                errors.append(f"qos {interface}: invalid policy: {exc}")
                continue
            if not ok:
                errors.append(f"qos {interface}: setup failed")

        return {
            "applied": True,
            "validation_mode": _validation_mode(),
            "errors": errors,
        }

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive firewall statistics"""

        # Get nftables stats
        nft_stats = await self.nftables.get_stats()

        # Get conntrack info
        conntrack_count = 0
        try:
            proc = await asyncio.create_subprocess_exec(
                "conntrack",
                "-C",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            conntrack_count = int(stdout.decode().strip())
        except:
            pass

        return {
            "nftables": nft_stats,
            "connections": {
                "tracked": conntrack_count,
                "max": 262144,  # Default nf_conntrack_max
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def block_ip(self, ip: str, reason: str = "manual", timeout: str = "1h") -> bool:
        """Block an IP address"""
        return await self.nftables.add_to_blacklist(ip, timeout)

    async def unblock_ip(self, ip: str) -> bool:
        """Unblock an IP address"""
        return await self.nftables.remove_from_blacklist(ip)


# ============================================================================
# HTTP API Server (for API gateway → agent communication)
# ============================================================================

if FASTAPI_AVAILABLE:
    app = FastAPI(title="Viswall Firewall Agent", version="1.0.0")
    agent = FirewallAgent()

    INSTANCE_API_KEY = os.getenv("INSTANCE_API_KEY")

    class InstanceKeyAuthMiddleware:
        """Pure-ASGI middleware: /health is open for liveness probes, every
        other endpoint requires X-Instance-Key to match INSTANCE_API_KEY."""

        def __init__(self, app, instance_api_key: Optional[str]):
            self.app = app
            self.instance_api_key = instance_api_key

        async def __call__(self, scope, receive, send):
            if scope["type"] != "http" or scope["path"] == "/health":
                await self.app(scope, receive, send)
                return

            provided = ""
            for name, value in scope["headers"]:
                if name == b"x-instance-key":
                    provided = value.decode("latin-1")
                    break

            if self.instance_api_key is None or not secrets.compare_digest(
                provided, self.instance_api_key
            ):
                response = JSONResponse(
                    status_code=401, content={"detail": "invalid instance key"}
                )
                await response(scope, receive, send)
                return

            await self.app(scope, receive, send)

    app.add_middleware(InstanceKeyAuthMiddleware, instance_api_key=INSTANCE_API_KEY)

    class FirewallApplyRequest(BaseModel):
        interfaces: TypingList[Dict[str, Any]] = []
        rules: TypingList[Dict[str, Any]] = []
        nat_rules: TypingList[Dict[str, Any]] = []
        routing_rules: TypingList[Dict[str, Any]] = []
        qos: Optional[TypingList[Dict[str, Any]]] = None

    class BlockRequest(BaseModel):
        ip: str
        reason: Optional[str] = "manual"
        timeout: Optional[str] = "1h"

    class UnblockRequest(BaseModel):
        ip: str

    class QoSApplyRequest(BaseModel):
        interface: str
        algorithm: str
        download_kbps: int
        upload_kbps: int
        classes: TypingList[dict] = []

    class QoSClearRequest(BaseModel):
        interface: str

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "firewall-agent"}

    @app.post("/firewall/apply")
    async def api_firewall_apply(request: FirewallApplyRequest):
        try:
            result = await agent.deploy_firewall_config(
                interfaces=request.interfaces,
                rules=request.rules,
                nat_rules=request.nat_rules,
                routing_rules=request.routing_rules,
                qos_config=request.qos,
            )
        except FirewallApplyError as exc:
            raise HTTPException(status_code=500, detail=str(exc))
        return result

    @app.get("/firewall/status")
    async def api_firewall_status():
        table_present = False
        nft_dump: Optional[Dict[str, Any]] = None
        try:
            rc, stdout, _ = await _run_capture(
                "nft", "-j", "list", "table", "inet", "viswall"
            )
        except OSError:
            rc, stdout = 1, ""
        if rc == 0:
            table_present = True
            try:
                nft_dump = json.loads(stdout)
            except json.JSONDecodeError:
                nft_dump = None
        return {
            "validation_mode": _validation_mode(),
            "table_present": table_present,
            "last_applied_at": _read_last_applied_at(),
            "nft_dump": nft_dump,
        }

    @app.post("/firewall/rollback")
    async def api_firewall_rollback():
        snapshot = _newest_snapshot_dir()
        if snapshot is None:
            raise HTTPException(status_code=500, detail="no snapshot available to roll back to")
        try:
            if shutil.which(RESTORE_SCRIPT):
                await _rollback_via_script(snapshot)
                return {
                    "restored": True,
                    "mechanism": RESTORE_SCRIPT,
                    "restored_from": str(snapshot),
                    "restored_artifacts": [
                        "rules.v4",
                        "rules.v6",
                        "netplan/",
                        "wg-quick@client restart (docker restart skipped via --no-restart-docker)",
                    ],
                }
            restored = await _rollback_direct(snapshot)
            return {
                "restored": True,
                "mechanism": "direct (snapshot files)",
                "restored_from": str(snapshot),
                "restored_artifacts": restored + ["nft: table inet viswall removed"],
            }
        except (FirewallApplyError, OSError) as exc:
            raise HTTPException(status_code=500, detail=f"rollback failed: {exc}")

    @app.post("/qos/apply")
    async def api_apply_qos(request: QoSApplyRequest):
        try:
            ok = await agent.tc.setup_qos(
                interface=request.interface,
                download_rate=request.download_kbps,
                upload_rate=request.upload_kbps,
                algorithm=request.algorithm,
                classes=request.classes,
            )
        except QoSValidationError as e:
            raise HTTPException(status_code=422, detail=str(e))
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to apply QoS")
        return {
            "success": True,
            "interface": request.interface,
            "algorithm": request.algorithm,
        }

    @app.post("/qos/clear")
    async def api_clear_qos(request: QoSClearRequest):
        try:
            await agent.tc._run_tc(["qdisc", "del", "dev", request.interface, "root"])
            return {"success": True, "interface": request.interface}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to clear QoS: {e}")

    @app.get("/qos/stats/{interface}")
    async def api_qos_stats(interface: str):
        # Contract: stats.queues is a list of {name, bytes, packets, dropped,
        # rate} (mapped by the gateway into QoSQueueStats) and stats.raw is the
        # literal `tc -s` text for advanced display.
        stats = await agent.tc.get_stats(interface)
        return {
            "interface": interface,
            "stats": {
                "queues": stats.get("queues", []),
                "raw": stats.get("raw", ""),
            },
        }

    @app.get("/stats")
    async def api_system_stats():
        return await agent.get_system_stats()

    @app.post("/block")
    async def api_block_ip(request: BlockRequest):
        ok = await agent.block_ip(request.ip, request.reason, request.timeout)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to block IP")
        return {"success": True, "ip": request.ip}

    @app.post("/unblock")
    async def api_unblock_ip(request: UnblockRequest):
        ok = await agent.unblock_ip(request.ip)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to unblock IP")
        return {"success": True, "ip": request.ip}
