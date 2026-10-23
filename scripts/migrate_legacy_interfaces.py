#!/usr/bin/env python3
"""Import legacy host interfaces + WireGuard client into the viswall console.

Sibling of scripts/migrate_legacy_firewall.py (todo 34); shares its
--import-manifest convention: a JSON file recording the rows created by a
previous --apply, consumed by --rollback (deletes ONLY those rows; the two
importers use separate per-importer files so rollbacks never cross):

    {
      "created": [
        {"kind": "network_interface", "name": "enp0s31f6", "id": 2},
        {"kind": "vpn_server", "name": "site-to-site-base0", "id": 1}
      ],
      "instance_id": 1,
      "applied_at": 1761200000,
      "rolled_back_at": null
    }

Sources (read-only):
  * <netplan-file> (default /etc/netplan/01-netcfg.yaml)
        -> WAN row: type wan, config_type static, ipv4 (ip/netmask), gateway,
           ipv6 (+gateway), dns (v4 first, then v6), extra routes incl. the
           on-link 0.0.0.0/0 default route.
  * `ip -j addr` / `ip -j link` on the host
        -> docker0/br-*/client/veth rows (type other, config_type dhcp); the
           `client` row gets description "wireguard site-to-site". `lo` and
           netplan-defined names are excluded. Fallback: --ip-addr-json <file>
           (the saved output of `ip -j addr`) when the ip binary is missing.
  * <wireguard-conf> (default /etc/wireguard/client.conf)
        -> VPNServer row: tunnel_type site-to-site, protocol wireguard,
           name site-to-site-base0, enabled, status stopped (the host
           wg-quick@client unit remains the lifecycle owner until the VPN
           takeover marker). private_key is imported per the documented
           plaintext-at-rest posture and carried in the row description as
           the audit note.

Safety: --dry-run is the DEFAULT and never constructs an API client. Key
material (private key, peer public key) is redacted from ALL stdout, never
written to the manifest, and a fail-closed scan aborts before printing if
any secret would leak. --apply/--rollback require VISWALL_TOKEN (admin JWT).
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_API_URL = "https://viswall.webmasters.co.at/api/v1"
DEFAULT_NETPLAN = "/etc/netplan/01-netcfg.yaml"
DEFAULT_WG_CONF = "/etc/wireguard/client.conf"
REDACTED = "REDACTED"


class MigrationError(Exception):
    """Fatal, user-facing import error (nothing is written or printed)."""


@dataclass(frozen=True)
class InterfaceRow:
    name: str
    type: str = "other"
    config_type: str = "dhcp"
    ip_address: str | None = None
    netmask: str | None = None
    gateway: str | None = None
    ipv6_address: str | None = None
    ipv6_gateway: str | None = None
    dns_servers: list[str] = field(default_factory=list)
    routes: list[dict[str, Any]] = field(default_factory=list)
    mtu: int | None = None
    description: str | None = None
    enabled: bool = True

    def payload(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "config_type": self.config_type,
            "ip_address": self.ip_address,
            "netmask": self.netmask,
            "gateway": self.gateway,
            "ipv6_address": self.ipv6_address,
            "ipv6_gateway": self.ipv6_gateway,
            "dns_servers": self.dns_servers,
            "routes": self.routes,
            "mtu": self.mtu,
            "description": self.description,
            "enabled": self.enabled,
        }

    def cidr(self) -> str | None:
        """ip/netmask rendered as CIDR (for the plan output only)."""
        if not self.ip_address:
            return None
        if not self.netmask:
            return self.ip_address
        return f"{self.ip_address}/{ipaddress.IPv4Network(f'0.0.0.0/{self.netmask}').prefixlen}"


@dataclass(frozen=True)
class VpnRow:
    endpoint: str
    peer_public_key: str
    allowed_ips: str
    persistent_keepalive: int
    local_address: str
    private_key: str
    name: str = "site-to-site-base0"
    tunnel_type: str = "site-to-site"
    protocol: str = "wireguard"
    enabled: bool = True
    description: str = ""

    def base_payload(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "protocol": self.protocol,
            "tunnel_type": self.tunnel_type,
            "listen_port": 51820,
        }

    def tunnel_payload(self) -> dict[str, Any]:
        return {
            "tunnel_type": self.tunnel_type,
            "endpoint": self.endpoint,
            "peer_public_key": self.peer_public_key,
            "allowed_ips": self.allowed_ips,
            "persistent_keepalive": self.persistent_keepalive,
            "local_address": self.local_address,
            "private_key": self.private_key,
            "description": self.description,
        }


def _netmask(prefixlen: int) -> str:
    return str(ipaddress.IPv4Network(f"0.0.0.0/{prefixlen}").netmask)


def _dns_v4_first(entries: list[Any], source: str) -> list[str]:
    v4: list[str] = []
    v6: list[str] = []
    for entry in entries:
        if not isinstance(entry, str):
            raise MigrationError(f"{source}: non-string nameserver entry {entry!r}")
        host = entry.split("/", 1)[0]
        try:
            version = ipaddress.ip_address(host).version
        except ValueError as exc:
            raise MigrationError(f"{source}: invalid nameserver {entry!r}") from exc
        (v4 if version == 4 else v6).append(entry)
    return v4 + v6


def parse_netplan(path: Path) -> list[InterfaceRow]:
    if not path.is_file():
        raise MigrationError(f"netplan file not found: {path}")
    try:
        doc = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise MigrationError(f"malformed netplan yaml {path}: {exc}") from exc
    network = (doc or {}).get("network")
    if not isinstance(network, dict):
        raise MigrationError(f"{path}: missing 'network:' mapping")
    ethernets = network.get("ethernets")
    if not isinstance(ethernets, dict) or not ethernets:
        raise MigrationError(f"{path}: no 'ethernets:' interfaces defined")

    rows: list[InterfaceRow] = []
    for name, spec in ethernets.items():
        if not isinstance(spec, dict):
            raise MigrationError(f"{path}: malformed ethernet entry {name!r}")
        ip_address: str | None = None
        netmask: str | None = None
        ipv6_address: str | None = None
        for cidr in spec.get("addresses") or []:
            if not isinstance(cidr, str):
                raise MigrationError(f"{path}: non-string address under {name}: {cidr!r}")
            try:
                iface = ipaddress.ip_interface(cidr)
            except ValueError as exc:
                raise MigrationError(f"{path}: invalid address {cidr!r} under {name}") from exc
            if iface.version == 4 and ip_address is None:
                ip_address = str(iface.ip)
                netmask = _netmask(iface.network.prefixlen)
            elif iface.version == 6 and ipv6_address is None:
                ipv6_address = cidr

        gateway: str | None = None
        ipv6_gateway: str | None = None
        routes: list[dict[str, Any]] = []
        has_default: bool = False
        for route in spec.get("routes") or []:
            if not isinstance(route, dict) or not isinstance(route.get("to"), str):
                raise MigrationError(f"{path}: malformed route entry under {name}: {route!r}")
            to, via = route["to"], route.get("via")
            on_link = bool(route.get("on-link", False))
            if to == "0.0.0.0/0":
                has_default = True
                gateway = via if isinstance(via, str) else gateway
                routes.append({"to": to, "via": via, "on_link": on_link})
            elif to == "::/0":
                ipv6_gateway = via if isinstance(via, str) else ipv6_gateway
            else:
                routes.append({"to": to, "via": via, "on_link": on_link})

        ns = spec.get("nameservers")
        dns = _dns_v4_first(ns.get("addresses") or [], str(path)) if isinstance(ns, dict) else []
        rows.append(
            InterfaceRow(
                name=name,
                type="wan" if has_default else "other",
                config_type="static",
                ip_address=ip_address,
                netmask=netmask,
                gateway=gateway,
                ipv6_address=ipv6_address,
                ipv6_gateway=ipv6_gateway,
                dns_servers=dns,
                routes=routes,
            )
        )
    return rows


def _run_ip_json() -> list[Any]:
    try:
        result = subprocess.run(["ip", "-j", "addr"], capture_output=True, text=True, check=True)
    except FileNotFoundError as exc:
        raise MigrationError(
            "iproute2 'ip' binary not found; provide --ip-addr-json <file> "
            "(the saved output of `ip -j addr`)"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise MigrationError(f"'ip -j addr' failed: {exc.stderr.strip()}") from exc
    return json.loads(result.stdout)


def discover_live(
    addr_json: Path | None, netplan_names: set[str]
) -> tuple[list[InterfaceRow], dict[str, int]]:
    """Live rows (docker0/br-*/client/veth) plus an mtu map for every name."""
    if addr_json is not None:
        if not addr_json.is_file():
            raise MigrationError(f"--ip-addr-json file not found: {addr_json}")
        raw = json.loads(addr_json.read_text())
        source = str(addr_json)
    else:
        raw = _run_ip_json()
        source = "ip -j addr"
    if not isinstance(raw, list):
        raise MigrationError(f"{source}: expected a JSON list of interfaces")

    mtu_by_name: dict[str, int] = {}
    rows: list[InterfaceRow] = []
    for entry in raw:
        if not isinstance(entry, dict):
            raise MigrationError(f"{source}: interface entry is not an object")
        name = entry.get("ifname")
        if not isinstance(name, str):
            continue
        mtu = entry.get("mtu")
        if isinstance(mtu, int):
            mtu_by_name[name] = mtu
        if name == "lo" or name in netplan_names:
            continue
        ip_address: str | None = None
        netmask: str | None = None
        ipv6_address: str | None = None
        for addr in entry.get("addr_info") or []:
            if not isinstance(addr, dict):
                continue
            local, prefix = addr.get("local"), addr.get("prefixlen")
            if addr.get("family") == "inet" and isinstance(local, str) and isinstance(prefix, int) and ip_address is None:
                ip_address, netmask = local, _netmask(prefix)
            elif (
                addr.get("family") == "inet6"
                and isinstance(local, str)
                and isinstance(prefix, int)
                and ipv6_address is None
                and not ipaddress.IPv6Address(local).is_link_local
            ):
                ipv6_address = f"{local}/{prefix}"
        rows.append(
            InterfaceRow(
                name=name,
                ip_address=ip_address,
                netmask=netmask,
                ipv6_address=ipv6_address,
                mtu=mtu if isinstance(mtu, int) else None,
                description="wireguard site-to-site" if name == "client" else None,
            )
        )
    rows.sort(key=lambda row: row.name)
    return rows, mtu_by_name


def parse_wireguard(path: Path) -> VpnRow:
    if not path.is_file():
        raise MigrationError(f"wireguard config not found: {path}")
    sections: dict[str, dict[str, str]] = {}
    current: str | None = None
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped[1:-1].strip()
            if current in sections:
                raise MigrationError(f"{path}:{lineno}: duplicate [{current}] section")
            sections[current] = {}
            continue
        if current is None:
            raise MigrationError(f"{path}:{lineno}: key outside any [Section]")
        if "=" not in stripped:
            raise MigrationError(f"{path}:{lineno}: malformed line (expected 'Key = Value')")
        key, _, value = stripped.partition("=")
        sections[current][key.strip()] = value.split("#", 1)[0].strip()

    iface = sections.get("Interface")
    peer = sections.get("Peer")
    if iface is None:
        raise MigrationError(f"{path}: missing [Interface] section")
    if peer is None:
        raise MigrationError(f"{path}: missing [Peer] section")
    private_key = iface.get("PrivateKey")
    local_address = iface.get("Address")
    peer_public_key = peer.get("PublicKey")
    endpoint = peer.get("Endpoint")
    allowed_ips = peer.get("AllowedIPs")
    for missing, where in (
        (private_key, "PrivateKey in [Interface] (key material is mandatory)"),
        (local_address, "Address in [Interface]"),
        (peer_public_key, "PublicKey in [Peer] — refusing partial import"),
        (endpoint, "Endpoint in [Peer]"),
        (allowed_ips, "AllowedIPs in [Peer]"),
    ):
        if not missing:
            raise MigrationError(f"{path}: missing {where}")
    keepalive_raw = peer.get("PersistentKeepalive")
    try:
        persistent_keepalive = int(keepalive_raw) if keepalive_raw else 25
    except ValueError as exc:
        raise MigrationError(f"{path}: invalid PersistentKeepalive {keepalive_raw!r}") from exc

    return VpnRow(
        endpoint=endpoint,
        peer_public_key=peer_public_key,
        allowed_ips=",".join(part.strip() for part in allowed_ips.split(",")),
        persistent_keepalive=persistent_keepalive,
        local_address=local_address,
        private_key=private_key,
        description=(
            "site-to-site WireGuard tunnel imported from /etc/wireguard/client.conf; "
            "private key stored plaintext-at-rest (documented posture, audit note)"
        ),
    )


def _assert_no_secrets(text: str, secrets: list[str]) -> None:
    for secret in secrets:
        if secret and secret in text:
            raise MigrationError("refusing to print output containing key material")


def format_interface(row: InterfaceRow) -> str:
    parts = [f"type={row.type}", f"config_type={row.config_type}"]
    if row.cidr():
        parts.append(f"ip={row.cidr()}")
    if row.gateway:
        parts.append(f"gateway={row.gateway}")
    if row.ipv6_address:
        parts.append(f"ipv6={row.ipv6_address}")
    if row.ipv6_gateway:
        parts.append(f"ipv6_gateway={row.ipv6_gateway}")
    if row.dns_servers:
        parts.append(f"dns_servers={row.dns_servers}")
    if row.routes:
        parts.append(f"routes={row.routes}")
    if row.mtu is not None:
        parts.append(f"mtu={row.mtu}")
    if row.description:
        parts.append(f"description={row.description!r}")
    parts.append(f"enabled={row.enabled}")
    return f"  - {row.name}: " + " ".join(parts)


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise MigrationError(f"cannot read manifest {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise MigrationError(f"manifest {path} is not a JSON object")
    return data


def _save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def _api_client(api_url: str) -> Any:
    try:
        import httpx
    except ImportError as exc:
        raise MigrationError(
            "httpx is required for --apply/--rollback (run with `uv run --with httpx`); "
            "--dry-run has no dependencies"
        ) from exc
    token = os.environ.get("VISWALL_TOKEN")
    if not token:
        raise MigrationError("VISWALL_TOKEN env var is required for --apply/--rollback")
    return httpx.Client(
        base_url=api_url, headers={"Authorization": f"Bearer {token}"}, timeout=30.0
    )


def _existing_names(client: Any, path: str) -> set[str]:
    response = client.get(path)
    response.raise_for_status()
    return {
        item["name"]
        for item in response.json()
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }


def apply_rows(args: argparse.Namespace, interfaces: list[InterfaceRow], vpn: VpnRow) -> None:
    client = _api_client(args.api_url)
    manifest = _load_manifest(Path(args.import_manifest))
    created = manifest.setdefault("created", [])
    run = 0

    existing = _existing_names(client, f"/network/interfaces/{args.instance_id}")
    for row in interfaces:
        if row.name in existing:
            print(f"  [skip] interface {row.name}: already exists (console row preserved)")
            continue
        response = client.post(f"/network/interfaces/{args.instance_id}", json=row.payload())
        response.raise_for_status()
        interface_id = response.json()["id"]
        created.append({"kind": "network_interface", "name": row.name, "id": interface_id})
        existing.add(row.name)
        run += 1
        print(f"  [created] interface {row.name} id={interface_id}")

    existing = _existing_names(client, f"/vpn/servers/{args.instance_id}")
    if vpn.name in existing:
        print(f"  [skip] vpn server {vpn.name}: already exists (console row preserved)")
    else:
        response = client.post(f"/vpn/servers/{args.instance_id}", json=vpn.base_payload())
        response.raise_for_status()
        server_id = response.json()["id"]
        response = client.patch(f"/vpn/servers/{server_id}", json=vpn.tunnel_payload())
        response.raise_for_status()
        created.append({"kind": "vpn_server", "name": vpn.name, "id": server_id})
        run += 1
        print(f"  [created] vpn server {vpn.name} id={server_id}")

    manifest.update(instance_id=args.instance_id, applied_at=int(time.time()), created=created)
    _save_manifest(Path(args.import_manifest), manifest)
    print(f"\n[apply] created this run: {run} | total in manifest: {len(created)} | "
          f"manifest={args.import_manifest}")


def rollback_rows(args: argparse.Namespace) -> None:
    manifest_path = Path(args.import_manifest)
    if not manifest_path.is_file():
        raise MigrationError(
            f"import manifest {args.import_manifest} not found; cannot determine which rows to roll back"
        )
    client = _api_client(args.api_url)
    manifest = _load_manifest(manifest_path)
    deleted = 0
    missing = 0
    for entry in manifest.get("created", []):
        kind, entry_id = entry.get("kind"), entry.get("id")
        if kind == "network_interface":
            url = f"/network/interfaces/detail/{entry_id}"
        elif kind == "vpn_server":
            url = f"/vpn/servers/{entry_id}"
        else:
            raise MigrationError(f"manifest entry has unknown kind {kind!r}: {entry!r}")
        response = client.delete(url)
        if response.status_code == 404:
            missing += 1
            print(f"  [skip] {kind} {entry.get('name')} id={entry_id}: already gone")
            continue
        response.raise_for_status()
        deleted += 1
        print(f"  [deleted] {kind} {entry.get('name')} id={entry_id}")
    manifest["rolled_back_at"] = int(time.time())
    _save_manifest(manifest_path, manifest)
    print(f"\n[rollback] deleted {deleted} rows, already gone {missing}; manifest kept")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", default=True, help="print the plan, no API calls (default)")
    mode.add_argument("--apply", action="store_true", help="create rows via the API")
    mode.add_argument("--rollback", action="store_true", help="delete rows recorded in the import manifest")
    parser.add_argument("--instance-id", type=int, default=int(os.environ.get("INSTANCE_ID", "1")))
    parser.add_argument("--api-url", default=os.environ.get("VISWALL_API_URL", DEFAULT_API_URL))
    parser.add_argument("--netplan-file", default=DEFAULT_NETPLAN)
    parser.add_argument("--wireguard-conf", default=DEFAULT_WG_CONF)
    parser.add_argument("--ip-addr-json", default=None, help="fallback: saved `ip -j addr` output")
    parser.add_argument(
        "--import-manifest",
        default=str(Path(__file__).resolve().parent / "interfaces_import_manifest.json"),
    )
    args = parser.parse_args()

    if args.rollback:  # manifest-only; no host parsing needed
        print(f"mode: ROLLBACK (manifest {args.import_manifest})")
        rollback_rows(args)
        return 0

    netplan_rows = parse_netplan(Path(args.netplan_file))
    live_rows, mtu_by_name = discover_live(
        Path(args.ip_addr_json) if args.ip_addr_json else None, {row.name for row in netplan_rows}
    )
    netplan_rows = [
        row
        if row.mtu is not None or row.name not in mtu_by_name
        else InterfaceRow(**{**row.__dict__, "mtu": mtu_by_name[row.name]})
        for row in netplan_rows
    ]
    vpn = parse_wireguard(Path(args.wireguard_conf))
    secrets = [vpn.private_key, vpn.peer_public_key]

    print("==================== MIGRATION PLAN ====================")
    print(f"instance: {args.instance_id}   api: {args.api_url}   manifest: {args.import_manifest}")
    print(f"[netplan] {args.netplan_file}")
    for row in netplan_rows:
        line = format_interface(row)
        _assert_no_secrets(line, secrets)
        print(line)
    print(f"[live discovery] {args.ip_addr_json or 'ip -j addr'} ({len(live_rows)} rows)")
    for row in live_rows:
        line = format_interface(row)
        _assert_no_secrets(line, secrets)
        print(line)
    print(f"[wireguard] {args.wireguard_conf}")
    line = (
        f"  - {vpn.name}: tunnel_type={vpn.tunnel_type} protocol={vpn.protocol} "
        f"endpoint={vpn.endpoint} peer_public_key={REDACTED} allowed_ips={vpn.allowed_ips} "
        f"persistent_keepalive={vpn.persistent_keepalive} local_address={vpn.local_address} "
        f"private_key={REDACTED} enabled={vpn.enabled} status=stopped"
    )
    _assert_no_secrets(line, secrets)
    print(line)
    print(f"\ninterfaces to create: {len(netplan_rows) + len(live_rows)}   vpn servers to create: 1")

    if args.apply:
        print("\nmode: APPLY")
        apply_rows(args, netplan_rows + live_rows, vpn)
        return 0
    print("\nmode: DRY-RUN — no API calls were made. Pass --apply to create rows or --rollback to remove them.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MigrationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - API transport failures only
        if exc.__class__.__module__.partition(".")[0] == "httpx":
            print(f"ERROR: API request failed: {exc}", file=sys.stderr)
            sys.exit(1)
        raise
