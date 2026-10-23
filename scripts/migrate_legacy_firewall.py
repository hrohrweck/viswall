#!/usr/bin/env python3
"""Legacy iptables-save importer -> Viswall console FirewallRule rows (plan todo 34).

Source of truth: the LIVE todo-3 captures (rules.v4.live / rules.v6.live) — never
the stale /etc/iptables/rules.v4 file (no DOCKER-FORWARD there, 48 MASQUERADE vs
65 live). A divergence report (stale vs live) prints before the plan.

Chain placement is NAME-TAGGED; the firewall agent derives chain/anti_spoof from
the row name (firewall-service api.py ``_rule_chain``, nft.py tag docs):
  "anti-spoof" in name -> forward chain; "internal-port" in name -> forward
  DOCKER-USER set; dest 127.0.0.1 + tcp/dport + drop -> input loopback guard;
  input + limit + meter dport -> managed meter.

Mapping: INPUT accepts -> accept rows (conntrack/lo/docker0/log lines skipped —
renderer hardcodes them); hashlimit lines -> rows with limit "N/minute burst M
packets" + the live hashlimit name; INPUT drops (5432, NOT the final policy) ->
drop rows; raw container-IP anti-spoof -> forward drop rows (bridge in
name/description); raw loopback guards -> input drop rows; DOCKER-USER -> ONE
aggregated row "docker-internal-port-protection"; FORWARD docker0/br-* + DOCKER*
plumbing -> not rows (renderer hardcodes); nat table -> NEVER imported
("docker-owned NAT (not imported)" report + duplicate-MASQUERADE detection,
live baseline for todo 48).

DRY-RUN by default: parse + print the plan, never opens a socket. --apply POSTs
rows (admin JWT from VISWALL_TOKEN, skips names that already exist — never
overwrites console rows); --rollback deletes only the rows in --import-manifest.
"""

# allow: SIZE_OK — plan todo 34 mandates exactly ONE file
# (scripts/migrate_legacy_firewall.py only); parse + map + report + API live
# here by design, and todo 37 imports it as a single module.

import argparse
import json
import os
import shlex
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_BACKUP = "/data/docker/persistent/backup/firewall-20261022-221901"
DEFAULT_API = "https://viswall.webmasters.co.at/api/v1"

DOCKER_CHAINS = ("DOCKER", "DOCKER-USER", "DOCKER-BRIDGE", "DOCKER-CT",
                 "DOCKER-FORWARD", "DOCKER-INTERNAL", "DOCKER-ISOLATION")

# Every iptables option that takes a value, mapped to its internal field name.
VALUE_FIELD = {
    "--ctstate": "ctstate", "--ctorigdstport": "ctorig", "--ctdir": "ctdir",
    "--hashlimit-above": "hl_rate", "--hashlimit-burst": "hl_burst",
    "--hashlimit-name": "hl_name", "--hashlimit-mode": "hl_mode",
    "--limit": "limit", "--log-prefix": "logprefix", "--dst-type": "addrtype",
    "--comment": "comment", "--to-destination": "todest", "--to-source": "tosrc",
}

# Open ports the migration must preserve (FIREWALL_MIGRATION_PLAN.md inventory).
EXPECTED_V4 = [(proto, port) for proto, ports in (
    ("tcp", (22, 25, 53, 80, 110, 143, 443, 993, 995, 21114, 21115, 21116, 21117, 21118, 21119)),
    ("udp", (53, 51820, 21116))) for port in ports]


class ParseError(ValueError):
    """An iptables-save line could not be parsed/classified (no silent drops)."""


class ApiError(RuntimeError):
    """A console API call failed; carries the HTTP status code."""

    def __init__(self, code: int, detail: str):
        self.code = code
        super().__init__(f"HTTP {code}: {detail}")


@dataclass(frozen=True)
class Rule:
    """One parsed -A line from an iptables-save dump."""
    table: str = ""
    chain: str = ""
    line: int = 0
    text: str = ""
    target: str = ""
    protocol: str = ""
    source: str = ""
    dest: str = ""
    in_iface: str = ""
    in_neg: bool = False
    out_iface: str = ""
    out_neg: bool = False
    dports: tuple = ()
    sports: tuple = ()
    opts: dict = field(default_factory=dict)


@dataclass
class Plan:
    """Import plan: rows to create, documented skips, NAT/MASQUERADE report."""
    row_meta: list = field(default_factory=list)          # [(kind, rowdict)]
    row_kinds: Counter = field(default_factory=Counter)   # (family, kind) -> n
    skips: dict = field(default_factory=dict)             # category -> [texts]
    unmapped: list = field(default_factory=list)
    internal_ports: set = field(default_factory=set)
    internal_lines: int = 0
    nat_lines: int = 0
    masquerade: Counter = field(default_factory=Counter)  # line text -> count

    @property
    def rows(self) -> list:
        return [row for _, row in self.row_meta]


def _int(text: str, num: int) -> int:
    try:
        return int(text)
    except ValueError:
        raise ParseError(f"line {num}: bad integer {text!r}") from None


def _ports(text: str, num: int) -> tuple:
    """Parse --dports/--sports (comma list, ranges with '-' or ':')."""
    out = []
    for part in text.replace(":", "-").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            low, _, high = part.partition("-")
            out.extend(range(_int(low, num), _int(high, num) + 1))
        else:
            out.append(_int(part, num))
    return tuple(out)


def parse_iptables_save(text: str) -> list:
    """Parse an iptables-save dump into Rule objects (hard fail on unknowns)."""
    rules, table = [], ""
    for num, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "COMMIT":
            table = ""  # lines outside a table block are unmapped, never inherited
            continue
        if line.startswith("*"):
            table = line[1:].strip()
            continue
        if line.startswith(":"):
            continue  # chain declaration/policy — never a row
        if not line.startswith("-A"):
            raise ParseError(f"line {num}: unsupported directive {line!r}")
        tokens = shlex.split(line)  # honors quoted values, e.g. --log-prefix "..."
        rule = dict(table=table, chain=tokens[1], line=num, text=line, target="",
                    protocol="", source="", dest="", in_iface="", in_neg=False,
                    out_iface="", out_neg=False, dports=(), sports=(), opts={})
        i, neg = 2, False
        while i < len(tokens):
            tok = tokens[i]
            if tok == "!":
                neg = True
                i += 1
                continue
            if tok == "-m":
                i += 2  # match module; its options carry the data
                continue
            if tok in ("-i", "--in-interface"):
                rule["in_iface"], rule["in_neg"] = tokens[i + 1], neg
            elif tok in ("-o", "--out-interface"):
                rule["out_iface"], rule["out_neg"] = tokens[i + 1], neg
            elif tok in ("-s", "--src"):
                rule["source"] = ("!" if neg else "") + tokens[i + 1]
            elif tok in ("-d", "--dst"):
                rule["dest"] = ("!" if neg else "") + tokens[i + 1]
            elif tok in ("-p", "--protocol"):
                rule["protocol"] = tokens[i + 1]
            elif tok in ("-j", "--jump", "-g", "--goto"):
                rule["target"] = tokens[i + 1]
            elif tok == "--dport":
                rule["dports"] += (_int(tokens[i + 1], num),)
            elif tok == "--dports":
                rule["dports"] += _ports(tokens[i + 1], num)
            elif tok == "--sport":
                rule["sports"] += (_int(tokens[i + 1], num),)
            elif tok == "--sports":
                rule["sports"] += _ports(tokens[i + 1], num)
            elif tok in VALUE_FIELD:
                rule["opts"][VALUE_FIELD[tok]] = tokens[i + 1]
            else:
                raise ParseError(f"line {num}: unknown token {tok!r}")
            neg = False
            i += 2
        rules.append(Rule(**rule))
    return rules


def classify(rule: Rule) -> tuple:
    """Classify one rule line: (kind, data) with kind row/skip/agg/unmapped."""
    table, chain = rule.table, rule.chain
    if table == "nat":
        return "skip", {"cat": "docker-owned NAT (not imported)"}
    if table == "raw" and chain == "PREROUTING":
        if (rule.dest == "127.0.0.1/32" and rule.in_neg and rule.in_iface == "lo"
                and rule.protocol == "tcp" and rule.dports and rule.target == "DROP"):
            return "row", {"kind": "loopback"}
        if (rule.in_neg and rule.in_iface and rule.dest and rule.target == "DROP"
                and not rule.protocol and not rule.dports):
            return "row", {"kind": "antispoof"}
        return "unmapped", {}
    if table != "filter":
        return "unmapped", {}
    ctstate = rule.opts.get("ctstate", "")
    if chain == "INPUT":
        if "RELATED" in ctstate or "ESTABLISHED" in ctstate:
            return "skip", {"cat": "conntrack-established accept (renderer hardcodes)"}
        if rule.in_iface == "lo" and not rule.in_neg:
            return "skip", {"cat": "loopback accept (renderer hardcodes)"}
        if not rule.in_neg and (rule.in_iface == "docker0" or rule.in_iface.startswith("br-")):
            return "skip", {"cat": "docker bridge INPUT accept (renderer hardcodes)"}
        if rule.opts.get("logprefix"):
            return "skip", {"cat": "FIREWALL-DROP log line (renderer hardcodes)"}
        if rule.opts.get("hl_name"):
            return "row", {"kind": "meter"}
        if rule.dports and rule.target == "ACCEPT":
            return "row", {"kind": "accept"}
        if rule.dports and rule.target == "DROP":
            return "row", {"kind": "drop"}
        return "unmapped", {}
    if chain == "FORWARD":
        if (rule.target in DOCKER_CHAINS
                or rule.in_iface == "docker0" or rule.in_iface.startswith("br-")
                or rule.out_iface == "docker0" or rule.out_iface.startswith("br-")
                or "RELATED" in ctstate):
            return "skip", {"cat": "docker FORWARD plumbing (renderer hardcodes)"}
        return "unmapped", {}
    if chain == "DOCKER-USER":
        if rule.opts.get("ctorig"):
            return "agg", {"port": _int(rule.opts["ctorig"], rule.line)}
        return "unmapped", {}
    if chain in DOCKER_CHAINS:
        return "skip", {"cat": "docker-owned chain"}
    return "unmapped", {}


def _row(name, desc, *, proto="tcp", ports=None, dst=("any", None),
         action="accept", limit=None) -> dict:
    """One FirewallRuleCreate payload (shared/schemas.py field names)."""
    return {"name": name, "description": desc, "enabled": True,
            "source_type": "any", "source_value": None,
            "dest_type": dst[0], "dest_value": dst[1],
            "service_protocol": proto, "service_ports": ports,
            "action": action, "log_enabled": False, "limit": limit}


def build_rows(rule: Rule, data: dict, family: str) -> list:
    """Build [(kind, rowdict)] for one classified rule line."""
    kind = data["kind"]
    sfx = " (ipv6)" if family == "v6" else ""
    proto = rule.protocol or "any"
    if kind == "meter":
        rate = rule.opts["hl_rate"].replace("/min", "/minute")
        limit = f"{rate} burst {rule.opts.get('hl_burst', '5')} packets"
        row = _row(rule.opts["hl_name"],
                   f"hashlimit {rule.opts['hl_rate']} burst {rule.opts.get('hl_burst', '')} "
                   f"from live {family} capture ({rule.text})",
                   proto=proto, ports=",".join(str(p) for p in rule.dports),
                   action="drop", limit=limit)
        return [("meter", row)]
    if kind == "loopback":
        port = rule.dports[0]
        return [("loopback-guard", _row(
            f"loopback-guard tcp/{port}", f"live {family} raw guard: {rule.text}",
            proto="tcp", ports=str(port), dst=("host", "127.0.0.1"), action="drop"))]
    if kind == "antispoof":
        return [("anti-spoof", _row(
            f"anti-spoof {rule.dest.partition('/')[0]} via {rule.in_iface}",
            f"live {family} raw anti-spoof: {rule.text}", proto="any",
            dst=("network", rule.dest), action="drop"))]
    if kind == "accept":
        return [("accept", _row(f"allow {proto}/{p}{sfx}",
                                f"live {family} INPUT accept ({rule.text})",
                                proto=proto, ports=str(p))) for p in rule.dports]
    if kind == "drop":
        return [("drop", _row(f"drop {proto}/{p}{sfx}",
                              f"live {family} INPUT explicit drop ({rule.text})",
                              proto=proto, ports=str(p), action="drop"))
                for p in rule.dports]
    raise ParseError(f"unknown row kind {kind!r}")


def internal_protection_row(plan: Plan) -> tuple:
    """Aggregate every live DOCKER-USER ctorigdstport into ONE named row."""
    ports = sorted(plan.internal_ports)
    text = ", ".join(str(p) for p in ports)
    row = _row("docker-internal-port-protection",
               f"migrated from live DOCKER-USER ({plan.internal_lines} lines, "
               f"iif enp0s31f6, ct direction original, ctorigdstport): {text}",
               proto="tcp", ports=",".join(str(p) for p in ports), action="drop")
    return ("internal-port-protection", row)


def classify_into(plan: Plan, rule: Rule, family: str) -> None:
    kind, data = classify(rule)
    if kind == "unmapped":
        plan.unmapped.append(f"{family} line {rule.line}: {rule.text}")
        return
    if kind == "skip":
        if data["cat"].startswith("docker-owned NAT"):
            plan.nat_lines += 1
            if "MASQUERADE" in rule.text:
                plan.masquerade[rule.text] += 1
        plan.skips.setdefault(data["cat"], []).append(f"{family}:{rule.line}: {rule.text}")
        return
    if kind == "agg":
        plan.internal_ports.add(data["port"])
        plan.internal_lines += 1
        return
    for row_kind, row in build_rows(rule, data, family):
        plan.row_meta.append((row_kind, row))
        plan.row_kinds[(family, row_kind)] += 1


def build_plan(args: argparse.Namespace) -> Plan:
    plan = Plan()
    for family, path in (("v4", args.rules_file), ("v6", args.rules6_file)):
        try:
            text = Path(path).read_text()
        except OSError as exc:
            raise SystemExit(f"error reading capture {path}: {exc}") from exc
        for rule in parse_iptables_save(text):
            classify_into(plan, rule, family)
    if plan.internal_ports:
        kind, row = internal_protection_row(plan)
        plan.row_meta.append((kind, row))
        plan.row_kinds[("agg", kind)] += 1
    return plan


def divergence_report(live_text: str, label: str, stale_path: str) -> None:
    """Diff the stale /etc/iptables file against the live capture (-A lines)."""
    if not stale_path or not Path(stale_path).is_file():
        print(f"divergence [{label}]: no stale file at {stale_path} (skipped)")
        return
    live = {l for l in live_text.splitlines() if l.startswith("-A")}
    stale = {l for l in Path(stale_path).read_text().splitlines() if l.startswith("-A")}
    print(f"divergence [{label}] stale={stale_path}: -A lines live={len(live)} "
          f"stale={len(stale)}; only-in-live={len(live - stale)} "
          f"only-in-stale={len(stale - live)}")


def print_report(plan: Plan, args: argparse.Namespace) -> None:
    print("==================== FIREWALL MIGRATION PREVIEW (todo 34) ====================")
    print(f"sources: v4={args.rules_file}\n         v6={args.rules6_file}")
    print(f"rows planned: {len(plan.rows)}")
    kinds = (("accept", "input accepts"),
             ("meter", "rate-limit meters (hashlimit -> limit)"),
             ("drop", "input drops"),
             ("loopback-guard", "loopback guards (127.0.0.1, iifname != lo)"),
             ("anti-spoof", "container-IP anti-spoof (forward chain)"),
             ("internal-port-protection", "DOCKER-USER aggregation"))
    for kind, label in kinds:
        fam = Counter(f for (f, k), c in plan.row_kinds.items() if k == kind for _ in range(c))
        line = f"  {label}: {fam.total()}"
        if fam["v6"]:
            line += f"  (v4 {fam['v4']} + v6 {fam['v6']})"
        print(line)
    for kind, row in plan.row_meta:
        if kind == "meter":
            print(f"    meter {row['name']}: limit={row['limit']}")
    got = {(r["service_protocol"], int(p)) for kind, r in plan.row_meta if kind == "accept"
           for p in str(r["service_ports"]).split(",")}
    missing = [f"{proto}/{port}" for proto, port in EXPECTED_V4 if (proto, port) not in got]
    verdict = "ALL PRESENT" if not missing else f"MISSING: {missing}"
    print(f"  inventory check (FIREWALL_MIGRATION_PLAN.md open ports): "
          f"{len(EXPECTED_V4) - len(missing)}/{len(EXPECTED_V4)} present — {verdict}")
    print("skipped by documented category:")
    for cat, texts in plan.skips.items():
        print(f"  {cat}: {len(texts)}" + (f"  e.g. {texts[0]}" if texts else ""))
    print(f"docker-owned NAT (not imported): {plan.nat_lines} lines")
    total = plan.masquerade.total()
    if total:
        print(f"  MASQUERADE lines total: {total} — docker-owned, NOT imported")
        for text, count in plan.masquerade.items():
            if count > 1:
                print(f"  !!! DUPLICATE MASQUERADE DETECTED: {count} identical lines -> {text}")
        print(f"  !!! LIVE BASELINE for todo 48: MASQUERADE count = {total} "
              f"(docker re-creates these on restart; duplicates are expected, not imported)")


def _token() -> str:
    token = os.environ.get("VISWALL_TOKEN", "")
    if not token:
        raise SystemExit("VISWALL_TOKEN (admin JWT) is required for --apply/--rollback")
    return token


def _http(method: str, url: str, token: str, body=None) -> dict:
    """One console API call. Imported lazily so dry-run never touches sockets."""
    import urllib.error
    import urllib.request
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method,
                                     headers={"Authorization": f"Bearer {token}",
                                              "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
    except urllib.error.HTTPError as exc:
        raise ApiError(exc.code, exc.read().decode(errors="replace")[:400]) from exc
    except urllib.error.URLError as exc:
        raise ApiError(0, f"{method} {url} -> {exc.reason}") from exc
    return json.loads(payload) if payload else {}


def _load_manifest(path: str) -> dict:
    p = Path(path)
    if p.is_file():
        try:
            data = json.loads(p.read_text())
            return data if isinstance(data, dict) else {}
        except ValueError:
            print(f"WARNING: unparseable manifest {path}; starting fresh")
    return {}


def _save_manifest(path: str, manifest: dict) -> None:
    Path(path).write_text(json.dumps(manifest, indent=2) + "\n")


def apply_rows(rows: list, args: argparse.Namespace) -> int:
    token = _token()
    base = args.api_url.rstrip("/")
    existing = _http("GET", f"{base}/firewall/rules/{args.instance_id}", token)
    names = {r["name"] for r in existing}
    manifest = _load_manifest(args.import_manifest)
    created = manifest.setdefault("created", [])
    run = 0
    for row in rows:
        if row["name"] in names:
            print(f"  SKIP (name exists; console row preserved): {row['name']}")
            continue
        response = _http("POST", f"{base}/firewall/rules/{args.instance_id}", token, row)
        created.append({"name": row["name"], "id": response["id"]})
        names.add(row["name"])
        run += 1
        print(f"  created rule id={response['id']} name={row['name']}")
    manifest.update(instance_id=args.instance_id, applied_at=int(time.time()),
                    created=created)
    _save_manifest(args.import_manifest, manifest)
    print(f"\n[apply] created this run: {run} | total in manifest: {len(created)} | "
          f"manifest={args.import_manifest}")
    return 0


def rollback_rows(args: argparse.Namespace) -> int:
    if not Path(args.import_manifest).is_file():
        print(f"FATAL: import manifest {args.import_manifest} not found; "
              f"cannot determine which rows to roll back")
        return 4
    token = _token()
    base = args.api_url.rstrip("/")
    manifest = _load_manifest(args.import_manifest)
    deleted = missing = 0
    for entry in manifest.get("created", []):
        try:
            _http("DELETE", f"{base}/firewall/rules/{entry['id']}", token)
            deleted += 1
            print(f"  deleted rule id={entry['id']} name={entry.get('name')}")
        except ApiError as exc:
            if exc.code == 404:
                missing += 1
                print(f"  already gone id={entry['id']} name={entry.get('name')}")
                continue
            raise
    manifest["rolled_back_at"] = int(time.time())
    _save_manifest(args.import_manifest, manifest)
    print(f"\n[rollback] deleted {deleted} rows, already gone {missing}; manifest kept")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Import legacy iptables-save into viswall console")
    ap.add_argument("--rules-file", default=os.path.join(DEFAULT_BACKUP, "rules.v4.live"))
    ap.add_argument("--rules6-file", default=os.path.join(DEFAULT_BACKUP, "rules.v6.live"))
    ap.add_argument("--stale4-file", default="/etc/iptables/rules.v4")
    ap.add_argument("--stale6-file", default="/etc/iptables/rules.v6")
    ap.add_argument("--instance-id", type=int, default=int(os.environ.get("INSTANCE_ID", "1")))
    ap.add_argument("--api-url", default=os.environ.get("VISWALL_API_URL", DEFAULT_API))
    ap.add_argument("--import-manifest",
                    default=str(Path(__file__).resolve().parent / "firewall_import_manifest.json"))
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true",
                      help="default: parse and print the plan; no API, no writes")
    mode.add_argument("--apply", action="store_true",
                      help="POST planned rows (skips names that already exist)")
    mode.add_argument("--rollback", action="store_true",
                      help="DELETE the rows recorded in --import-manifest")
    args = ap.parse_args()

    if args.rollback:
        return rollback_rows(args)  # manifest-only; no capture parsing needed

    try:
        v4_text = Path(args.rules_file).read_text()
        v6_text = Path(args.rules6_file).read_text()
    except OSError as exc:
        print(f"error reading capture: {exc}")
        return 1
    divergence_report(v4_text, "v4", args.stale4_file)
    divergence_report(v6_text, "v6", args.stale6_file)

    try:
        plan = build_plan(args)
    except ParseError as exc:
        print(f"FATAL: parse/classification error: {exc}")
        return 1

    print_report(plan, args)
    if plan.unmapped:
        print(f"\nFATAL: {len(plan.unmapped)} line(s) could not be mapped "
              f"(no silent drops allowed):")
        for line in plan.unmapped:
            print(f"  {line}")
        return 1
    try:
        if args.apply:
            return apply_rows(plan.rows, args)
        if args.rollback:
            return rollback_rows(args)
    except ApiError as exc:
        print(f"FATAL: API error: {exc}")
        return 3
    print("\nmode: DRY-RUN — no API calls, no writes. Use --apply (VISWALL_TOKEN) "
          "or --rollback.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
