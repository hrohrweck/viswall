"""Request/response models for the node agent's interface API.

InterfaceConfig mirrors the gateway's NetworkInterface model (netmask
string form, e.g. "255.255.255.0") so the gateway can relay its
desired-state rows verbatim.
"""

from __future__ import annotations

import ipaddress
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

IFACE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]{1,15}$")
MANAGED_MTU_MIN = 68
MANAGED_MTU_MAX = 65535


class LiveAddress(BaseModel):
    address: str  # "10.0.0.5"
    prefixlen: int
    family: str = "inet"  # iproute2 address family ("inet" | "inet6")


class LiveInterface(BaseModel):
    name: str
    operstate: str = "unknown"  # iproute2 operstate (UP, DOWN, UNKNOWN, ...)
    up: bool = False
    mtu: int | None = None
    mac: str | None = None
    addresses: list[LiveAddress] = Field(default_factory=list)
    # Filled by discovery from the routing table
    has_default_route: bool = False


class RouteConfig(BaseModel):
    """One extra static route: {to, via, on_link}.

    ``to`` is either ``"default"`` or a CIDR (v4 or v6). ``via`` is omitted
    for pure on-link routes. Matches the netplan route entry shape.
    """

    to: str
    via: str | None = None
    on_link: bool = False

    @field_validator("to")
    @classmethod
    def validate_to(cls, value: str) -> str:
        if value == "default":
            return value
        try:
            ipaddress.ip_network(value, strict=False)
        except ValueError as exc:
            raise ValueError(f"invalid route destination: {value!r}") from exc
        return value

    @field_validator("via")
    @classmethod
    def validate_via(cls, value: str | None) -> str | None:
        if value is not None:
            ipaddress.ip_address(value)  # raises ValueError on bad input
        return value


class InterfaceConfig(BaseModel):
    """Desired state for one host interface (mirrors NetworkInterface)."""

    name: str
    config_type: str = "static"  # static | dhcp
    ip_address: str | None = None
    netmask: str | None = None  # "255.255.255.0" style
    gateway: str | None = None
    ipv6_address: str | None = None  # "<addr>/<prefixlen>", netplan form
    ipv6_gateway: str | None = None
    dns_servers: list[str] = Field(default_factory=list)
    routes: list[RouteConfig] = Field(default_factory=list)
    mtu: int | None = Field(default=None, ge=MANAGED_MTU_MIN, le=MANAGED_MTU_MAX)
    enabled: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if value == "lo":
            raise ValueError("refusing to manage the loopback interface")
        if not IFACE_NAME_PATTERN.match(value):
            raise ValueError(f"invalid interface name: {value!r}")
        return value

    @field_validator("config_type")
    @classmethod
    def validate_config_type(cls, value: str) -> str:
        if value not in ("static", "dhcp"):
            raise ValueError("config_type must be 'static' or 'dhcp'")
        return value

    @field_validator("ip_address", "gateway")
    @classmethod
    def validate_ip(cls, value: str | None) -> str | None:
        if value is not None:
            ipaddress.ip_address(value)  # raises ValueError on bad input
        return value

    @field_validator("netmask")
    @classmethod
    def validate_netmask(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            ipaddress.IPv4Network(f"0.0.0.0/{value}")
        except ValueError as exc:
            raise ValueError(f"invalid netmask: {value!r}") from exc
        return value

    @field_validator("ipv6_address")
    @classmethod
    def validate_ipv6_address(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if "/" not in value:
            raise ValueError(
                f"ipv6_address must include a prefix, e.g. '2001:db8::2/64': {value!r}"
            )
        try:
            ipaddress.IPv6Interface(value)
        except ValueError as exc:
            raise ValueError(f"invalid ipv6 address: {value!r}") from exc
        return value

    @field_validator("ipv6_gateway")
    @classmethod
    def validate_ipv6_gateway(cls, value: str | None) -> str | None:
        if value is not None:
            try:
                ipaddress.IPv6Address(value)
            except ValueError as exc:
                raise ValueError(f"invalid ipv6 gateway: {value!r}") from exc
        return value

    @field_validator("dns_servers")
    @classmethod
    def validate_dns_servers(cls, value: list[str]) -> list[str]:
        for entry in value:
            try:
                ipaddress.ip_address(entry)
            except ValueError as exc:
                raise ValueError(f"invalid DNS server address: {entry!r}") from exc
        return value

    @property
    def prefixlen(self) -> int | None:
        if not self.netmask:
            return None
        return ipaddress.IPv4Network(f"0.0.0.0/{self.netmask}").prefixlen


class ApplyRequest(BaseModel):
    interfaces: list[InterfaceConfig]
    # Acknowledge that changes touching the interface carrying the default
    # route (or the default route itself) may cut management connectivity.
    force: bool = False
    # Try-mode: render to netplan, run `netplan try` and confirm via health
    # probes instead of applying live netlink changes. Failed probes close
    # netplan's stdin so the change auto-reverts.
    try_mode: bool = False

    @model_validator(mode="after")
    def unique_interface_names(self) -> ApplyRequest:
        names = [cfg.name for cfg in self.interfaces]
        if len(names) != len(set(names)):
            raise ValueError("duplicate interface names in request")
        return self


class ApplyChange(BaseModel):
    interface: str
    action: str  # address | stale-address | gateway | mtu | link | netplan
    detail: str
    ok: bool = True


class ProbeResult(BaseModel):
    """Outcome of one pre-confirm health probe in try-mode applies."""

    name: str
    ok: bool
    detail: str = ""


class ApplyResult(BaseModel):
    success: bool
    changes: list[ApplyChange] = Field(default_factory=list)
    default_route_interface: str | None = None
    netplan_file: str | None = None
    netplan_written: bool = False
    message: str = ""
    try_mode: bool = False
    probes: list[ProbeResult] = Field(default_factory=list)
    netplan_outcome: Literal["accepted", "reverted", "error"] | None = None
    snapshot_dir: str | None = None
