"""nftables management for the Viswall firewall agent.

Docker-safe renderer (todo 7): ``generate_ruleset`` emits a ruleset that
creates/replaces ONLY ``table inet viswall``. It never clears the global
ruleset — Docker's own tables and chains stay untouched. ``apply_ruleset``
swaps the viswall table by deleting it first, then loading the rendered file.

``FirewallRule`` tagging conventions consumed by the renderer (tagged rules
are rendered in their dedicated sections and skipped by the generic
user-rule pass):

* managed-port meter — ``chain="input"`` + ``protocol``/``destination_port``
  matching 22/80/443/51820 + ``limit`` set: drives the per-source meter rate.
  Two family-scoped buckets per port — ``meta nfproto ipv4`` (``ip saddr``)
  and ``meta nfproto ipv6`` (``ip6 saddr``). A row whose name ends ``_v6``
  (the importer names rules.v6 hashlimit rows by their live
  ``--hashlimit-name``, e.g. ``ssh_limit_v6``) feeds the v6 bucket; any other
  matching row feeds the v4 bucket. The DB ``limit`` string is emitted
  VERBATIM inside the meter as ``limit rate over <rate>`` — ``over`` makes
  the meter match only the OVER-limit traffic (live ``--hashlimit-above``
  semantics; plain ``limit rate`` drops the FIRST burst packets instead),
  and no burst clause is ever appended twice. The built-in default is used
  only when no such row exists; never both.
* loopback guard — ``chain="input"`` + ``action=DROP`` +
  ``destination="127.0.0.1"`` + ``protocol="tcp"`` + ``destination_port``:
  grouped into one ``iifname != "lo"`` guarded dport set.
* container-IP anti-spoof — ``anti_spoof=True`` (or "anti-spoof" in
  ``name``/``comment``) + ``chain="forward"`` + ``destination``=container
  IP: rendered as ``iifname != "<bridge>" <family> daddr <ip> drop`` in the
  forward chain. The bridge comes from ``interface_in`` when set; otherwise
  it is parsed from the name's ``via <bridge>`` suffix (todo 34 importer
  convention: "anti-spoof <ip> via <bridge>" — the FirewallRule schema has
  no interface_in column, so the bridge rides in the row name).
* internal-port protection — "internal-port" in ``name``/``comment`` +
  ``chain="forward"`` + ``protocol="tcp"`` + ``destination_port``: grouped
  into the DOCKER-USER replacement set (built-in boseman defaults used when
  no DB-origin rule exists), rendered BEFORE the docker0/br-* bridge accepts
  (live jumps to DOCKER-USER before DOCKER-FORWARD; a bridge accept first
  would let WAN->published internal ports through).

When env ``VALIDATION_MODE=1`` the renderer emits a pass-through ruleset:
every chain policy accept, no drop/limit/meter rules, log-only matches with
prefix "VW-VALIDATION" and ``limit rate 10/minute`` on every log rule.
"""

import asyncio
import ipaddress
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class FirewallAction(Enum):
    ACCEPT = "accept"
    DROP = "drop"
    REJECT = "reject"
    LOG = "log"
    QUEUE = "queue"  # For content scanning


@dataclass
class FirewallRule:
    id: int
    name: str
    chain: str  # input, output, forward, prerouting, postrouting
    source: Optional[str] = None  # IP, CIDR, or "any"
    destination: Optional[str] = None
    protocol: Optional[str] = None  # tcp, udp, icmp, any
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    interface_in: Optional[str] = None
    interface_out: Optional[str] = None
    action: FirewallAction = FirewallAction.ACCEPT
    log: bool = False
    state: Optional[str] = None  # NEW, ESTABLISHED, RELATED, INVALID
    limit: Optional[str] = None  # rate limiting, e.g., "10/minute"
    comment: Optional[str] = None
    order: int = 0
    anti_spoof: bool = False  # container-IP anti-spoof tag (forward chain)


@dataclass
class NATRule:
    id: int
    name: str
    type: str  # snat, dnat, masquerade
    chain: str  # prerouting, postrouting
    source: Optional[str] = None
    destination: Optional[str] = None
    to_source: Optional[str] = None  # For SNAT
    to_destination: Optional[str] = None  # For DNAT
    protocol: Optional[str] = None
    port: Optional[int] = None
    interface: Optional[str] = None
    comment: Optional[str] = None


# (protocol, port) -> (meter name, default rate). Both the ipv4 and the
# ipv6 meter are always emitted; a FirewallRule matching protocol+port with
# ``limit`` set overrides its family's default rate (see ``_meter_rate``).
METER_SPECS: Dict[Tuple[str, int], Tuple[str, str]] = {
    ("tcp", 22): ("ssh_limit", "10/minute"),
    ("tcp", 80): ("http_limit", "100/minute"),
    ("tcp", 443): ("https_limit", "100/minute"),
    ("udp", 51820): ("wireguard_limit", "20/minute"),
}

# Management accepts. ONE list rendered with a family filter: ipv4 gets every
# entry, ipv6 only the entries in _V6_OPEN (22/80/443/51820).
_MGMT_ACCEPTS: Tuple[Tuple[str, Union[int, Tuple[int, int]]], ...] = (
    ("tcp", 22),
    ("tcp", 80),
    ("tcp", 443),
    ("udp", 51820),
    ("tcp", 25),
    ("tcp", 53),
    ("tcp", 110),
    ("tcp", 143),
    ("tcp", 993),
    ("tcp", 995),
    ("tcp", (21114, 21119)),
    ("udp", 25),
    ("udp", 53),
    ("udp", 21116),
)
_V6_OPEN = {("tcp", 22), ("tcp", 80), ("tcp", 443), ("udp", 51820)}

DEFAULT_WAN = "enp0s31f6"
DEFAULT_INTERNAL_PORTS: Tuple[int, ...] = (
    5000, 5055, 5678, 8000, 8001, 8080, 8089, 8090, 8091,
    8096, 8100, 8201, 8502, 8888, 9090, 10000, 11434,
)

_PROTO_NAMES = {"tcp", "udp", "icmp", "icmpv6", "sctp", "igmp", "esp", "ah", "gre"}
_CT_STATES = {"NEW", "ESTABLISHED", "RELATED", "INVALID", "UNTRACKED"}
_IFNAME_RE = re.compile(r"[A-Za-z0-9_.:*+@-]+\Z")
_LIMIT_RE = re.compile(r"[0-9]+\s*/\s*(second|minute|hour|day)(\s+burst\s+[0-9]+\s+packets)?\Z")
#: Bridge extraction from the todo-34 importer row name convention
#: "anti-spoof <ip> via <bridge>" (the schema has no interface_in column).
_BRIDGE_VIA_RE = re.compile(r"\bvia\s+(\S+)")
#: Default burst appended exactly once when a DB limit string carries none
#: (live hashlimit burst is 5; the old render appended a second burst to
#: strings that already had one, which made nft -c fail).
_DEFAULT_BURST = " burst 5 packets"


def _quote(value: str) -> str:
    """Double-quote a string for nft, escaping backslashes and quotes."""
    return '"' + value.replace("\\", "\\\\").replace('"', "'") + '"'


def _safe_ifname(name: str) -> bool:
    return bool(name) and bool(_IFNAME_RE.fullmatch(name))


def _valid_net(value: str) -> bool:
    try:
        ipaddress.ip_network(value, strict=False)
        return True
    except ValueError:
        return False


def _valid_limit(value: str) -> bool:
    return bool(_LIMIT_RE.fullmatch(value))


def _valid_to_addr(value: str) -> bool:
    candidate = value
    if ":" in value and "::" not in value:
        candidate = value.rsplit(":", 1)[0]
    try:
        ipaddress.ip_network(candidate, strict=False)
        return True
    except ValueError:
        return False


class NFTablesManager:
    """Manages nftables firewall rules (modern replacement for iptables)"""

    # Fixed ruleset location — deliberately inlined at every use so no
    # caller-supplied value can influence the path.
    CONFIG_PATH = "/etc/nftables.conf"

    def __init__(self):
        self.ruleset: Dict[str, Any] = {}

    # ---- todo 7 renderer --------------------------------------------------

    @staticmethod
    def _validation_mode() -> bool:
        return os.environ.get("VALIDATION_MODE") == "1"

    @staticmethod
    def _parse_addr_family(addr: str) -> Optional[str]:
        """'ip' / 'ip6' for a bare address OR a CIDR; None when unparsable."""
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            try:
                net = ipaddress.ip_network(addr, strict=False)
            except ValueError:
                return None
            return "ip6" if isinstance(net, ipaddress.IPv6Network) else "ip"
        return "ip6" if isinstance(ip, ipaddress.IPv6Address) else "ip"

    @staticmethod
    def _port_set(ports) -> str:
        parts = []
        for p in sorted(ports, key=lambda p: p[0] if isinstance(p, tuple) else p):
            parts.append(f"{p[0]}-{p[1]}" if isinstance(p, tuple) else str(p))
        return "{" + ", ".join(parts) + "}"

    def _meter_rate(
        self, rules: List[FirewallRule], proto: str, port: int, family: str = "ip"
    ) -> str:
        """Single-bucket rate: DB-origin ``limit`` wins, built-in default otherwise.

        ``family`` selects the bucket: ``"ip6"`` accepts only rows whose name
        ends ``_v6`` (the importer names rules.v6 hashlimit rows by their live
        --hashlimit-name), ``"ip"`` only rows that do not. The returned string
        is the DB ``limit`` verbatim (with or without its burst clause); the
        caller appends the default burst only when it is absent.
        """
        for rule in rules:
            if (rule.chain or "").lower() != "input":
                continue
            if not rule.protocol or rule.protocol.lower() != proto:
                continue
            if rule.destination_port != port or not rule.limit:
                continue
            if ((rule.name or "").lower().endswith("_v6")) != (family == "ip6"):
                continue
            if _valid_limit(rule.limit):
                return rule.limit
        return METER_SPECS[(proto, port)][1]

    @staticmethod
    def _with_burst(limit: str) -> str:
        """Ensure exactly ONE burst clause (duplicating it breaks nft -c)."""
        return limit if " burst " in limit else limit + _DEFAULT_BURST

    @staticmethod
    def _is_loopback_guard(rule: FirewallRule) -> bool:
        return (
            (rule.chain or "").lower() == "input"
            and rule.action is FirewallAction.DROP
            and bool(rule.destination)
            and rule.destination != "any"
            and rule.destination.split("/", 1)[0] == "127.0.0.1"
            and bool(rule.protocol)
            and rule.protocol.lower() == "tcp"
            and bool(rule.destination_port)
        )

    @staticmethod
    def _is_managed_meter(rule: FirewallRule) -> bool:
        return (
            (rule.chain or "").lower() == "input"
            and bool(rule.limit)
            and bool(rule.protocol)
            and bool(rule.destination_port)
            and (rule.protocol.lower(), rule.destination_port) in METER_SPECS
        )

    @staticmethod
    def _is_anti_spoof(rule: FirewallRule) -> bool:
        return (
            rule.anti_spoof
            or "anti-spoof" in (rule.name or "").lower()
            or "anti-spoof" in (rule.comment or "").lower()
        )

    @staticmethod
    def _is_internal_port(rule: FirewallRule) -> bool:
        return "internal-port" in (rule.name or "").lower() or "internal-port" in (rule.comment or "").lower()

    def _loopback_ports(self, rules: List[FirewallRule]) -> List[int]:
        ports = {rule.destination_port for rule in rules if self._is_loopback_guard(rule)}
        return sorted(p for p in ports if p is not None)

    def _internal_ports(self, rules: List[FirewallRule]) -> Tuple[int, ...]:
        ports = {
            rule.destination_port
            for rule in rules
            if (rule.chain or "").lower() == "forward"
            and bool(rule.protocol)
            and rule.protocol.lower() == "tcp"
            and bool(rule.destination_port)
            and self._is_internal_port(rule)
        }
        return tuple(sorted(p for p in ports if p is not None)) or DEFAULT_INTERNAL_PORTS

    def _anti_spoof_bridge(self, rule: FirewallRule) -> Optional[str]:
        """Bridge for one anti-spoof row; None when it cannot be determined.

        Precedence: an explicit ``interface_in``; otherwise the bridge is
        parsed from the row name's ``via <bridge>`` suffix. Parsing rule
        (todo 34 importer convention — the FirewallRule schema has no
        interface_in column, so the bridge rides in the name):
        ``build_rows`` emits ``anti-spoof {dest_ip} via {in_iface}``, e.g.
        "anti-spoof 172.18.0.3 via br-d46e3a305cbd"; the token after the
        final " via " is the bridge and must pass ``_safe_ifname``.
        """
        if rule.interface_in and _safe_ifname(rule.interface_in):
            return rule.interface_in
        match = _BRIDGE_VIA_RE.search(rule.name or "")
        if match and _safe_ifname(match.group(1)):
            return match.group(1)
        return None

    def _anti_spoof_lines(self, rules: List[FirewallRule]) -> List[str]:
        lines: List[str] = []
        for rule in rules:
            if (rule.chain or "").lower() != "forward" or not self._is_anti_spoof(rule):
                continue
            bridge = self._anti_spoof_bridge(rule)
            if not bridge or not rule.destination:
                continue
            family = self._parse_addr_family(rule.destination)
            if family is None:
                continue
            lines.append(
                f'        iifname != "{bridge}" {family} daddr {rule.destination} drop'
            )
        return lines

    def _user_rules(self, rules: List[FirewallRule], chain: str) -> List[str]:
        rendered: List[str] = []
        for rule in sorted(rules, key=lambda r: r.order):
            if (rule.chain or "").lower() != chain:
                continue
            if chain == "input" and (self._is_loopback_guard(rule) or self._is_managed_meter(rule)):
                continue  # rendered in their dedicated sections
            if chain == "forward" and (
                self._is_anti_spoof(rule)
                or ((rule.chain or "").lower() == "forward" and self._is_internal_port(rule))
            ):
                continue  # rendered in their dedicated sections
            rendered.append(self._convert_rule_to_nft(rule).rstrip("\n"))
        return rendered

    def _render_header(self) -> str:
        return (
            "#!/usr/sbin/nft -f\n"
            "\n"
            "# Viswall Firewall Configuration (docker-safe renderer)\n"
            f"# Generated: {datetime.now(timezone.utc).isoformat()}\n"
            "# Replaces ONLY `table inet viswall`; Docker keeps its own tables.\n"
            "\n"
        )

    def _render_input(
        self,
        validation: bool,
        rules: List[FirewallRule],
        conntrack: bool,
        logging: bool,
    ) -> str:
        policy = "accept" if validation else "drop"
        lines = [
            "    chain input {",
            f"        type filter hook input priority -200; policy {policy};",
        ]
        if validation:
            lines.append('        log prefix "VW-VALIDATION: input " limit rate 10/minute accept')
            lines.append("    }")
            return "\n".join(lines)
        if conntrack:
            lines.extend(
                [
                    "        # Connection tracking",
                    "        ct state established,related accept",
                    "        ct state invalid drop",
                ]
            )
        lines.extend(
            [
                "        # Loopback",
                '        iif "lo" accept',
                "        # Container bridges (docker coexistence) — live INPUT accepts docker0 only",
                '        iifname "docker0" accept',
                "        # ICMP / ICMPv6 rate limited",
                "        ip protocol icmp limit rate 5/second accept",
                "        ip6 nexthdr icmpv6 limit rate 5/second accept",
            ]
        )
        # dport-scoped per-source meters, family-split so v6 traffic cannot
        # bypass them; ``limit rate over`` drops only the OVER-limit traffic
        # (live --hashlimit-above semantics — plain ``limit rate`` would drop
        # the first burst packets and let the flood through).
        for (proto, port), (name, _default) in METER_SPECS.items():
            rate_v4 = self._with_burst(self._meter_rate(rules, proto, port, "ip"))
            rate_v6 = self._with_burst(self._meter_rate(rules, proto, port, "ip6"))
            lines.append(
                f"        meta nfproto ipv4 {proto} dport {port} meter {name} "
                f"{{ ip saddr limit rate over {rate_v4} }} drop"
            )
            lines.append(
                f"        meta nfproto ipv6 {proto} dport {port} meter {name}_v6 "
                f"{{ ip6 saddr limit rate over {rate_v6} }} drop"
            )
        # Management accepts, family-scoped from the single _MGMT_ACCEPTS list
        v4_tcp = [p for proto, p in _MGMT_ACCEPTS if proto == "tcp"]
        v4_udp = [p for proto, p in _MGMT_ACCEPTS if proto == "udp"]
        v6_tcp = [p for proto, p in _MGMT_ACCEPTS if proto == "tcp" and (proto, p) in _V6_OPEN]
        v6_udp = [p for proto, p in _MGMT_ACCEPTS if proto == "udp" and (proto, p) in _V6_OPEN]
        lines.extend(
            [
                f"        meta nfproto ipv4 tcp dport {self._port_set(v4_tcp)} accept",
                f"        meta nfproto ipv4 udp dport {self._port_set(v4_udp)} accept",
                f"        meta nfproto ipv6 tcp dport {self._port_set(v6_tcp)} accept",
                f"        meta nfproto ipv6 udp dport {self._port_set(v6_udp)} accept",
                "        # PostgreSQL never exposed",
                "        tcp dport 5432 drop",
            ]
        )
        loop = self._loopback_ports(rules)
        if loop:
            lines.append(
                f'        iifname != "lo" ip daddr 127.0.0.1 tcp dport {self._port_set(loop)} drop'
            )
        # User rules: ALWAYS after the mandatory accepts above (a console rule
        # can never override SSH/WG/established/lo access).
        lines.extend(self._user_rules(rules, "input"))
        if logging:
            lines.append('        log prefix "FIREWALL-DROP: " limit rate 5/minute drop')
        else:
            lines.append("        drop")
        lines.append("    }")
        return "\n".join(lines)

    def _render_forward(
        self,
        validation: bool,
        rules: List[FirewallRule],
        wan_ifaces: List[str],
        conntrack: bool,
    ) -> str:
        policy = "accept" if validation else "drop"
        lines = [
            "    chain forward {",
            f"        type filter hook forward priority -150; policy {policy};",
        ]
        if validation:
            lines.append('        log prefix "VW-VALIDATION: forward " limit rate 10/minute accept')
            lines.append("    }")
            return "\n".join(lines)
        if conntrack:
            lines.append("        ct state established,related accept")
        lines.append("        # Container-IP anti-spoof drops")
        lines.extend(self._anti_spoof_lines(rules))
        ports = self._internal_ports(rules)
        # DOCKER-USER replacement, rendered BEFORE the bridge accepts: live
        # jumps to DOCKER-USER before DOCKER-FORWARD — a bridge accept first
        # would let WAN->published internal ports through.
        lines.append("        # DOCKER-USER replacement: external access to internal ports")
        for wan in wan_ifaces or [DEFAULT_WAN]:
            lines.append(
                f'        iifname "{wan}" ct direction original ct original proto-dst {self._port_set(ports)} drop'
            )
        lines.extend(
            [
                "        # Container bridge traffic (docker coexistence)",
                '        iifname "docker0" accept',
                '        oifname "docker0" accept',
                '        iifname "br-*" accept',
                '        oifname "br-*" accept',
            ]
        )
        lines.extend(self._user_rules(rules, "forward"))
        lines.append("        accept")
        lines.append("    }")
        return "\n".join(lines)

    def _render_output(self, validation: bool, conntrack: bool) -> str:
        lines = [
            "    chain output {",
            "        type filter hook output priority -200; policy accept;",
        ]
        if validation:
            lines.append('        log prefix "VW-VALIDATION: output " limit rate 10/minute accept')
        elif conntrack:
            lines.append("        ct state established,related accept")
        lines.append("    }")
        return "\n".join(lines)

    def _render_nat(self, nat_rules: List[NATRule]) -> str:
        lines = [
            "    chain prerouting {",
            "        type nat hook prerouting priority -110; policy accept;",
        ]
        for rule in nat_rules:
            if rule.type == "dnat" and rule.to_destination and _valid_to_addr(rule.to_destination):
                lines.append(self._convert_nat_rule_to_nft(rule).rstrip("\n"))
        lines.append("    }")
        lines.extend(
            [
                "    chain postrouting {",
                "        type nat hook postrouting priority 90; policy accept;",
            ]
        )
        for rule in nat_rules:
            if rule.type == "snat" and rule.to_source and _valid_to_addr(rule.to_source):
                lines.append(self._convert_nat_rule_to_nft(rule).rstrip("\n"))
            elif rule.type == "masquerade":
                # Docker owns NAT; viswall never emits masquerade (on WAN or anywhere).
                lines.append(f"        # masquerade skipped (docker owns NAT): {rule.name}")
        lines.append("    }")
        return "\n".join(lines)

    def generate_ruleset(
        self,
        interfaces: List[Dict[str, str]],
        firewall_rules: List[FirewallRule],
        nat_rules: List[NATRule],
        enable_logging: bool = True,
        enable_conntrack: bool = True,
    ) -> str:
        """Generate a docker-safe nftables ruleset (table inet viswall only)."""
        validation = self._validation_mode()
        wan_ifaces = [
            str(iface["name"])
            for iface in interfaces
            if iface.get("type") == "wan" and _safe_ifname(str(iface.get("name") or ""))
        ]
        # The named meters (ssh/http/https/wireguard_limit) are declared
        # implicitly by the rule-level ``meter NAME { ... }`` statements below
        # — nft < 1.1 rejects table-level ``meter`` declarations, so none are
        # emitted here.
        parts = [
            self._render_header(),
            "table inet viswall {",
        ]
        parts.append(self._render_input(validation, firewall_rules, enable_conntrack, enable_logging))
        parts.append(self._render_forward(validation, firewall_rules, wan_ifaces, enable_conntrack))
        parts.append(self._render_output(validation, enable_conntrack))
        if nat_rules and not validation:
            parts.append(self._render_nat(nat_rules))
        parts.append("}")
        return "\n".join(parts) + "\n"

    def _ip_family(self, addr: Optional[str]) -> str:
        """Return 'ip' or 'ip6' for an address or CIDR."""
        if not addr or addr == "any":
            return "ip"
        try:
            if "/" in addr:
                net = ipaddress.ip_network(addr, strict=False)
                return "ip6" if isinstance(net, ipaddress.IPv6Network) else "ip"
            else:
                ip = ipaddress.ip_address(addr)
                return "ip6" if isinstance(ip, ipaddress.IPv6Address) else "ip"
        except ValueError:
            return "ip"

    def _convert_rule_to_nft(self, rule: FirewallRule) -> str:
        """Convert a FirewallRule to an nftables rule line (8-space indent).

        Unparsable values are skipped rather than emitted, so a malformed rule
        still yields a ruleset that passes ``nft -c``.
        """
        conditions: List[str] = []

        if rule.interface_in and _safe_ifname(rule.interface_in):
            conditions.append(f'iifname "{rule.interface_in}"')
        if rule.interface_out and _safe_ifname(rule.interface_out):
            conditions.append(f'oifname "{rule.interface_out}"')

        src_family = self._ip_family(rule.source)
        dst_family = self._ip_family(rule.destination)
        if rule.source and rule.source != "any" and _valid_net(rule.source):
            conditions.append(f"{src_family} saddr {rule.source}")
        if rule.destination and rule.destination != "any" and _valid_net(rule.destination):
            conditions.append(f"{dst_family} daddr {rule.destination}")

        if rule.protocol and rule.protocol != "any" and rule.protocol.lower() in _PROTO_NAMES:
            proto = rule.protocol.lower()
            family = "ip6" if (src_family == "ip6" or dst_family == "ip6") else "ip"
            if family == "ip6":
                conditions.append(f"ip6 nexthdr {proto}")
            else:
                conditions.append(f"ip protocol {proto}")
            if rule.source_port and 1 <= rule.source_port <= 65535:
                conditions.append(f"{proto} sport {rule.source_port}")
            if rule.destination_port and 1 <= rule.destination_port <= 65535:
                conditions.append(f"{proto} dport {rule.destination_port}")

        if rule.state:
            states = [s.strip().upper() for s in rule.state.split(",")]
            valid = [s for s in states if s in _CT_STATES]
            if valid:
                conditions.append("ct state " + ",".join(valid))

        if rule.limit and _valid_limit(rule.limit):
            conditions.append(f"limit rate {rule.limit}")

        nft_rule = "        " + (" ".join(conditions) + " " if conditions else "")
        name = _quote(f"[NFT {rule.name or ''}]")

        if rule.action is FirewallAction.LOG:
            nft_rule += f"log prefix {name} accept"
        else:
            if rule.log:
                nft_rule += f"log prefix {name} "
            nft_rule += rule.action.value

        if rule.comment:
            nft_rule += f" comment {_quote(rule.comment)}"

        return nft_rule + "\n"

    def _convert_nat_rule_to_nft(self, rule: NATRule) -> str:
        """Convert a NATRule to nftables syntax (dual-stack aware)"""
        nft_rule = "        "
        conditions = []

        if rule.interface and _safe_ifname(rule.interface):
            conditions.append(f'iifname "{rule.interface}"')

        src_family = self._ip_family(rule.source)
        dst_family = self._ip_family(rule.destination)

        if rule.source and _valid_net(rule.source):
            conditions.append(f"{src_family} saddr {rule.source}")
        if rule.destination and _valid_net(rule.destination):
            conditions.append(f"{dst_family} daddr {rule.destination}")

        if rule.protocol and rule.protocol != "any" and rule.protocol.lower() in _PROTO_NAMES:
            proto = rule.protocol.lower()
            family = "ip6" if (src_family == "ip6" or dst_family == "ip6") else "ip"
            if family == "ip6":
                conditions.append(f"ip6 nexthdr {proto}")
            else:
                conditions.append(f"ip protocol {proto}")
            if rule.port and 1 <= rule.port <= 65535:
                conditions.append(f"{proto} dport {rule.port}")

        if conditions:
            nft_rule += " ".join(conditions) + " "

        if rule.type == "dnat":
            nft_rule += f"dnat to {rule.to_destination}"
        elif rule.type == "snat":
            nft_rule += f"snat to {rule.to_source}"

        if rule.comment:
            nft_rule += f" comment {_quote(rule.comment)}"

        nft_rule += "\n"
        return nft_rule

    async def apply_ruleset(self, ruleset: str) -> bool:
        """Apply nftables ruleset"""
        try:
            # Normalized + contained to /etc — the ruleset path is fixed and
            # no caller-supplied value can influence it.
            conf_path = Path("/etc/nftables.conf").resolve()
            if not conf_path.is_relative_to(Path("/etc").resolve()):
                raise ValueError("refusing to write ruleset outside /etc")

            # Write config
            with conf_path.open("w") as f:
                f.write(ruleset)

            # Validate ruleset
            proc = await asyncio.create_subprocess_exec(
                "nft",
                "-c",
                "-f",
                str(conf_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                print(f"nftables validation failed: {stderr.decode()}")
                return False

            # Swap only the viswall table: delete it first (a first apply has
            # no such table — a non-zero exit there is expected and harmless),
            # then load the rendered file. Docker's tables are never touched.
            del_proc = await asyncio.create_subprocess_exec(
                "nft",
                "delete",
                "table",
                "inet",
                "viswall",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await del_proc.communicate()

            # Apply ruleset
            proc = await asyncio.create_subprocess_exec(
                "nft",
                "-f",
                str(conf_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            return proc.returncode == 0

        except Exception as e:
            print(f"Failed to apply nftables: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get nftables statistics"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "nft",
                "list",
                "ruleset",
                "-j",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            return json.loads(stdout.decode())
        except:
            return {}

    async def add_to_blacklist(self, ip: str, timeout: str = "1h") -> bool:
        """Dynamically add IP to blacklist (dual-stack aware)"""
        try:
            set_name = "blacklist_v6" if self._ip_family(ip) == "ip6" else "blacklist_v4"
            proc = await asyncio.create_subprocess_exec(
                "nft",
                "add",
                "element",
                "inet",
                "viswall",
                set_name,
                "{",
                ip,
                "timeout",
                timeout,
                "}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except:
            return False

    async def remove_from_blacklist(self, ip: str) -> bool:
        """Remove IP from blacklist (dual-stack aware)"""
        try:
            set_name = "blacklist_v6" if self._ip_family(ip) == "ip6" else "blacklist_v4"
            proc = await asyncio.create_subprocess_exec(
                "nft",
                "delete",
                "element",
                "inet",
                "viswall",
                set_name,
                "{",
                ip,
                "}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except:
            return False
