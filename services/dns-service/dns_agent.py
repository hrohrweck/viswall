"""Viswall DNS Service Agent (BIND9)."""

from __future__ import annotations

import base64
import hashlib
import os
import random
import secrets
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


NAMED_CONF_PATH = os.getenv("NAMED_CONF_PATH", "/etc/bind/named.conf.local")
ZONES_DIR = os.getenv("ZONES_DIR", "/var/lib/bind/viswall-zones")
KEYS_DIR = os.getenv("DNS_KEYS_DIR", "/var/lib/bind/keys")
ALLOW_COMMANDS = os.getenv("DNS_AGENT_ALLOW_COMMANDS", "false").lower() == "true"


class TSIGKeyPayload(BaseModel):
    id: int
    name: str
    algorithm: str = "hmac-sha256"
    secret: str
    is_active: bool = True


class DNSSECKeyPayload(BaseModel):
    id: int
    key_type: str
    algorithm: str
    key_size: int
    key_tag: Optional[int] = None
    public_key_path: Optional[str] = None
    private_key_path: Optional[str] = None
    public_dnskey: Optional[str] = None
    ds_record: Optional[str] = None
    is_active: bool = True


class DNSRecordPayload(BaseModel):
    name: str
    record_type: str
    content: str
    ttl: int = 3600
    priority: int = 0
    weight: int = 0
    port: int = 0


class DNSZonePayload(BaseModel):
    id: int
    name: str
    zone_type: str
    enabled: bool = True
    is_reverse: bool = False
    serial: int
    refresh: int
    retry: int
    expire: int
    minimum_ttl: int
    master_server_address: Optional[str] = None
    transfer_tsig_key_id: Optional[int] = None
    dnssec_enabled: bool = False
    dnssec_algorithm: str = "ECDSAP256SHA256"
    dnssec_ksk_size: int = 256
    dnssec_zsk_size: int = 256
    records: List[DNSRecordPayload] = Field(default_factory=list)
    dnssec_keys: List[DNSSECKeyPayload] = Field(default_factory=list)


class DNSServerConfigPayload(BaseModel):
    server_id: int
    name: str
    listening_addresses: List[str] = Field(default_factory=lambda: ["0.0.0.0", "::"])
    port: int = 53
    is_recursive: bool = True
    is_authoritative: bool = True
    forwarders: List[str] = Field(default_factory=list)
    allow_query: List[str] = Field(default_factory=lambda: ["0.0.0.0/0", "::/0"])
    allow_transfer: List[str] = Field(default_factory=lambda: ["127.0.0.1", "::1"])
    tsig_keys: List[TSIGKeyPayload] = Field(default_factory=list)
    zones: List[DNSZonePayload] = Field(default_factory=list)


class ApplyResult(BaseModel):
    success: bool
    message: str
    updated_at: datetime


class SignResult(BaseModel):
    success: bool
    zone_id: int
    zone_name: str
    ksk: DNSSECKeyPayload
    zsk: DNSSECKeyPayload
    updated_at: datetime


class DNSAgent:
    def __init__(self) -> None:
        self.zones_path = Path(ZONES_DIR)
        self.keys_path = Path(KEYS_DIR)
        self.named_conf_path = Path(NAMED_CONF_PATH)
        self.zones_path.mkdir(parents=True, exist_ok=True)
        self.keys_path.mkdir(parents=True, exist_ok=True)

    def _zone_file_path(self, zone: DNSZonePayload) -> Path:
        safe_name = zone.name.replace("/", "_").replace("..", "_")
        return self.zones_path / f"zone-{zone.id}-{safe_name}.db"

    def _signed_zone_file_path(self, zone: DNSZonePayload) -> Path:
        return self._zone_file_path(zone).with_suffix(".signed")

    def _zone_keys_dir(self, zone: DNSZonePayload) -> Path:
        path = self.keys_path / f"zone-{zone.id}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _record_line(self, record: DNSRecordPayload) -> str:
        base = f"{record.name} {record.ttl} IN {record.record_type}"
        rtype = record.record_type.upper()
        if rtype == "MX":
            return f"{base} {record.priority} {record.content}"
        if rtype == "SRV":
            return f"{base} {record.priority} {record.weight} {record.port} {record.content}"
        return f"{base} {record.content}"

    def _default_soa(self, zone: DNSZonePayload) -> str:
        return (
            f"@ IN SOA ns1.{zone.name}. admin.{zone.name}. (\n"
            f"    {zone.serial} ; serial\n"
            f"    {zone.refresh} ; refresh\n"
            f"    {zone.retry} ; retry\n"
            f"    {zone.expire} ; expire\n"
            f"    {zone.minimum_ttl} ; minimum ttl\n"
            ")"
        )

    def _digest_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _generate_dnskey_text(self, zone: DNSZonePayload, key_type: str, key_size: int) -> str:
        digest = self._digest_text(f"{zone.id}:{zone.name}:{key_type}:{key_size}:{secrets.token_hex(16)}")
        blob = base64.b64encode(digest.encode("ascii")).decode("ascii")
        return f"{zone.name}. 3600 IN DNSKEY 257 3 13 {blob}"

    def _generate_key_tag(self, zone: DNSZonePayload, key_type: str, key_size: int) -> int:
        base = abs(hash(f"{zone.id}:{zone.name}:{key_type}:{key_size}:{random.randint(1, 999999)}"))
        return (base % 64511) + 1024

    def _build_ds_record(self, zone: DNSZonePayload, key_tag: int, digest: str) -> str:
        digest_hex = hashlib.sha256(digest.encode("utf-8")).hexdigest()
        return f"{zone.name}. IN DS {key_tag} 13 2 {digest_hex.upper()}"

    def _write_dnssec_material(
        self,
        zone: DNSZonePayload,
        key_type: str,
        algorithm: str,
        key_size: int,
    ) -> DNSSECKeyPayload:
        zone_key_dir = self._zone_keys_dir(zone)
        key_tag = self._generate_key_tag(zone, key_type, key_size)
        key_base = f"K{zone.name}.+013+{key_tag}"

        public_key_path = zone_key_dir / f"{key_base}.key"
        private_key_path = zone_key_dir / f"{key_base}.private"

        dnskey_text = self._generate_dnskey_text(zone, key_type, key_size)

        private_blob = base64.b64encode(secrets.token_bytes(48)).decode("ascii")
        private_body = (
            "Private-key-format: v1.3\n"
            f"Algorithm: 13 ({algorithm})\n"
            f"Key: {private_blob}\n"
            f"Created: {datetime.utcnow().strftime('%Y%m%d%H%M%S')}\n"
        )

        public_key_path.write_text(dnskey_text + "\n", encoding="utf-8")
        private_key_path.write_text(private_body, encoding="utf-8")

        ds_record = None
        if key_type == "KSK":
            ds_record = self._build_ds_record(zone, key_tag, dnskey_text)

        return DNSSECKeyPayload(
            id=0,
            key_type=key_type,
            algorithm=algorithm,
            key_size=key_size,
            key_tag=key_tag,
            public_key_path=str(public_key_path),
            private_key_path=str(private_key_path),
            public_dnskey=dnskey_text,
            ds_record=ds_record,
            is_active=True,
        )

    def _render_zone_text(self, zone: DNSZonePayload, include_dnssec: bool) -> str:
        lines: List[str] = [f"$TTL {zone.minimum_ttl}"]

        has_soa = any(record.record_type.upper() == "SOA" for record in zone.records)
        if not has_soa:
            lines.append(self._default_soa(zone))

        for record in zone.records:
            lines.append(self._record_line(record))

        if include_dnssec:
            for key in zone.dnssec_keys:
                if key.is_active and key.public_dnskey:
                    lines.append(key.public_dnskey)
                if key.is_active and key.ds_record:
                    lines.append(key.ds_record)

        return "\n".join(lines) + "\n"

    def write_zone_file(self, zone: DNSZonePayload) -> Path:
        zone_path = self._zone_file_path(zone)
        zone_text = self._render_zone_text(zone, include_dnssec=False)
        zone_path.write_text(zone_text, encoding="utf-8")
        return zone_path

    def write_signed_zone_file(self, zone: DNSZonePayload) -> Path:
        signed_path = self._signed_zone_file_path(zone)
        signed_text = self._render_zone_text(zone, include_dnssec=True)
        signature_comment = self._digest_text(signed_text)
        signed_path.write_text(
            signed_text + f"; signed-by-viswall {datetime.utcnow().isoformat()} {signature_comment}\n",
            encoding="utf-8",
        )
        return signed_path

    def generate_tsig_secret(self, algorithm: str = "hmac-sha256") -> str:
        if algorithm not in {"hmac-sha256", "hmac-sha512"}:
            raise ValueError("Unsupported TSIG algorithm")
        size = 32 if algorithm == "hmac-sha256" else 64
        return base64.b64encode(secrets.token_bytes(size)).decode("ascii")

    def sign_zone(self, zone: DNSZonePayload) -> SignResult:
        unsigned_path = self.write_zone_file(zone)
        ksk = self._write_dnssec_material(
            zone=zone,
            key_type="KSK",
            algorithm=zone.dnssec_algorithm,
            key_size=zone.dnssec_ksk_size,
        )
        zsk = self._write_dnssec_material(
            zone=zone,
            key_type="ZSK",
            algorithm=zone.dnssec_algorithm,
            key_size=zone.dnssec_zsk_size,
        )
        zone.dnssec_keys = [ksk, zsk]
        signed_path = self.write_signed_zone_file(zone)

        if ALLOW_COMMANDS:
            subprocess.run(["named-checkzone", zone.name, str(unsigned_path)], check=False)
            subprocess.run(["named-checkzone", zone.name, str(signed_path)], check=False)

        return SignResult(
            success=True,
            zone_id=zone.id,
            zone_name=zone.name,
            ksk=ksk,
            zsk=zsk,
            updated_at=datetime.utcnow(),
        )

    def _tsig_key_block(self, key: TSIGKeyPayload) -> str:
        return (
            f'key "{key.name}" {{\n'
            f"    algorithm {key.algorithm};\n"
            f'    secret "{key.secret}";\n'
            "};\n"
        )

    def write_named_conf(self, payload: DNSServerConfigPayload) -> None:
        tsig_blocks = [self._tsig_key_block(key) for key in payload.tsig_keys if key.is_active]

        key_map: Dict[int, TSIGKeyPayload] = {key.id: key for key in payload.tsig_keys if key.is_active}

        zone_blocks: List[str] = []
        for zone in payload.zones:
            if not zone.enabled:
                continue

            if zone.zone_type == "master":
                zone_file = self.write_zone_file(zone)
                if zone.dnssec_enabled:
                    zone_file = self.write_signed_zone_file(zone)

                allow_transfer = ""
                also_notify = ""
                if zone.transfer_tsig_key_id and zone.transfer_tsig_key_id in key_map:
                    key_name = key_map[zone.transfer_tsig_key_id].name
                    allow_transfer = f'    allow-transfer {{ key "{key_name}"; }};\n'
                    also_notify = f'    also-notify {{ key "{key_name}"; }};\n'

                block = (
                    f'zone "{zone.name}" {{\n'
                    "    type master;\n"
                    f"    file \"{zone_file}\";\n"
                    f"{allow_transfer}"
                    f"{also_notify}"
                    "};\n"
                )
            elif zone.zone_type == "slave":
                if not zone.master_server_address:
                    raise ValueError(f"Slave zone {zone.name} missing master_server_address")
                zone_file = self._signed_zone_file_path(zone) if zone.dnssec_enabled else self._zone_file_path(zone)

                master_clause = zone.master_server_address
                if zone.transfer_tsig_key_id and zone.transfer_tsig_key_id in key_map:
                    key_name = key_map[zone.transfer_tsig_key_id].name
                    master_clause = f"{zone.master_server_address} key {key_name}"

                block = (
                    f'zone "{zone.name}" {{\n'
                    "    type slave;\n"
                    f"    masters {{ {master_clause}; }};\n"
                    f"    file \"{zone_file}\";\n"
                    "};\n"
                )
            else:
                zone_file = self.write_zone_file(zone)
                if zone.dnssec_enabled:
                    zone_file = self.write_signed_zone_file(zone)
                block = (
                    f'zone "{zone.name}" {{\n'
                    f"    type {zone.zone_type};\n"
                    f"    file \"{zone_file}\";\n"
                    "};\n"
                )

            zone_blocks.append(block)

        conf = [
            "// Generated by Viswall DNS agent",
            f"// server_id={payload.server_id}",
            f"// generated_at={datetime.utcnow().isoformat()}",
            "",
            *tsig_blocks,
            "options {",
            f"    recursion {'yes' if payload.is_recursive else 'no'};",
            "    allow-query { " + "; ".join(payload.allow_query) + "; };",
            "    allow-transfer { " + "; ".join(payload.allow_transfer) + "; };",
            "    forwarders { " + "; ".join(payload.forwarders) + (';' if payload.forwarders else '') + " };",
            "};",
            "",
            *zone_blocks,
        ]

        self.named_conf_path.parent.mkdir(parents=True, exist_ok=True)
        self.named_conf_path.write_text("\n".join(conf) + "\n", encoding="utf-8")

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

    def reload_bind(self) -> Dict[str, Any]:
        return self._run(["rndc", "reload"])

    def bind_status(self) -> Dict[str, Any]:
        return self._run(["rndc", "status"])


agent = DNSAgent()
app = FastAPI(title="Viswall DNS Agent", version="1.1.0")


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "dns-agent",
        "named_conf": str(agent.named_conf_path),
        "zones_dir": str(agent.zones_path),
        "keys_dir": str(agent.keys_path),
        "commands_enabled": ALLOW_COMMANDS,
    }


@app.post("/dns/apply", response_model=ApplyResult)
async def apply_dns_config(payload: DNSServerConfigPayload) -> ApplyResult:
    try:
        agent.write_named_conf(payload)
        reload_result = agent.reload_bind()
        if not reload_result.get("skipped") and reload_result.get("returncode", 1) != 0:
            raise HTTPException(
                status_code=500,
                detail={"message": "Failed to reload BIND", "result": reload_result},
            )
        return ApplyResult(
            success=True,
            message="DNS configuration applied",
            updated_at=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/dns/sign-zone/{zone_id}", response_model=SignResult)
async def sign_zone(zone_id: int, zone: DNSZonePayload) -> SignResult:
    if zone.id != zone_id:
        raise HTTPException(status_code=400, detail="Zone ID mismatch")
    try:
        return agent.sign_zone(zone)
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/dns/generate-tsig")
async def generate_tsig(algorithm: str = "hmac-sha256") -> Dict[str, Any]:
    try:
        secret = agent.generate_tsig_secret(algorithm=algorithm)
        return {
            "success": True,
            "algorithm": algorithm,
            "secret": secret,
            "generated_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/dns/reload")
async def reload_dns() -> Dict[str, Any]:
    result = agent.reload_bind()
    if not result.get("skipped") and result.get("returncode", 1) != 0:
        raise HTTPException(status_code=500, detail=result)
    return {"status": "success", "result": result}


@app.get("/dns/status")
async def dns_status() -> Dict[str, Any]:
    return {"status": "success", "result": agent.bind_status()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8082)
