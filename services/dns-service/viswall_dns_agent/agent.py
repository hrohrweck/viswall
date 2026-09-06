"""Filesystem and BIND-tool integration for the Viswall DNS agent."""

from __future__ import annotations

import base64
import hashlib
import random
import secrets
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from viswall_dns_agent.config import AgentConfig
from viswall_dns_agent.payloads import (
    DNSSECKeyPayload,
    DNSZonePayload,
    DNSServerConfigPayload,
    SignResult,
)
from viswall_dns_agent.render import render_local_text, render_options_text, render_zone_block, render_zone_text


class DNSAgent:
    """Writes BIND configuration/zone files and drives named via rndc."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.zones_path = Path(config.zones_dir)
        self.keys_path = Path(config.keys_dir)
        self.named_conf_path = Path(config.named_conf_path)
        self.named_options_path = Path(config.named_options_path)
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

    def write_zone_file(self, zone: DNSZonePayload) -> Path:
        zone_path = self._zone_file_path(zone)
        zone_path.write_text(render_zone_text(zone, include_dnssec=False), encoding="utf-8")
        return zone_path

    def write_signed_zone_file(self, zone: DNSZonePayload) -> Path:
        signed_path = self._signed_zone_file_path(zone)
        signed_text = render_zone_text(zone, include_dnssec=True)
        signature_comment = hashlib.sha256(signed_text.encode("utf-8")).hexdigest()
        signed_path.write_text(
            signed_text
            + f"; signed-by-viswall {datetime.utcnow().isoformat()} {signature_comment}\n",
            encoding="utf-8",
        )
        return signed_path

    def write_configs(self, payload: DNSServerConfigPayload) -> None:
        """Render and write both named.conf.options and named.conf.local."""
        key_map = {key.id: key.name for key in payload.tsig_keys if key.is_active}

        zone_blocks: List[str] = []
        for zone in payload.zones:
            if not zone.enabled:
                continue

            tsig_key_name = (
                key_map.get(zone.transfer_tsig_key_id)
                if zone.transfer_tsig_key_id is not None
                else None
            )

            if zone.zone_type == "master":
                zone_file = self.write_zone_file(zone)
                if zone.dnssec_enabled:
                    zone_file = self.write_signed_zone_file(zone)
            elif zone.zone_type == "slave":
                zone_file = (
                    self._signed_zone_file_path(zone)
                    if zone.dnssec_enabled
                    else self._zone_file_path(zone)
                )
            else:
                zone_file = self.write_zone_file(zone)
                if zone.dnssec_enabled:
                    zone_file = self.write_signed_zone_file(zone)

            zone_blocks.append(
                render_zone_block(zone, str(zone_file), tsig_key_name)
            )

        self.named_options_path.parent.mkdir(parents=True, exist_ok=True)
        self.named_options_path.write_text(
            render_options_text(payload), encoding="utf-8"
        )

        self.named_conf_path.parent.mkdir(parents=True, exist_ok=True)
        self.named_conf_path.write_text(
            render_local_text(payload, zone_blocks), encoding="utf-8"
        )

    # ------------------------------------------------------------------
    # TSIG / DNSSEC material (DNSSEC material remains synthetic upstream;
    # keep zones dnssec_enabled=false until real signing lands)
    # ------------------------------------------------------------------

    def generate_tsig_secret(self, algorithm: str = "hmac-sha256") -> str:
        if algorithm not in {"hmac-sha256", "hmac-sha512"}:
            raise ValueError("Unsupported TSIG algorithm")
        size = 32 if algorithm == "hmac-sha256" else 64
        return base64.b64encode(secrets.token_bytes(size)).decode("ascii")

    def _digest_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _generate_dnskey_text(self, zone: DNSZonePayload, key_type: str, key_size: int) -> str:
        digest = self._digest_text(
            f"{zone.id}:{zone.name}:{key_type}:{key_size}:{secrets.token_hex(16)}"
        )
        blob = base64.b64encode(digest.encode("ascii")).decode("ascii")
        return f"{zone.name}. 3600 IN DNSKEY 257 3 13 {blob}"

    def _generate_key_tag(self, zone: DNSZonePayload, key_type: str, key_size: int) -> int:
        base = abs(
            hash(f"{zone.id}:{zone.name}:{key_type}:{key_size}:{random.randint(1, 999999)}")
        )
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

        ds_record = (
            self._build_ds_record(zone, key_tag, dnskey_text)
            if key_type == "KSK"
            else None
        )

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

        if self.config.allow_commands:
            subprocess.run(
                ["named-checkzone", zone.name, str(unsigned_path)], check=False
            )
            subprocess.run(
                ["named-checkzone", zone.name, str(signed_path)], check=False
            )

        return SignResult(
            success=True,
            zone_id=zone.id,
            zone_name=zone.name,
            ksk=ksk,
            zsk=zsk,
            updated_at=datetime.utcnow(),
        )

    # ------------------------------------------------------------------
    # named control (gated by DNS_AGENT_ALLOW_COMMANDS)
    # ------------------------------------------------------------------

    def _run(self, args: List[str]) -> Dict[str, Any]:
        if not self.config.allow_commands:
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
