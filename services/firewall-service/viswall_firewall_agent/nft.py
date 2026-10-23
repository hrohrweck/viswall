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
  grouped into one ``iifname != "lo"`` guarded dport set, rendered in the
  ``raw_prerouting`` chain (filter hook prerouting priority -300, PRE-DNAT).
* container-IP anti-spoof — ``anti_spoof=True`` (or "anti-spoof" in
  ``name``/``comment``) + ``chain="forward"`` + ``destination``=container
  IP: rendered as ``iifname != "<bridge>" <family> daddr <ip> drop`` in the
  ``raw_prerouting`` chain (same hook as the live raw PREROUTING table).
  Both MUST run pre-DNAT: docker publishes container ports via DNAT, so a
  post-DNAT placement (input/forward hook) sees the rewritten destination —
  the loopback guard would miss the 127.0.0.1-published flows entirely, and
  the anti-spoof drop would wrongly kill legitimate published-port flows
  (todo 39b finding). The bridge comes from ``interface_in`` when set;
  otherwise it is parsed from the name's ``via <bridge>`` suffix (todo 34
  importer convention: "anti-spoof <ip> via <bridge>" — the FirewallRule
  schema has no interface_in column, so the bridge rides in the row name).
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
import logging
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


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
#: Block timeout shape: <digits> + one of s/m/h/d (rendered into an nft
#: element statement — anything else is an injection vector).
_BLOCK_TIMEOUT_RE = re.compile(r"^\d+(s|m|h|d)$")
#: Bridge extraction from the todo-34 importer row name convention
#: "anti-spoof <ip> via <bridge>" (the schema has no interface_in column).
_BRIDGE_VIA_RE = re.compile(r"\bvia\s+(\S+)")
#: Default burst appended exactly once when a DB limit string carries none
#: (live hashlimit burst is 5; the old render appended a second burst to
#: strings that already had one, which made nft -c fail).
_DEFAULT_BURST = " burst 5 packets"


def _quote(value: str) -> str:
    """Double-quote a string for nft, escaping backslashes and double quotes.

    nft double-quoted strings escape ``"`` as ``\\"`` — replacing the quote
    with ``'`` (the old behavior) silently rewrote the content instead of
    producing a valid nft-quoted string.
    """
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


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


def _valid_block_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def _valid_block_timeout(value: str) -> bool:
    return bool(_BLOCK_TIMEOUT_RE.fullmatch(value))


def _valid_to_addr(value: str) -> bool:
    return _normalize_to_addr(value) is not None


def _normalize_to_addr(value: str) -> Optional[str]:
    """Strictly parse a NAT target ``<ip>(:<port>)?`` (v4) or ``[<v6>](:<port>)?``.

    Returns the canonical safe form, or None. to_source/to_destination are
    rendered verbatim into the ruleset, so any newline/CR/`=` is rejected
    outright — an unvalidated newline injects arbitrary nft statements (e.g.
    ``flush chain input``) into a root-run ``nft -f``.
    """
    if not value or any(ch in value for ch in ("\n", "\r", "=")):
        return None
    if value.startswith("["):
        match = re.fullmatch(r"\[([0-9a-fA-F:.%]+)\](?::(\d{1,5}))?", value)
        if not match:
            return None
        try:
            address = str(ipaddress.IPv6Address(match.group(1)))
        except ValueError:
            return None
        port_text = match.group(2)
        if port_text is not None and not 1 <= int(port_text) <= 65535:
            return None
        return f"[{address}]" + (f":{port_text}" if port_text else "")
    if ":" in value:
        address_text, _, port_text = value.rpartition(":")
        if not re.fullmatch(r"\d{1,5}", port_text):
            return None
        if not 1 <= int(port_text) <= 65535:
            return None
        try:
            address = str(ipaddress.IPv4Address(address_text))
        except ValueError:
            return None
        return f"{address}:{port_text}"
    try:
        return str(ipaddress.IPv4Address(value))
    except ValueError:
        return None


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
                ]
            )
        # Blacklist drops FIRST (F2 REMAINING MINOR #1): /block adds timed
        # elements to the declared blacklist_v4/blacklist_v6 sets. Sitting
        # them before the loopback/icmp/meters/management accepts means a
        # blocked source IP reaches NO host INPUT service — not even an
        # already-open port (22/80/443/51820) or a user-rule accept.
        # INPUT-only scope: forwarded/docker-published traffic from a
        # blacklisted IP is Docker's concern (its own forward chains), never
        # the viswall blacklist (F2 REMAINING MINOR #2).
        lines.append("        # Blacklist (host INPUT only, pre-accept precedence)")
        lines.append("        ip saddr @blacklist_v4 drop")
        lines.append("        ip6 saddr @blacklist_v6 drop")
        lines.extend(
            [
                "        # Loopback",
                '        iif "lo" accept',
                "        # ICMP / ICMPv6 rate limited (deliberate addition — live drops all icmp; parity rows A05/A06)",
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
            ]
        )
        # Docker bridge input accept — positioned AFTER the meters and the
        # management accepts exactly like live line 96 (live hashlimits
        # docker0-sourced ssh/http/https/wg too; an early accept would let
        # docker0 traffic bypass the meters). Precedes the 5432 drop, like
        # live (docker0 can reach the host's postgres socket).
        lines.append("        # Container bridges (docker coexistence) — live INPUT accepts docker0 only")
        lines.append('        iifname "docker0" accept')
        # F2 MAJOR #9: agent control ports (firewall :8081, vpn :8083, node
        # :8085) reachable from the bridge interfaces — the gateway container
        # dispatches to the host-net agents via host.docker.internal, which
        # arrives on a br-* bridge. Port-scoped and bridge-scoped, so only the
        # agent control surface opens, nothing else. Intentional addition (no
        # live equivalent — live had no host-net agents).
        lines.append('        iifname "docker0" tcp dport {8081, 8083, 8085} accept')
        lines.append('        iifname "br-*" tcp dport {8081, 8083, 8085} accept')
        lines.append("        # PostgreSQL never exposed")
        lines.append("        tcp dport 5432 drop")
        # User rules: ALWAYS after the mandatory accepts above (a console rule
        # can never override SSH/WG/established/lo access).
        lines.extend(self._user_rules(rules, "input"))
        if conntrack:
            # Invalid-state drop sits AFTER every accept: live had no invalid
            # rule at all, so invalids to open ports/lo/docker0 passed its
            # unqualified accepts; this explicit drop covers exactly the
            # live policy-DROP remainder.
            lines.append("        ct state invalid drop")
        if logging:
            lines.append('        log prefix "FIREWALL-DROP: " limit rate 5/minute drop')
        else:
            lines.append("        drop")
        lines.append("    }")
        return "\n".join(lines)

    def _render_prerouting(self, validation: bool, rules: List[FirewallRule]) -> str:
        """Raw prerouting chain — the live raw-PREROUTING home of the
        loopback guards and the container-IP anti-spoof drops.

        Both rule families must run PRE-DNAT (filter hook prerouting priority
        -300, before conntrack at -200 and docker's nat prerouting at -100):
        docker publishes container ports via DNAT, so at the input/forward
        hooks the destination is already rewritten. A post-DNAT guard misses
        the 127.0.0.1-published flows, and a post-DNAT anti-spoof rule also
        matches legitimate published-port flows (todo 39b: the forward-chain
        placement rendered in todo 7b dropped every WAN-published port).
        """
        if validation:
            return ""
        lines: List[str] = [
            "    chain raw_prerouting {",
            "        type filter hook prerouting priority -300; policy accept;",
        ]
        loop = self._loopback_ports(rules)
        anti_spoof = self._anti_spoof_lines(rules)
        if not loop and not anti_spoof:
            return ""
        if loop:
            lines.append("        # Loopback guards (live raw PREROUTING: -d 127.0.0.1/32 ! -i lo)")
            lines.append(
                f'        iifname != "lo" ip daddr 127.0.0.1 tcp dport {self._port_set(loop)} drop'
            )
        if anti_spoof:
            lines.append("        # Container-IP anti-spoof drops (live raw PREROUTING)")
            lines.extend(anti_spoof)
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
        ports = self._internal_ports(rules)
        # DOCKER-USER replacement, rendered BEFORE the bridge accepts: live
        # jumps to DOCKER-USER before DOCKER-FORWARD — a bridge accept first
        # would let WAN->published internal ports through. ``meta l4proto
        # tcp`` reproduces live's ``-p tcp`` scope (both families).
        lines.append("        # DOCKER-USER replacement: external access to internal ports")
        for wan in wan_ifaces or [DEFAULT_WAN]:
            lines.append(
                f'        iifname "{wan}" meta l4proto tcp ct direction original ct original proto-dst {self._port_set(ports)} drop'
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
                rendered = self._convert_nat_rule_to_nft(rule).rstrip("\n")
                if rendered:
                    lines.append(rendered)
        lines.append("    }")
        lines.extend(
            [
                "    chain postrouting {",
                "        type nat hook postrouting priority 90; policy accept;",
            ]
        )
        for rule in nat_rules:
            if rule.type == "snat" and rule.to_source and _valid_to_addr(rule.to_source):
                rendered = self._convert_nat_rule_to_nft(rule).rstrip("\n")
                if rendered:
                    lines.append(rendered)
            elif rule.type == "masquerade":
                # Docker owns NAT; viswall never emits masquerade (on WAN or anywhere).
                lines.append(f"        # masquerade skipped (docker owns NAT): {rule.name}")
        lines.append("    }")
        return "\n".join(lines)

    def _render_blacklist_sets(self) -> str:
        """Named sets the /block + /unblock endpoints add/delete elements in.

        Declared on EVERY render so a block right after an apply always has a
        set to insert into; the INPUT references are what make them enforce.
        """
        return (
            "    set blacklist_v4 {\n"
            "        type ipv4_addr\n"
            "        flags timeout\n"
            "    }\n"
            "    set blacklist_v6 {\n"
            "        type ipv6_addr\n"
            "        flags timeout\n"
            "    }\n"
        )

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
        parts.append(self._render_blacklist_sets())
        parts.append(self._render_prerouting(validation, firewall_rules))
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
            target = _normalize_to_addr(rule.to_destination) if rule.to_destination else None
            if target is None:
                return ""
            nft_rule += f"dnat to {target}"
        elif rule.type == "snat":
            target = _normalize_to_addr(rule.to_source) if rule.to_source else None
            if target is None:
                return ""
            nft_rule += f"snat to {target}"

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

            # F2 MAJOR #7: save the currently applied conf BEFORE overwriting
            # it. Delete-then-load leaves NO firewall when the new file fails
            # to load; the last-good copy is the undo point for that case.
            last_good = (
                Path(os.getenv("STATE_DIR", "/var/lib/viswall-firewall"))
                / "nftables.conf.last-good"
            )
            if conf_path.exists():
                shutil.copy2(conf_path, last_good)

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

            if proc.returncode != 0:
                logger.error(
                    "nft -f failed: %s — restoring last-good config",
                    stderr.decode(errors="replace").strip(),
                )
                if last_good.exists():
                    shutil.copy2(last_good, conf_path)
                    restore_proc = await asyncio.create_subprocess_exec(
                        "nft",
                        "-f",
                        str(conf_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    _, restore_stderr = await restore_proc.communicate()
                    if restore_proc.returncode != 0:
                        logger.error(
                            "last-good re-apply failed: %s",
                            restore_stderr.decode(errors="replace").strip(),
                        )
                return False

            return True

        except (OSError, ValueError) as exc:
            logger.error("failed to apply nftables: %s", exc)
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
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.error("nft list ruleset failed: %s", exc)
            return {}

    async def add_to_blacklist(self, ip: str, timeout: str = "1h") -> bool:
        """Dynamically add IP to blacklist (dual-stack aware)"""
        if not _valid_block_ip(ip) or not _valid_block_timeout(timeout):
            logger.warning("refusing to block invalid ip/timeout: %r %r", ip, timeout)
            return False
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
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.error("nft add element %s failed: %s", set_name, stderr.decode(errors="replace").strip())
            return proc.returncode == 0
        except OSError as exc:
            logger.error("nft add element failed: %s", exc)
            return False

    async def remove_from_blacklist(self, ip: str) -> bool:
        """Remove IP from blacklist (dual-stack aware)"""
        if not _valid_block_ip(ip):
            logger.warning("refusing to unblock invalid ip: %r", ip)
            return False
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
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.error("nft delete element %s failed: %s", set_name, stderr.decode(errors="replace").strip())
            return proc.returncode == 0
        except OSError as exc:
            logger.error("nft delete element failed: %s", exc)
            return False
