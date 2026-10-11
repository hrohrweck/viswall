"""Request/response models for the node agent's interface API.

InterfaceConfig mirrors the gateway's NetworkInterface model (netmask
string form, e.g. "255.255.255.0") so the gateway can relay its
desired-state rows verbatim.
"""

from __future__ import annotations

import ipaddress
import re

from pydantic import BaseModel, Field, field_validator, model_validator

IFACE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]{1,15}$")
MANAGED_MTU_MIN = 68
MANAGED_MTU_MAX = 65535


class LiveAddress(BaseModel):
    address: str  # "10.0.0.5"
    prefixlen: int


class LiveInterface(BaseModel):
    name: str
    operstate: str = "unknown"  # iproute2 operstate (UP, DOWN, UNKNOWN, ...)
    up: bool = False
    mtu: int | None = None
    mac: str | None = None
    addresses: list[LiveAddress] = Field(default_factory=list)
    # Filled by discovery from the routing table
    has_default_route: bool = False


class InterfaceConfig(BaseModel):
    """Desired state for one host interface (mirrors NetworkInterface)."""

    name: str
    config_type: str = "static"  # static | dhcp
    ip_address: str | None = None
    netmask: str | None = None  # "255.255.255.0" style
    gateway: str | None = None
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

    @model_validator(mode="after")
    def unique_interface_names(self) -> "ApplyRequest":
        names = [cfg.name for cfg in self.interfaces]
        if len(names) != len(set(names)):
            raise ValueError("duplicate interface names in request")
        return self


class ApplyChange(BaseModel):
    interface: str
    action: str  # address | stale-address | gateway | mtu | link | netplan
    detail: str
    ok: bool = True


class ApplyResult(BaseModel):
    success: bool
    changes: list[ApplyChange] = Field(default_factory=list)
    default_route_interface: str | None = None
    netplan_file: str | None = None
    netplan_written: bool = False
    message: str = ""
