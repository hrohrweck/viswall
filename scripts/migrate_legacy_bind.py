#!/usr/bin/env python3
"""
Migrate legacy Webmin/BIND zone files (dns1) -> Viswall console DNS module.

Source: /data/docker/persistent/dns1/bind/lib/<zone>.hosts (Webmin-managed
master files: $ttl + SOA/NS/MX/TXT/A records, wildcards).

Target: viswall api-gateway DNS API — one DNSServer under the instance plus
one zone per file with an explicit SOA record (preserves
dns1.grafixpromo.com mname / admin.webmasters.co.at rname; the agent skips
its generated default SOA when a SOA record is present) and bulk-imported
records (<=500 per call).

Server options mirror legacy dns1: recursion refused, AXFR + notify to
93.111.66.28 (dns2.grafixpromo.com — kept, per operator decision 2026-09-05).

DRY-RUN by default: prints the planned API payloads. --apply executes.
Auth: admin username/password (VISWALL_PASSWORD env) or a pre-minted --token.

Run: uv run --with dnspython,httpx scripts/migrate_legacy_bind.py [--apply]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import dns.rdatatype
import dns.zone
import httpx

BULK_LIMIT = 500


@dataclass(frozen=True)
class ZonePlan:
    origin: str
    refresh: int
    retry: int
    expire: int
    minimum_ttl: int
    records: list[dict[str, Any]] = field(default_factory=list)

    @property
    def non_soa_records(self) -> list[dict[str, Any]]:
        return [r for r in self.records if r["record_type"] != "SOA"]


@dataclass(frozen=True)
class MigrationPlan:
    server: dict[str, Any]
    zones: list[ZonePlan]


def rdata_text(rtype: str, rdata: Any) -> str:
    """Content WITHOUT priority fields — the agent renders those itself."""
    match rtype:
        case "MX":
            return str(rdata.exchange)
        case "SRV":
            return str(rdata.target)
        case _:
            return str(rdata)


def rdata_priority(rtype: str, rdata: Any) -> int:
    match rtype:
        case "MX":
            return int(rdata.preference)
        case "SRV":
            return int(rdata.priority)
        case _:
            return 0


def rdata_weight_port(rtype: str, rdata: Any) -> tuple[int, int]:
    match rtype:
        case "SRV":
            return int(rdata.weight), int(rdata.port)
        case _:
            return 0, 0


def record_name(name: dns.name.Name, origin: dns.name.Name) -> str:
    if name == dns.name.empty:
        return "@"
    relative = name.relativize(origin)
    return str(relative)


def zone_records(zone: dns.zone.Zone, origin: dns.name.Name) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for name, rds in zone.iterate_rdatasets():
        rtype = dns.rdatatype.to_text(rds.rdtype)
        label = record_name(name, origin)
        weight, port = 0, 0
        for rdata in rds:
            priority = rdata_priority(rtype, rdata)
            if rtype == "SRV":
                weight, port = rdata_weight_port(rtype, rdata)
            records.append(
                {
                    "name": label,
                    "record_type": rtype,
                    "content": rdata_text(rtype, rdata),
                    "ttl": rds.ttl,
                    "priority": priority,
                    "weight": weight,
                    "port": port,
                    "is_system": rtype in {"SOA", "NS"},
                }
            )
    return records


def parse_zone_file(path: Path) -> ZonePlan:
    origin = dns.name.from_text(path.name.removesuffix(".hosts"))
    zone = dns.zone.from_file(str(path), origin=origin, relativize=True)
    soa = zone.get_rdataset("@", "SOA")[0]
    records = zone_records(zone, origin)
    return ZonePlan(
        origin=str(origin).rstrip("."),
        refresh=soa.refresh,
        retry=soa.retry,
        expire=soa.expire,
        minimum_ttl=soa.minimum,
        records=records,
    )


def _ensure_fqdn(value: str) -> str:
    return value if value.endswith(".") else f"{value}."


def skip_server_ns_duplicate(zones: list[ZonePlan], server_name_fqdn: str) -> None:
    """Drop the migrated NS that duplicates create_zone's auto system NS.

    delete_record refuses system records, so the import keeps the auto NS for
    the server's own name and migrates only the remaining NS records.
    """
    for zone in zones:
        filtered = [
            r
            for r in zone.records
            if not (r["record_type"] == "NS" and r["content"] == server_name_fqdn)
        ]
        zones[zones.index(zone)] = replace(zone, records=filtered)


def build_plan(args: argparse.Namespace) -> MigrationPlan:
    zones = [parse_zone_file(p) for p in sorted(Path(args.zones_dir).glob("*.hosts"))]
    if not zones:
        raise SystemExit(f"no *.hosts zone files found in {args.zones_dir}")
    skip_server_ns_duplicate(zones, _ensure_fqdn(args.server_name))
    server = {
        "name": args.server_name,
        "description": "migrated from dns1 (sameersbn/bind + Webmin) 2026-09",
        "enabled": True,
        "listening_addresses": args.listen.split(","),
        "port": 53,
        "is_recursive": False,
        "is_authoritative": True,
        "forwarders": [],
        "allow_query": ["0.0.0.0/0", "::/0"],
        "allow_transfer": args.allow_transfer.split(","),
        "also_notify": args.also_notify.split(","),
    }
    return MigrationPlan(server=server, zones=zones)


def print_plan(plan: MigrationPlan) -> None:
    print(f"server: {plan.server['name']} ({plan.server['listening_addresses']})")
    for zone in plan.zones:
        soa = next(r for r in zone.records if r["record_type"] == "SOA")
        print(f"zone {zone.origin}: {len(zone.records)} records, SOA {soa['content']}")
        for record in zone.records:
            print(
                f"    {record['name']:24} {record['ttl']:>6} IN {record['record_type']:5} {record['content']}"
            )


def login(client: httpx.Client, username: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    response.raise_for_status()
    return response.json()["access_token"]


def execute(plan: MigrationPlan, args: argparse.Namespace) -> None:
    with httpx.Client(base_url=args.api_url, timeout=30) as client:
        headers = {"Authorization": f"Bearer {args.token or login(client, args.username, args.password)}"}

        response = client.post(
            f"/api/v1/dns/servers/{args.instance_id}", json=plan.server, headers=headers
        )
        response.raise_for_status()
        server_id = response.json()["id"]
        print(f"created server id={server_id}")

        for zone in plan.zones:
            zone_payload = {
                "name": zone.origin,
                "zone_type": "master",
                "enabled": True,
                "refresh": zone.refresh,
                "retry": zone.retry,
                "expire": zone.expire,
                "minimum_ttl": zone.minimum_ttl,
                "dnssec_enabled": False,
            }
            response = client.post(
                f"/api/v1/dns/servers/{server_id}/zones", json=zone_payload, headers=headers
            )
            response.raise_for_status()
            zone_id = response.json()["id"]

            for batch in chunked(zone.records, BULK_LIMIT):
                response = client.post(
                    f"/api/v1/dns/zones/{zone_id}/records/bulk",
                    json={"records": batch},
                    headers=headers,
                )
                response.raise_for_status()
            print(f"zone {zone.origin}: id={zone_id}, {len(zone.records)} records imported")


def chunked(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Import legacy BIND zones into viswall console")
    parser.add_argument("--api-url", default="http://127.0.0.1:8010")
    parser.add_argument("--instance-id", type=int, default=1)
    parser.add_argument("--zones-dir", default="/data/docker/persistent/dns1/bind/lib")
    parser.add_argument("--server-name", default="dns1.grafixpromo.com")
    parser.add_argument(
        "--listen",
        default="0.0.0.0",
        help="named listen addresses inside the container namespace (bridge mode: 0.0.0.0)",
    )
    parser.add_argument("--allow-transfer", default="93.111.66.28")
    parser.add_argument("--also-notify", default="93.111.66.28")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default=os.environ.get("VISWALL_PASSWORD", ""))
    parser.add_argument("--token", default=None)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    plan = build_plan(args)
    print_plan(plan)
    if not args.apply:
        print("\ndry-run only; pass --apply to execute")
        return 0
    execute(plan, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
