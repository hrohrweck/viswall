"""Pydantic payload models shared with the viswall api-gateway DNS dispatch."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


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
    key_tag: int | None = None
    public_key_path: str | None = None
    private_key_path: str | None = None
    public_dnskey: str | None = None
    ds_record: str | None = None
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
    master_server_address: str | None = None
    transfer_tsig_key_id: int | None = None
    dnssec_enabled: bool = False
    dnssec_algorithm: str = "ECDSAP256SHA256"
    dnssec_ksk_size: int = 256
    dnssec_zsk_size: int = 256
    records: list[DNSRecordPayload] = Field(default_factory=list)
    dnssec_keys: list[DNSSECKeyPayload] = Field(default_factory=list)


class DNSServerConfigPayload(BaseModel):
    server_id: int
    name: str
    listening_addresses: list[str] = Field(
        default_factory=lambda: ["0.0.0.0", "::"]
    )
    port: int = 53
    is_recursive: bool = True
    is_authoritative: bool = True
    forwarders: list[str] = Field(default_factory=list)
    allow_query: list[str] = Field(
        default_factory=lambda: ["0.0.0.0/0", "::/0"]
    )
    allow_transfer: list[str] = Field(default_factory=lambda: ["127.0.0.1", "::1"])
    also_notify: list[str] = Field(default_factory=list)
    tsig_keys: list[TSIGKeyPayload] = Field(default_factory=list)
    zones: list[DNSZonePayload] = Field(default_factory=list)


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
