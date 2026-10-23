#!/usr/bin/env python3
"""Firewall parity gate — the cutover's HARD GATE (plan todo 44 step 5).

Compares the legacy iptables surface that the viswall firewall replaces with the
*rendered* ``table inet viswall`` ruleset, mechanically, and exits non-zero on
any unexplained difference. The human-readable companion is
``docs/firewall-parity-checklist.md`` (todo 39); this tool is the assertion the
cutover runbook requires ("the INPUT parity diff ... 100 percent PASS").

What is compared (per family, v4 and v6):

  * INPUT accepts       every (proto, port) the legacy INPUT chain accepts must
                        be accepted by the rendered table (extras are only the
                        documented agent-control ports on docker bridges);
  * INPUT drops         every (proto, port) the legacy INPUT chain drops must be
                        dropped (5432); stricter extras are reported, not failed;
  * named meters        every legacy ``--hashlimit-name`` must exist with the
                        same rate (the ``limit rate over`` inversion counts);
  * loopback guards     the exact port set from raw PREROUTING
                        (-d 127.0.0.1/32 ! -i lo --dport N -j DROP);
  * Docker internal     the exact 17-port DOCKER-USER set, rendered as the
                        forward chain's ``ct original proto-dst`` drop;
  * anti-spoof          the exact count of container-IP PREROUTING drops;
  * chain policies      input/forward must be ``policy drop``, output and
                        raw_prerouting ``policy accept``.

Usage in the window (after the real ruleset is applied):
    nft list table inet viswall > /tmp/viswall.nft
    python3 scripts/firewall_parity_gate.py \
        --rules-v4 /etc/iptables/rules.v4 --rules-v6 /etc/iptables/rules.v6 \
        --nft-table /tmp/viswall.nft

Offline / pre-window dry run (renders the desired real-mode ruleset in-process
from the live capture; no host change):
    python3 scripts/firewall_parity_gate.py --render

Exit: 0 = ALL PASS; 1 = at least one DIFF; 2 = usage/input error.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Iterable

DEFAULT_CAPTURE_DIR = Path("/data/docker/persistent/backup/firewall-20261022-221901")

#: Rendered-side accepts that are intentional additions (agent control ports on
#: the docker bridges) rather than legacy INPUT accepts. Everything else that is
#: accepted by the table but absent from iptables is a DIFF.
ALLOWED_EXTRA_ACCEPTS = {
    # The agent-control accepts are rendered on bare docker-bridge rules, which
    # match both families in an inet table.
    (family, "tcp", port)
    for family in ("v4", "v6")
    for port in (8081, 8083, 8085)
}

#: Rendered-side drop that is stricter than the live capture on v6 because the
#: bare ``tcp dport 5432 drop`` line matches both families in an inet table.
#: The checklist documents 5432 as never exposed, so this is accepted.
ALLOWED_EXTRA_DROPS = {("v6", "tcp", 5432)}


def _expand_ports(text: str) -> set[int]:
    """Expand an iptables/nft port list (``22,53,21114-21119``)."""
    ports: set[int] = set()
    for chunk in text.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            lo, hi = chunk.split("-", 1)
            ports.update(range(int(lo), int(hi) + 1))
        else:
            ports.add(int(chunk))
    return ports


def _opt(tokens: list[str], name: str) -> str | None:
    """Return the value following ``name`` in a tokenized rule, else None."""
    try:
        return tokens[tokens.index(name) + 1]
    except (ValueError, IndexError):
        return None


def _norm_rate(rate: str) -> str:
    """Normalize ``10/min`` → ``10/minute`` (unit plural)."""
    units = {
        "s": "second", "sec": "second", "second": "second", "seconds": "second",
        "m": "minute", "min": "minute", "minute": "minute", "minutes": "minute",
        "h": "hour", "hour": "hour", "hours": "hour",
        "d": "day", "day": "day", "days": "day",
    }
    match = re.fullmatch(r"(\d+)/(\w+)", rate.strip())
    if not match:
        return rate.strip()
    amount, unit = match.groups()
    return f"{amount}/{units.get(unit.lower(), unit)}"


def _is_accept_rule(tokens: list[str]) -> bool:
    return _opt(tokens, "-j") == "ACCEPT"


def _is_drop_rule(tokens: list[str]) -> bool:
    return _opt(tokens, "-j") == "DROP"


def _rule_ports(tokens: list[str]) -> set[int]:
    single = _opt(tokens, "--dport")
    if single:
        return {int(single)}
    multi = _opt(tokens, "--dports")
    if multi:
        return _expand_ports(multi)
    return set()


class Expected:
    """The legacy iptables surface, per family."""

    def __init__(self) -> None:
        self.accepts: set[tuple[str, str, int]] = set()
        self.drops: set[tuple[str, str, int]] = set()
        self.meters: dict[str, str] = {}
        self.guards: set[int] = set()
        self.internal: set[int] = set()
        self.antisp00f = 0

    def add_iptables(self, text: str, family: str) -> None:
        for line in text.splitlines():
            if not line.startswith("-A "):
                continue
            tokens = line.split()
            chain = tokens[1]
            proto = _opt(tokens, "-p") or "all"

            if chain == "INPUT":
                name = _opt(tokens, "--hashlimit-name")
                if name:
                    rate = _opt(tokens, "--hashlimit-above")
                    if rate:
                        self.meters[name] = _norm_rate(rate)
                    continue
                if proto not in ("tcp", "udp"):
                    continue
                ports = _rule_ports(tokens)
                if not ports:
                    continue  # established / lo / docker0 accepts carry no dport
                for port in ports:
                    if _is_accept_rule(tokens):
                        self.accepts.add((family, proto, port))
                    elif _is_drop_rule(tokens):
                        self.drops.add((family, proto, port))

            elif chain == "PREROUTING":
                dest = _opt(tokens, "-d") or ""
                dport = _opt(tokens, "--dport")
                if _is_drop_rule(tokens) and dest == "127.0.0.1/32" and dport:
                    self.guards.add(int(dport))
                elif _is_drop_rule(tokens) and dest and dest != "127.0.0.1/32":
                    self.antisp00f += 1

            elif chain == "DOCKER-USER":
                ct_port = _opt(tokens, "--ctorigdstport")
                if ct_port and _is_drop_rule(tokens):
                    self.internal.add(int(ct_port))


class Actual:
    """The rendered ``table inet viswall`` surface."""

    def __init__(self) -> None:
        self.accepts: set[tuple[str, str, int]] = set()
        self.drops: set[tuple[str, str, int]] = set()
        self.meters: dict[str, str] = {}
        self.guards: set[int] = set()
        self.internal: set[int] = set()
        self.antisp00f = 0
        self.policies: dict[str, str] = {}

    @staticmethod
    def _families(line: str) -> tuple[str, ...]:
        """A bare rule matches both families in an inet table."""
        if "nfproto ipv6" in line or re.search(r"\bip6\b", line):
            return ("v6",)
        if "nfproto ipv4" in line or re.search(r"\bip protocol\b", line):
            return ("v4",)
        return ("v4", "v6")

    @staticmethod
    def _ports(line: str) -> set[int]:
        match = re.search(r"(?:tcp|udp) dport \{([^}]*)\}", line)
        if match:
            return _expand_ports(match.group(1))
        match = re.search(r"(?:tcp|udp) dport (\d+)", line)
        return {int(match.group(1))} if match else set()

    @staticmethod
    def _proto_dst_ports(line: str) -> set[int]:
        """DOCKER-USER replacement: ``ct original proto-dst {a, b, ...}``."""
        match = re.search(r"ct original proto-dst \{([^}]*)\}", line)
        return _expand_ports(match.group(1)) if match else set()

    @staticmethod
    def _proto(line: str) -> str | None:
        if "tcp dport" in line or "meta l4proto tcp" in line:
            return "tcp"
        if "udp dport" in line:
            return "udp"
        return None

    def add_nft_text(self, text: str) -> None:
        chain: str | None = None
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r"chain (\w+) \{", line)
            if match:
                chain = match.group(1)
                continue
            if line == "}" or line.startswith("},"):
                chain = None
                continue
            match = re.search(r"type filter hook \w+ priority -?\d+; policy (\w+);", line)
            if match and chain:
                self.policies[chain] = match.group(1)
                continue
            if chain is None:
                continue

            proto = self._proto(line)
            ports = self._ports(line)

            # Named meters: `meter ssh_limit { ip saddr limit rate over R/unit ... }`
            if "meter " in line:
                meter = re.search(r"meter (\w+)", line)
                rate = re.search(r"limit rate (?:over )?(\d+/\w+)", line)
                if meter and rate:
                    self.meters[meter.group(1)] = _norm_rate(rate.group(1))
                continue

            if chain == "raw_prerouting":
                if 'iifname != "lo" ip daddr 127.0.0.1' in line and proto == "tcp":
                    self.guards |= ports
                elif re.search(r'iifname != "[^"]+" ip6? daddr \S+ drop', line):
                    self.antisp00f += 1
                continue

            if chain == "forward":
                if "ct original proto-dst" in line:
                    self.internal |= self._proto_dst_ports(line)
                continue

            if chain != "input":
                continue

            if _is_accept_line(line) and proto and ports:
                for family in self._families(line):
                    self.accepts |= {(family, proto, port) for port in ports}
            elif _is_drop_line(line) and proto and ports:
                for family in self._families(line):
                    self.drops |= {(family, proto, port) for port in ports}


def _is_accept_line(line: str) -> bool:
    return re.search(r"(?:^|[\s}])accept$", line) is not None


def _is_drop_line(line: str) -> bool:
    if "limit rate" in line:  # meter / log+limit rules are not plain drops
        return False
    return re.search(r"(?:^|[\s}])drop$", line) is not None


def render_desired(rules_v4: Path, rules_v6: Path) -> str:
    """Render the real-mode (non-validation) ruleset from a live capture.

    Offline mirror of the agent's /firewall/apply path: importer plan → gateway
    payload rows → ``_rules_from_payload`` → ``generate_ruleset``. Validation
    mode is forced off for this process only.
    """
    import argparse as _argparse
    import importlib.util

    scripts_dir = Path(__file__).resolve().parent
    repo = scripts_dir.parent

    spec = importlib.util.spec_from_file_location(
        "viswall_migrate_legacy_firewall", scripts_dir / "migrate_legacy_firewall.py"
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise SystemExit("cannot load the legacy importer")
    importer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(importer)

    args = _argparse.Namespace(
        rules_file=str(rules_v4),
        rules6_file=str(rules_v6),
        stale4_file="",
        stale6_file="",
        instance_id=1,
        api_url="unused",
        import_manifest="/nonexistent",
    )
    plan = importer.build_plan(args)

    agent_pkg = repo / "services" / "firewall-service"
    if str(agent_pkg) not in sys.path:
        sys.path.insert(0, str(agent_pkg))
    os.environ["VALIDATION_MODE"] = "0"
    from viswall_firewall_agent.api import _rules_from_payload  # noqa: PLC0415
    from viswall_firewall_agent.nft import NFTablesManager  # noqa: PLC0415

    rules = []
    for index, row in enumerate(plan.rows):
        rules.extend(_rules_from_payload(row, index))

    return NFTablesManager().generate_ruleset(
        interfaces=[{"name": "enp0s31f6", "type": "wan"}],
        firewall_rules=rules,
        nat_rules=[],
    )


def compare(expected: Expected, actual: Actual) -> list[str]:
    """Return PASS/DIFF lines; any line starting with DIFF fails the gate."""
    lines: list[str] = []

    def fail(message: str) -> None:
        lines.append(f"DIFF {message}")

    def ok(message: str) -> None:
        lines.append(f"PASS {message}")

    missing_accepts = expected.accepts - actual.accepts
    extra_accepts = actual.accepts - expected.accepts - ALLOWED_EXTRA_ACCEPTS
    if missing_accepts:
        for family, proto, port in sorted(missing_accepts):
            fail(f"accept missing: {family} {proto}/{port}")
    if extra_accepts:
        for family, proto, port in sorted(extra_accepts):
            fail(f"accept unexpected (port opened): {family} {proto}/{port}")
    if not missing_accepts and not extra_accepts:
        ok(f"accepts: {len(expected.accepts)} legacy ports present, "
           f"{len(ALLOWED_EXTRA_ACCEPTS)} documented agent ports added")

    missing_drops = expected.drops - actual.drops
    extra_drops = actual.drops - expected.drops - ALLOWED_EXTRA_DROPS
    if missing_drops:
        for family, proto, port in sorted(missing_drops):
            fail(f"drop missing: {family} {proto}/{port}")
    if extra_drops:
        for family, proto, port in sorted(extra_drops):
            fail(f"drop unexpected (port blocked): {family} {proto}/{port}")
    if not missing_drops and not extra_drops:
        ok(f"drops: {len(expected.drops)} legacy drop(s) enforced")

    for name, rate in sorted(expected.meters.items()):
        if name not in actual.meters:
            fail(f"meter missing: {name} ({rate})")
        elif actual.meters[name] != rate:
            fail(f"meter rate: {name} expected {rate}, rendered {actual.meters[name]}")
    extras = set(actual.meters) - set(expected.meters)
    for name in sorted(extras):
        fail(f"meter unexpected: {name}")
    if set(expected.meters) <= set(actual.meters) and not extras and all(
        actual.meters[name] == rate for name, rate in expected.meters.items()
    ):
        ok(f"meters: {len(expected.meters)} at exact rates")

    if expected.guards != actual.guards:
        fail(f"loopback guards: expected {sorted(expected.guards)}, rendered {sorted(actual.guards)}")
    else:
        ok(f"loopback-guards: {len(expected.guards)}")

    if expected.internal != actual.internal:
        fail(f"docker internal ports: expected {sorted(expected.internal)}, "
             f"rendered {sorted(actual.internal)}")
    else:
        ok(f"docker-internal-port-protection: {len(expected.internal)} ports")

    if expected.antisp00f != actual.antisp00f:
        fail(f"anti-spoof: expected {expected.antisp00f} drops, rendered {actual.antisp00f}")
    else:
        ok(f"anti-spoof: {expected.antisp00f}")

    for chain, required in (("input", "drop"), ("forward", "drop"),
                            ("output", "accept"), ("raw_prerouting", "accept")):
        policy = actual.policies.get(chain)
        if policy != required:
            fail(f"policy: chain {chain} is {policy!r}, expected {required!r}")
    if all(actual.policies.get(c) == p for c, p in
           (("input", "drop"), ("forward", "drop"), ("output", "accept"),
            ("raw_prerouting", "accept"))):
        ok("chain policies: input/forward drop, output/raw_prerouting accept")

    return lines


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rules-v4", default=str(DEFAULT_CAPTURE_DIR / "rules.v4.live"))
    parser.add_argument("--rules-v6", default=str(DEFAULT_CAPTURE_DIR / "rules.v6.live"))
    parser.add_argument("--nft-table", help="output of `nft list table inet viswall`")
    parser.add_argument("--render", action="store_true",
                        help="render the desired real-mode ruleset from the capture "
                             "(offline dry run; no host change)")
    args = parser.parse_args(list(argv) if argv is not None else None)

    rules_v4, rules_v6 = Path(args.rules_v4), Path(args.rules_v6)
    if not rules_v4.is_file() or not rules_v6.is_file():
        print(f"error: capture file missing: {rules_v4} / {rules_v6}", file=sys.stderr)
        return 2

    if args.nft_table:
        try:
            nft_text = Path(args.nft_table).read_text()
        except OSError as exc:
            print(f"error reading nft table: {exc}", file=sys.stderr)
            return 2
    elif args.render:
        nft_text = render_desired(rules_v4, rules_v6)
    else:
        print("error: pass --nft-table FILE (live table) or --render (offline dry run)",
              file=sys.stderr)
        return 2

    expected = Expected()
    expected.add_iptables(rules_v4.read_text(), "v4")
    expected.add_iptables(rules_v6.read_text(), "v6")

    actual = Actual()
    actual.add_nft_text(nft_text)

    lines = compare(expected, actual)
    print("\n".join(lines))
    diffs = sum(1 for line in lines if line.startswith("DIFF"))
    print(f"\nverdict: {'ALL PASS' if diffs == 0 else f'{diffs} DIFF'}")
    return 0 if diffs == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
