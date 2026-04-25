"""Tests for IPv6 dual-stack support in schemas and agents."""

import pytest
from pydantic import ValidationError
from shared.schemas import VPNRouteBase, VPNServerBase


def test_vpn_route_accepts_ipv4_cidr():
    route = VPNRouteBase(destination="192.168.1.0/24", gateway="192.168.1.1")
    assert str(route.destination) == "192.168.1.0/24"


def test_vpn_route_accepts_ipv6_cidr():
    route = VPNRouteBase(destination="2001:db8::/64", gateway="2001:db8::1")
    assert str(route.destination) == "2001:db8::/64"


def test_vpn_route_accepts_ipv6_full_cidr():
    route = VPNRouteBase(destination="2001:0db8:0000:0000:0000:0000:0000:0000/64")
    assert str(route.destination) == "2001:db8::/64"


def test_vpn_route_rejects_invalid_cidr():
    with pytest.raises(ValidationError):
        VPNRouteBase(destination="not-a-network")


def test_vpn_route_accepts_ipv4_host_as_prefix():
    """IPvAnyNetwork treats a bare IPv4 address as /32."""
    route = VPNRouteBase(destination="192.168.1.1")
    assert str(route.destination) == "192.168.1.1/32"


def test_vpn_route_accepts_ipv6_host_as_prefix():
    """IPvAnyNetwork treats a bare IPv6 address as /128."""
    route = VPNRouteBase(destination="2001:db8::1")
    assert str(route.destination) == "2001:db8::1/128"


def test_vpn_server_accepts_ipv6_tunnel_network():
    server = VPNServerBase(
        name="test",
        protocol="wireguard",
        network_cidr="10.200.0.0/24",
        ipv6_tunnel_network="fd00:200::/64",
    )
    assert server.ipv6_tunnel_network == "fd00:200::/64"


def test_vpn_server_without_ipv6_tunnel_network():
    server = VPNServerBase(
        name="test",
        protocol="wireguard",
        network_cidr="10.200.0.0/24",
    )
    assert server.ipv6_tunnel_network is None
