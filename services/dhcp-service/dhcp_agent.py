"""Viswall DHCP Service Agent (Kea DHCPv4/DHCPv6)."""

from __future__ import annotations

import csv
import ipaddress
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


KEA_DHCP4_CONF_PATH = os.getenv("KEA_DHCP4_CONF_PATH", "/etc/kea/kea-dhcp4.conf")
KEA_DHCP6_CONF_PATH = os.getenv("KEA_DHCP6_CONF_PATH", "/etc/kea/kea-dhcp6.conf")
LEASES4_PATH = os.getenv("KEA_LEASES4_PATH", "/var/lib/kea/kea-leases4.csv")
LEASES6_PATH = os.getenv("KEA_LEASES6_PATH", "/var/lib/kea/kea-leases6.csv")
ALLOW_COMMANDS = os.getenv("DHCP_AGENT_ALLOW_COMMANDS", "false").lower() == "true"


class DHCPOptionPayload(BaseModel):
    id: int
    option_code: int
    option_name: str
    option_value: str
    type: str = "v4"


class DHCPReservationPayload(BaseModel):
    id: int
    hostname: Optional[str] = None
    ip_address: str
    hw_address: str
    type: str = "v4"
    enabled: bool = True


class DHCPPoolPayload(BaseModel):
    id: int
    start_address: str
    end_address: str
    type: str = "v4"
    enabled: bool = True


class DHCPSubnetPayload(BaseModel):
    id: int
    name: str
    subnet: str
    type: str = "v4"
    interface: Optional[str] = None
    relay_addresses: List[str] = Field(default_factory=list)
    domain_name: Optional[str] = None
    dns_servers: List[str] = Field(default_factory=list)
    ntp_servers: List[str] = Field(default_factory=list)
    routers: List[str] = Field(default_factory=list)
    lease_time_default: int = 3600
    lease_time_max: int = 7200
    lease_time_min: int = 300
    delegated_prefix_length: Optional[int] = None
    enabled: bool = True
    pools: List[DHCPPoolPayload] = Field(default_factory=list)
    reservations: List[DHCPReservationPayload] = Field(default_factory=list)
    options: List[DHCPOptionPayload] = Field(default_factory=list)


class DHCPServerConfigPayload(BaseModel):
    server_id: int
    name: str
    kea_ctrl_agent_address: str = "127.0.0.1"
    kea_ctrl_agent_port: int = 8000
    ha_enabled: bool = False
    ha_mode: str = "hot-standby"
    ha_peer_address: Optional[str] = None
    dhcpv4_enabled: bool = True
    dhcpv6_enabled: bool = False
    subnets: List[DHCPSubnetPayload] = Field(default_factory=list)


class ApplyResult(BaseModel):
    success: bool
    message: str
    generated_files: List[str]
    command_results: List[Dict[str, Any]] = Field(default_factory=list)
    updated_at: datetime


class LeaseEntry(BaseModel):
    ip_address: str
    hw_address: Optional[str] = None
    client_id: Optional[str] = None
    hostname: Optional[str] = None
    expires_at: Optional[str] = None
    state: str = "active"
    subnet_id: Optional[str] = None
    pool_id: Optional[str] = None
    type: str


class LeaseReleaseRequest(BaseModel):
    ip_address: str
    type: str = Field(pattern="^(v4|v6)$")


class DHCPAgent:
    def __init__(self) -> None:
        self.dhcp4_conf = Path(KEA_DHCP4_CONF_PATH)
        self.dhcp6_conf = Path(KEA_DHCP6_CONF_PATH)
        self.leases4_path = Path(LEASES4_PATH)
        self.leases6_path = Path(LEASES6_PATH)

    def _run(self, args: List[str]) -> Dict[str, Any]:
        if not ALLOW_COMMANDS:
            return {"skipped": True, "command": args}
        result = subprocess.run(args, capture_output=True, text=True, check=False)
        return {
            "skipped": False,
            "command": args,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def _json_dump(self, path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _pool_range(self, pool: DHCPPoolPayload) -> str:
        return f"{pool.start_address} - {pool.end_address}"

    def _build_option_data_v4(self, subnet: DHCPSubnetPayload) -> List[Dict[str, Any]]:
        options: List[Dict[str, Any]] = []
        if subnet.routers:
            options.append({"name": "routers", "data": ", ".join(subnet.routers)})
        if subnet.dns_servers:
            options.append(
                {"name": "domain-name-servers", "data": ", ".join(subnet.dns_servers)}
            )
        if subnet.domain_name:
            options.append({"name": "domain-name", "data": subnet.domain_name})
        if subnet.ntp_servers:
            options.append({"name": "ntp-servers", "data": ", ".join(subnet.ntp_servers)})
        for item in subnet.options:
            if item.type != "v4":
                continue
            options.append(
                {
                    "name": item.option_name,
                    "code": item.option_code,
                    "data": item.option_value,
                }
            )
        return options

    def _build_option_data_v6(self, subnet: DHCPSubnetPayload) -> List[Dict[str, Any]]:
        options: List[Dict[str, Any]] = []
        if subnet.dns_servers:
            options.append({"name": "dns-servers", "data": ", ".join(subnet.dns_servers)})
        if subnet.domain_name:
            options.append({"name": "domain-search", "data": subnet.domain_name})
        if subnet.ntp_servers:
            options.append({"name": "sntp-servers", "data": ", ".join(subnet.ntp_servers)})
        for item in subnet.options:
            if item.type != "v6":
                continue
            options.append(
                {
                    "name": item.option_name,
                    "code": item.option_code,
                    "data": item.option_value,
                }
            )
        return options

    def _build_reservations_v4(self, subnet: DHCPSubnetPayload) -> List[Dict[str, Any]]:
        reservations: List[Dict[str, Any]] = []
        for item in subnet.reservations:
            if not item.enabled or item.type != "v4":
                continue
            entry: Dict[str, Any] = {
                "hw-address": item.hw_address,
                "ip-address": item.ip_address,
            }
            if item.hostname:
                entry["hostname"] = item.hostname
            reservations.append(entry)
        return reservations

    def _build_reservations_v6(self, subnet: DHCPSubnetPayload) -> List[Dict[str, Any]]:
        reservations: List[Dict[str, Any]] = []
        for item in subnet.reservations:
            if not item.enabled or item.type != "v6":
                continue
            entry: Dict[str, Any] = {
                "duid": item.hw_address,
                "ip-addresses": [item.ip_address],
            }
            if item.hostname:
                entry["hostname"] = item.hostname
            reservations.append(entry)
        return reservations

    def _build_pd_pools(self, subnet: DHCPSubnetPayload) -> List[Dict[str, Any]]:
        if subnet.type != "v6" or subnet.delegated_prefix_length is None:
            return []
        network = ipaddress.ip_network(subnet.subnet, strict=False)
        if not isinstance(network, ipaddress.IPv6Network):
            return []
        if subnet.delegated_prefix_length < network.prefixlen:
            return []
        return [
            {
                "prefix": str(network.network_address),
                "prefix-len": network.prefixlen,
                "delegated-len": subnet.delegated_prefix_length,
            }
        ]

    def _build_subnet4(self, subnet: DHCPSubnetPayload) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": subnet.id,
            "subnet": subnet.subnet,
            "valid-lifetime": subnet.lease_time_default,
            "min-valid-lifetime": subnet.lease_time_min,
            "max-valid-lifetime": subnet.lease_time_max,
            "option-data": self._build_option_data_v4(subnet),
            "pools": [
                {"pool": self._pool_range(pool)}
                for pool in subnet.pools
                if pool.enabled and pool.type == "v4"
            ],
            "reservations": self._build_reservations_v4(subnet),
        }
        if subnet.relay_addresses:
            payload["relay"] = {"ip-addresses": subnet.relay_addresses}
        if subnet.interface:
            payload["interface"] = subnet.interface
        return payload

    def _build_subnet6(self, subnet: DHCPSubnetPayload) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": subnet.id,
            "subnet": subnet.subnet,
            "preferred-lifetime": subnet.lease_time_default,
            "valid-lifetime": subnet.lease_time_max,
            "renew-timer": subnet.lease_time_min,
            "rebind-timer": subnet.lease_time_default,
            "option-data": self._build_option_data_v6(subnet),
            "pools": [
                {"pool": self._pool_range(pool)}
                for pool in subnet.pools
                if pool.enabled and pool.type == "v6"
            ],
            "reservations": self._build_reservations_v6(subnet),
        }
        pd_pools = self._build_pd_pools(subnet)
        if pd_pools:
            payload["pd-pools"] = pd_pools
        if subnet.relay_addresses:
            payload["relay"] = {"ip-addresses": subnet.relay_addresses}
        if subnet.interface:
            payload["interface"] = subnet.interface
        return payload

    def _ha_parameters(self, payload: DHCPServerConfigPayload) -> List[Dict[str, Any]]:
        if not payload.ha_enabled or not payload.ha_peer_address:
            return []
        return [
            {
                "name": "high-availability",
                "library": "/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_ha.so",
                "parameters": {
                    "high-availability": [
                        {
                            "this-server-name": payload.name,
                            "mode": payload.ha_mode,
                            "heartbeat-delay": 10000,
                            "max-response-delay": 60000,
                            "max-ack-delay": 5000,
                            "peers": [
                                {
                                    "name": payload.name,
                                    "url": f"http://{payload.kea_ctrl_agent_address}:{payload.kea_ctrl_agent_port}/",
                                    "role": "primary",
                                },
                                {
                                    "name": f"{payload.name}-peer",
                                    "url": f"http://{payload.ha_peer_address}:{payload.kea_ctrl_agent_port}/",
                                    "role": "standby",
                                },
                            ],
                        }
                    ]
                },
            }
        ]

    def render_dhcp4_config(self, payload: DHCPServerConfigPayload) -> Dict[str, Any]:
        subnet4 = [
            self._build_subnet4(item)
            for item in payload.subnets
            if item.enabled and item.type == "v4"
        ]
        interfaces = sorted({item.interface for item in payload.subnets if item.interface and item.type == "v4"})
        if not interfaces:
            interfaces = ["*"]

        return {
            "Dhcp4": {
                "interfaces-config": {"interfaces": interfaces},
                "lease-database": {
                    "type": "memfile",
                    "name": str(self.leases4_path),
                    "persist": True,
                },
                "control-socket": {
                    "socket-type": "unix",
                    "socket-name": "/tmp/kea4-ctrl-socket",
                },
                "renew-timer": 900,
                "rebind-timer": 1800,
                "valid-lifetime": 3600,
                "subnet4": subnet4,
                "hooks-libraries": self._ha_parameters(payload),
                "loggers": [
                    {
                        "name": "kea-dhcp4",
                        "severity": "INFO",
                        "output-options": [{"output": "stdout"}],
                    }
                ],
            }
        }

    def render_dhcp6_config(self, payload: DHCPServerConfigPayload) -> Dict[str, Any]:
        subnet6 = [
            self._build_subnet6(item)
            for item in payload.subnets
            if item.enabled and item.type == "v6"
        ]
        interfaces = sorted({item.interface for item in payload.subnets if item.interface and item.type == "v6"})
        if not interfaces:
            interfaces = ["*"]

        return {
            "Dhcp6": {
                "interfaces-config": {"interfaces": interfaces},
                "lease-database": {
                    "type": "memfile",
                    "name": str(self.leases6_path),
                    "persist": True,
                },
                "control-socket": {
                    "socket-type": "unix",
                    "socket-name": "/tmp/kea6-ctrl-socket",
                },
                "preferred-lifetime": 1800,
                "valid-lifetime": 3600,
                "renew-timer": 900,
                "rebind-timer": 1800,
                "subnet6": subnet6,
                "hooks-libraries": self._ha_parameters(payload),
                "loggers": [
                    {
                        "name": "kea-dhcp6",
                        "severity": "INFO",
                        "output-options": [{"output": "stdout"}],
                    }
                ],
            }
        }

    def apply_config(self, payload: DHCPServerConfigPayload) -> ApplyResult:
        generated_files: List[str] = []
        command_results: List[Dict[str, Any]] = []

        if payload.dhcpv4_enabled:
            dhcp4_payload = self.render_dhcp4_config(payload)
            self._json_dump(self.dhcp4_conf, dhcp4_payload)
            generated_files.append(str(self.dhcp4_conf))
            command_results.append(self._run(["kea-dhcp4", "-t", "-c", str(self.dhcp4_conf)]))

        if payload.dhcpv6_enabled:
            dhcp6_payload = self.render_dhcp6_config(payload)
            self._json_dump(self.dhcp6_conf, dhcp6_payload)
            generated_files.append(str(self.dhcp6_conf))
            command_results.append(self._run(["kea-dhcp6", "-t", "-c", str(self.dhcp6_conf)]))

        if ALLOW_COMMANDS:
            if payload.dhcpv4_enabled:
                command_results.append(self._run(["service", "kea-dhcp4-server", "restart"]))
            if payload.dhcpv6_enabled:
                command_results.append(self._run(["service", "kea-dhcp6-server", "restart"]))
            command_results.append(self._run(["service", "kea-ctrl-agent", "restart"]))

        failed = [
            item
            for item in command_results
            if not item.get("skipped") and int(item.get("returncode", 0)) != 0
        ]
        if failed:
            raise HTTPException(
                status_code=500,
                detail={"message": "Failed to apply DHCP configuration", "results": failed},
            )

        return ApplyResult(
            success=True,
            message="DHCP configuration applied",
            generated_files=generated_files,
            command_results=command_results,
            updated_at=datetime.utcnow(),
        )

    def _parse_leases(self, path: Path, lease_type: str) -> List[LeaseEntry]:
        if not path.exists():
            return []

        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            return []

        rows = list(csv.reader(raw.splitlines()))
        if not rows:
            return []

        header = rows[0]
        has_header = bool(header and "address" in header)

        if has_header:
            dict_rows = list(csv.DictReader(raw.splitlines()))
        else:
            if lease_type == "v4":
                fieldnames = [
                    "address",
                    "hwaddr",
                    "client_id",
                    "valid_lifetime",
                    "expire",
                    "subnet_id",
                    "fqdn_fwd",
                    "fqdn_rev",
                    "hostname",
                    "state",
                    "user_context",
                    "pool_id",
                ]
            else:
                fieldnames = [
                    "address",
                    "duid",
                    "valid_lifetime",
                    "expire",
                    "subnet_id",
                    "pref_lifetime",
                    "lease_type",
                    "iaid",
                    "prefix_len",
                    "fqdn_fwd",
                    "fqdn_rev",
                    "hostname",
                    "state",
                    "user_context",
                    "pool_id",
                ]
            dict_rows = [dict(zip(fieldnames, row)) for row in rows]

        items: List[LeaseEntry] = []
        for row in dict_rows:
            ip_address = (row.get("address") or "").strip()
            if not ip_address:
                continue
            items.append(
                LeaseEntry(
                    ip_address=ip_address,
                    hw_address=(row.get("hwaddr") or row.get("duid") or None),
                    client_id=(row.get("client_id") or row.get("iaid") or None),
                    hostname=(row.get("hostname") or None),
                    expires_at=(row.get("expire") or None),
                    state=(row.get("state") or "active"),
                    subnet_id=(row.get("subnet_id") or None),
                    pool_id=(row.get("pool_id") or None),
                    type=lease_type,
                )
            )
        return items

    def list_leases(self) -> List[LeaseEntry]:
        items = self._parse_leases(self.leases4_path, "v4") + self._parse_leases(
            self.leases6_path, "v6"
        )
        return sorted(items, key=lambda item: item.ip_address)

    def release_lease(self, ip_address: str, lease_type: str) -> Dict[str, Any]:
        target = self.leases4_path if lease_type == "v4" else self.leases6_path
        if not target.exists():
            raise HTTPException(status_code=404, detail="Lease database file not found")

        content = target.read_text(encoding="utf-8")
        lines = content.splitlines()
        if not lines:
            raise HTTPException(status_code=404, detail="Lease not found")

        header_has_address = "address" in lines[0]
        new_lines: List[str] = []
        removed = False

        for index, line in enumerate(lines):
            if index == 0 and header_has_address:
                new_lines.append(line)
                continue
            cols = next(csv.reader([line]))
            if not cols:
                continue
            address = cols[0].strip()
            if address == ip_address:
                removed = True
                continue
            new_lines.append(line)

        if not removed:
            raise HTTPException(status_code=404, detail="Lease not found")

        target.write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")
        return {
            "success": True,
            "ip_address": ip_address,
            "type": lease_type,
            "released_at": datetime.utcnow().isoformat(),
            "lease_file": str(target),
        }


agent = DHCPAgent()
app = FastAPI(title="Viswall DHCP Agent", version="1.0.0")


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "dhcp-agent",
        "dhcp4_conf": str(agent.dhcp4_conf),
        "dhcp6_conf": str(agent.dhcp6_conf),
        "leases4": str(agent.leases4_path),
        "leases6": str(agent.leases6_path),
        "commands_enabled": ALLOW_COMMANDS,
    }


@app.post("/dhcp/apply", response_model=ApplyResult)
async def apply_dhcp_config(payload: DHCPServerConfigPayload) -> ApplyResult:
    return agent.apply_config(payload)


@app.get("/dhcp/leases", response_model=List[LeaseEntry])
async def list_dhcp_leases() -> List[LeaseEntry]:
    return agent.list_leases()


@app.post("/dhcp/leases/release")
async def release_dhcp_lease(payload: LeaseReleaseRequest) -> Dict[str, Any]:
    return agent.release_lease(ip_address=payload.ip_address, lease_type=payload.type)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8083)
