"""Idempotent, tagged policy routing for the Viswall firewall agent.

Ported from the former single-file agent (``RoutingManager``) and then made
desired-state driven (todo 13).  ``apply_routing`` renders the desired
``ip rule`` / ``ip route`` state, reads the live state (``ip -j rule`` and
``ip -j route show table all``), and mutates only the delta.  Re-applying the
same payload therefore produces **zero** mutation commands instead of the
historical duplicate-rule drift.

Every object viswall creates carries two deterministic ownership tags:

* ``protocol 30`` on rules and ``proto 30`` on routes (the ``ip`` protocol
  field — 30 is unassigned in ``/etc/iproute2/rt_protos``; it is the u8-safe
  equivalent of the plan's ``0x1fe`` mark idea, which does not fit the
  kernel's 8-bit protocol field), and
* a lookup table named ``vw-table-<number>`` registered in
  ``/etc/iproute2/rt_tables`` (path configurable for tests).

Ownership is therefore discoverable from the live kernel state alone: any
rule/route with ``protocol 30`` or a ``vw-table-*`` table belongs to viswall
and may be removed when it is no longer in the payload (``rollback`` /
cleanup uses the same predicate).  Reserved tables (``local``/``main``/
``default``/``unspec``) are never renamed and a default route in ``main`` is
never created or removed — the host's default route and the WireGuard
``client`` route are out of scope.
"""

import asyncio
import ipaddress
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

TAG_PROTOCOL = 30
TABLE_PREFIX = "vw-table-"
RESERVED_TABLES = frozenset({0, 253, 254, 255})
RESERVED_NAMES = {"unspec": 0, "default": 253, "main": 254, "local": 255}
TableId = Union[int, str]


@dataclass
class RoutingRule:
    id: int
    name: str
    source: Optional[str] = None
    destination: Optional[str] = None
    table: int = 254  # Main routing table
    gateway: Optional[str] = None
    interface: Optional[str] = None
    mark: Optional[int] = None  # fwmark for policy routing
    priority: int = 100


@dataclass(frozen=True)
class _Rule:
    priority: int
    table: TableId
    source: Optional[str] = None
    destination: Optional[str] = None
    mark: Optional[int] = None
    interface: Optional[str] = None


@dataclass(frozen=True)
class _Route:
    destination: str
    table: TableId
    gateway: Optional[str] = None
    interface: Optional[str] = None
    source: Optional[str] = None
    metric: Optional[int] = None


def _prefix(value: Any) -> Optional[str]:
    """Normalise a match prefix; ``all``/empty means "no selector"."""
    if value in (None, "", "all"):
        return None
    return str(ipaddress.ip_network(str(value), strict=False))


def _live_prefix(address: Optional[str], length: Optional[int]) -> Optional[str]:
    if not address or address == "all":
        return None
    if length is None:
        return str(ipaddress.ip_network(address, strict=False))
    return str(ipaddress.ip_network(f"{address}/{length}", strict=False))


def _route_prefix(value: Any) -> str:
    text = str(value or "default")
    if text in ("default", "0.0.0.0/0", "::/0"):
        return "default"
    return str(ipaddress.ip_network(text, strict=False))


def _mark(value: Any) -> Optional[int]:
    if value in (None, "", 0, "0"):
        return None
    if isinstance(value, int):
        return value
    return int(str(value).split("/")[0], 0)


def _table(value: Any, default: int = 254) -> TableId:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    text = str(value)
    if text.startswith(TABLE_PREFIX):
        try:
            return int(text[len(TABLE_PREFIX):])
        except ValueError:
            return text
    if text.isdigit():
        return int(text)
    return RESERVED_NAMES.get(text, text)


def _owned(entry: Dict[str, Any]) -> bool:
    if str(entry.get("protocol")) == str(TAG_PROTOCOL):
        return True
    table = entry.get("table")
    return isinstance(table, str) and table.startswith(TABLE_PREFIX)


class RoutingManager:
    """Desired-state policy routing with deterministic viswall tags."""

    RT_TABLES_PATH = "/etc/iproute2/rt_tables"

    def __init__(
        self,
        *,
        netns: Optional[str] = None,
        rt_tables_path: Optional[str] = None,
        dry_run: bool = False,
        runner: Optional[Any] = None,
    ) -> None:
        self.rt_tables_path = rt_tables_path or self.RT_TABLES_PATH
        self.dry_run = dry_run
        self.runner = runner
        self._ip = ["ip", "netns", "exec", netns, "ip"] if netns else ["ip"]
        self._rt_tables: Dict[int, str] = {}
        # Observable audit trails (used by the no-mutation smoke check).
        self.mutations: List[List[str]] = []
        self.file_mutations: List[str] = []
        self.errors: List[str] = []

    # -- live state -------------------------------------------------------

    async def _exec(self, args: Sequence[str]) -> Tuple[int, str, str]:
        command = [*self._ip, *args]
        if self.runner is not None:
            return await self.runner(command)
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout.decode(), stderr.decode()

    async def _json(self, args: Sequence[str]) -> List[Dict[str, Any]]:
        rc, stdout, stderr = await self._exec(["-j", *args])
        if rc != 0:
            self.errors.append(f"ip -j {' '.join(args)} failed ({rc}): {stderr.strip()}")
            return []
        try:
            data = json.loads(stdout or "[]")
        except json.JSONDecodeError as exc:
            self.errors.append(f"ip -j {' '.join(args)} returned invalid JSON: {exc}")
            return []
        return data if isinstance(data, list) else []

    async def _live_rules(self) -> List[Dict[str, Any]]:
        return await self._json(["rule"])

    async def _live_routes(self) -> List[Dict[str, Any]]:
        return await self._json(["route", "show", "table", "all"])

    # -- iproute2 table name registry ------------------------------------

    def _read_rt_tables(self) -> List[str]:
        try:
            with open(self.rt_tables_path, "r") as handle:
                return handle.readlines()
        except OSError:
            return []

    async def _ensure_table(self, number: TableId) -> bool:
        """Register ``number`` as ``vw-table-<number>`` exactly once."""
        if not isinstance(number, int) or number in RESERVED_TABLES:
            return True
        name = f"{TABLE_PREFIX}{number}"
        for line in self._read_rt_tables():
            fields = line.split()
            if len(fields) >= 2 and fields[0].isdigit() and int(fields[0]) == number:
                self._rt_tables[number] = fields[1]
                return True
        try:
            with open(self.rt_tables_path, "a") as handle:
                handle.write(f"{number} {name}\n")
        except OSError as exc:
            self.errors.append(f"could not register {name}: {exc}")
            return False
        self._rt_tables[number] = name
        self.file_mutations.append(f"{number} {name}")
        return True

    async def add_routing_table(self, name: str, number: int) -> bool:
        """Idempotently register a named routing table (legacy signature)."""
        for line in self._read_rt_tables():
            fields = line.split()
            if len(fields) >= 2 and fields[1] == name:
                return True
        try:
            with open(self.rt_tables_path, "a") as handle:
                handle.write(f"{number} {name}\n")
        except OSError as exc:
            self.errors.append(f"could not register {name}: {exc}")
            return False
        self._rt_tables[number] = name
        self.file_mutations.append(f"{number} {name}")
        return True

    def _table_name(self, table: TableId) -> str:
        if isinstance(table, str):
            return table
        if table in RESERVED_TABLES:
            return {0: "unspec", 253: "default", 254: "main", 255: "local"}[table]
        return self._rt_tables.get(table, f"{TABLE_PREFIX}{table}")

    # -- desired-state parsing -------------------------------------------

    @staticmethod
    def _as_dict(entry: Any) -> Dict[str, Any]:
        if isinstance(entry, RoutingRule):
            return {
                "source": entry.source,
                "destination": entry.destination,
                "table": entry.table,
                "gateway": entry.gateway,
                "interface": entry.interface,
                "mark": entry.mark,
                "priority": entry.priority,
            }
        return dict(entry) if isinstance(entry, dict) else {}

    def _desired(self, routing_rules: Optional[Sequence[Any]]) -> Tuple[List[_Rule], List[_Route]]:
        rules: List[_Rule] = []
        routes: List[_Route] = []
        for index, raw in enumerate(routing_rules or []):
            entry = self._as_dict(raw)
            if not entry or entry.get("enabled", True) is False:
                continue
            try:
                kind = entry.get("kind")
                table = _table(entry.get("table", 254))
                # F2 MINOR #12: a malformed priority must surface as a
                # per-rule error in ``errors`` (surfaced by the apply
                # response), never as an unhandled ValueError -> 500.
                priority = int(entry.get("priority", entry.get("order_index", 100)) or 100)
                source = _prefix(entry.get("source", entry.get("source_network")))
                destination = _prefix(entry.get("destination", entry.get("dest_network")))
                inbound = entry.get("inbound_interface") or entry.get("iif")
                outbound = entry.get("outbound_interface") or entry.get("interface")
                interface = inbound or entry.get("interface")
                mark = _mark(entry.get("mark"))
                gateway = entry.get("gateway")
                metric = entry.get("metric")
            except (ValueError, TypeError) as exc:
                self.errors.append(f"routing rule {index}: {exc}")
                continue

            if kind == "route":
                routes.append(
                    _Route(
                        destination=_route_prefix(
                            entry.get("route_destination") or entry.get("destination") or "default"
                        ),
                        table=table,
                        gateway=gateway,
                        interface=outbound,
                        source=entry.get("route_source") or source,
                        metric=metric,
                    )
                )
                continue

            matched = any((source, destination, mark, interface))
            if kind is None and gateway and table not in RESERVED_TABLES:
                # A matched policy entry with a next hop also owns the route
                # its lookup table uses (never table main).
                routes.append(
                    _Route(
                        destination=_route_prefix(entry.get("route_destination") or "default"),
                        table=table,
                        gateway=gateway,
                        interface=outbound,
                        source=entry.get("route_source") or source,
                        metric=metric,
                    )
                )
            if kind is None and not matched and (gateway or table in RESERVED_TABLES):
                continue
            rules.append(_Rule(priority, table, source, destination, mark, interface))

        return (
            list({self._rule_key(rule): rule for rule in rules}.values()),
            list({self._route_key(route): route for route in routes}.values()),
        )

    # -- key normalisation / command rendering ---------------------------

    @staticmethod
    def _rule_key(rule: _Rule) -> Tuple[Any, ...]:
        return (rule.priority, rule.source, rule.destination, rule.mark, rule.interface, rule.table)

    @staticmethod
    def _route_key(route: _Route) -> Tuple[Any, ...]:
        return (
            route.destination,
            route.table,
            route.gateway,
            route.interface,
            route.source,
            route.metric,
        )

    @classmethod
    def _live_rule_obj(cls, obj: Dict[str, Any]) -> _Rule:
        return _Rule(
            priority=int(obj.get("priority", 0)),
            table=_table(obj.get("table")),
            source=_live_prefix(obj.get("src"), obj.get("srclen")),
            destination=_live_prefix(obj.get("dst"), obj.get("dstlen")),
            mark=_mark(obj.get("fwmark")),
            interface=obj.get("iif"),
        )

    @classmethod
    def _live_route_obj(cls, obj: Dict[str, Any]) -> _Route:
        return _Route(
            destination=_route_prefix(obj.get("dst")),
            table=_table(obj.get("table")),
            gateway=obj.get("gateway"),
            interface=obj.get("dev"),
            source=obj.get("prefsrc"),
            metric=obj.get("metric"),
        )

    def _rule_args(self, rule: _Rule, action: str) -> List[str]:
        args = ["rule", action]
        if rule.source:
            args.extend(["from", rule.source])
        if rule.destination:
            args.extend(["to", rule.destination])
        if rule.mark:
            args.extend(["fwmark", str(rule.mark)])
        if rule.interface:
            args.extend(["iif", rule.interface])
        args.extend(
            ["table", self._table_name(rule.table), "prio", str(rule.priority), "protocol", str(TAG_PROTOCOL)]
        )
        return args

    def _route_args(self, route: _Route, action: str) -> List[str]:
        args = ["route", action, route.destination]
        if route.gateway:
            args.extend(["via", route.gateway])
        if route.interface:
            args.extend(["dev", route.interface])
        if route.source:
            args.extend(["src", route.source])
        if route.metric is not None:
            args.extend(["metric", str(route.metric)])
        args.extend(["table", self._table_name(route.table), "proto", str(TAG_PROTOCOL)])
        return args

    async def _mutate(self, args: Sequence[str]) -> bool:
        command = ["ip", *args]
        self.mutations.append(command)
        if self.dry_run:
            return True
        rc, _, stderr = await self._exec(args)
        if rc != 0:
            self.errors.append(f"{' '.join(command)} failed ({rc}): {stderr.strip()}")
        return rc == 0

    # -- idempotent apply -------------------------------------------------

    async def apply_routing(self, routing_rules: Optional[Sequence[Any]]) -> bool:
        """Reconcile live routing to ``routing_rules``; mutate only deltas."""
        desired_rules, desired_routes = self._desired(routing_rules)
        ok = True
        tables = {_table(r.table) for r in desired_rules} | {_table(r.table) for r in desired_routes}
        for table in sorted(tables, key=str):
            ok = (await self._ensure_table(table)) and ok

        live_rule_entries = await self._live_rules()
        live_route_entries = await self._live_routes()
        all_rule_keys = {self._rule_key(self._live_rule_obj(o)) for o in live_rule_entries}
        all_route_keys = {self._route_key(self._live_route_obj(o)) for o in live_route_entries}
        desired_rule_keys = {self._rule_key(r) for r in desired_rules}
        desired_route_keys = {self._route_key(r) for r in desired_routes}

        for entry in live_rule_entries:
            live = self._live_rule_obj(entry)
            if _owned(entry) and self._rule_key(live) not in desired_rule_keys:
                ok = (await self._mutate(self._rule_args(live, "del"))) and ok

        for entry in live_route_entries:
            live = self._live_route_obj(entry)
            if _owned(entry) and self._route_key(live) not in desired_route_keys:
                ok = (await self._mutate(self._route_args(live, "del"))) and ok

        for rule in desired_rules:
            if self._rule_key(rule) not in all_rule_keys:
                ok = (await self._mutate(self._rule_args(rule, "add"))) and ok

        for route in desired_routes:
            if self._route_key(route) not in all_route_keys:
                ok = (await self._mutate(self._route_args(route, "add"))) and ok

        return ok

    # -- legacy single-object API (kept for api.py) -----------------------

    async def add_route(
        self,
        destination: str,
        gateway: Optional[str] = None,
        interface: Optional[str] = None,
        table: str = "main",
        source: Optional[str] = None,
        metric: Optional[int] = None,
    ) -> bool:
        """Add a route only if the identical route is not already live."""
        table_id = _table(table)
        await self._ensure_table(table_id)
        route = _Route(
            destination=_route_prefix(destination),
            table=table_id,
            gateway=gateway,
            interface=interface,
            source=source,
            metric=metric,
        )
        live = {self._route_key(self._live_route_obj(entry)) for entry in await self._live_routes()}
        if self._route_key(route) in live:
            return True
        return await self._mutate(self._route_args(route, "add"))

    async def add_policy_rule(
        self,
        table: int,
        priority: int,
        source: Optional[str] = None,
        destination: Optional[str] = None,
        mark: Optional[int] = None,
        interface: Optional[str] = None,
    ) -> bool:
        """Add a policy rule only if the identical rule is not already live."""
        await self._ensure_table(table)
        rule = _Rule(
            priority=priority,
            table=table,
            source=_prefix(source),
            destination=_prefix(destination),
            mark=_mark(mark),
            interface=interface,
        )
        live = {self._rule_key(self._live_rule_obj(entry)) for entry in await self._live_rules()}
        if self._rule_key(rule) in live:
            return True
        return await self._mutate(self._rule_args(rule, "add"))

    async def setup_load_balancing(
        self,
        gateways: List[Dict[str, str]],
        method: str = "round_robin",  # round_robin, weighted, failover
    ) -> bool:
        """Setup multi-WAN load balancing"""
        try:
            for i, gw in enumerate(gateways):
                table_name = f"wan{i + 1}"
                await self.add_routing_table(table_name, 100 + i)
                await self.add_route(
                    destination="default",
                    gateway=gw["gateway"],
                    interface=gw["interface"],
                    table=table_name,
                )

            if method == "round_robin":
                for i, _ in enumerate(gateways):
                    await self.add_policy_rule(table=100 + i, priority=100 + i, mark=i + 1)
            elif method == "failover":
                await self.add_policy_rule(table=100, priority=100)
                await self.add_policy_rule(table=101, priority=200)
            return True
        except Exception as exc:  # pragma: no cover - legacy behaviour
            print(f"Load balancing setup failed: {exc}")
            return False

    async def get_routes(self, table: str = "all") -> List[Dict[str, Any]]:
        """Get routing table (raw lines, legacy shape)."""
        args = ["route", "show"]
        if table != "all":
            args.extend(["table", table])
        rc, stdout, _ = await self._exec(args)
        if rc != 0:
            return []
        return [
            {"raw": line}
            for line in stdout.strip().splitlines()
            if line and not line.startswith("broadcast")
        ]

    async def get_rules(self) -> List[Dict[str, Any]]:
        """Get policy routing rules (raw lines, legacy shape)."""
        rc, stdout, _ = await self._exec(["rule", "show"])
        if rc != 0:
            return []
        return [{"raw": line} for line in stdout.strip().splitlines() if line]
