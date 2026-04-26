"""DHCP commands."""

from typing import Optional

import typer

from viswall_cli.utils import get_client
from viswall_cli.output import print_result, print_success, print_error
from viswall.exceptions import ViswallAPIError

app = typer.Typer(help="Manage DHCP servers, subnets, and leases")


@app.command("servers")
def list_servers(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List DHCP servers for an instance."""
    client = get_client(url=url, token=token)
    try:
        servers = client.dhcp.list_servers(instance_id)
        print_result(
            servers,
            format=format,
            columns=[
                "id",
                "name",
                "status",
                "dhcpv4_enabled",
                "dhcpv6_enabled",
                "subnets_count",
            ],
        )
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("server-create")
def create_server(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    name: str = typer.Option(..., "--name", "-n", help="Server name"),
    dhcpv4: bool = typer.Option(True, "--dhcpv4/--no-dhcpv4", help="Enable DHCPv4"),
    dhcpv6: bool = typer.Option(False, "--dhcpv6/--no-dhcpv6", help="Enable DHCPv6"),
    ha_enabled: bool = typer.Option(False, "--ha-enabled", help="Enable HA"),
    ha_peer_address: Optional[str] = typer.Option(None, "--ha-peer-address", help="HA peer address"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Create a DHCP server."""
    client = get_client(url=url, token=token)
    try:
        server = client.dhcp.create_server(
            instance_id,
            name=name,
            dhcpv4_enabled=dhcpv4,
            dhcpv6_enabled=dhcpv6,
            ha_enabled=ha_enabled,
            ha_peer_address=ha_peer_address,
        )
        print_result(server, format=format)
        print_success(f"DHCP server '{name}' created")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("subnets")
def list_subnets(
    server_id: int = typer.Option(..., "--server-id", "-s", help="DHCP server ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List DHCP subnets for a server."""
    client = get_client(url=url, token=token)
    try:
        subnets = client.dhcp.list_subnets(server_id)
        print_result(
            subnets,
            format=format,
            columns=[
                "id",
                "name",
                "subnet",
                "type",
                "pools_count",
                "reservations_count",
                "leases_count",
            ],
        )
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("subnet-create")
def create_subnet(
    server_id: int = typer.Option(..., "--server-id", "-s", help="DHCP server ID"),
    name: str = typer.Option(..., "--name", "-n", help="Subnet name"),
    subnet: str = typer.Option(..., "--subnet", help="CIDR subnet"),
    type: str = typer.Option("v4", "--type", help="Subnet type: v4 or v6"),
    lease_min: int = typer.Option(300, "--lease-min", help="Minimum lease time"),
    lease_default: int = typer.Option(3600, "--lease-default", help="Default lease time"),
    lease_max: int = typer.Option(7200, "--lease-max", help="Maximum lease time"),
    routers: Optional[str] = typer.Option(None, "--routers", help="Comma-separated router IPs"),
    dns_servers: Optional[str] = typer.Option(None, "--dns-servers", help="Comma-separated DNS server IPs"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Create a DHCP subnet."""
    client = get_client(url=url, token=token)
    try:
        subnet_data = client.dhcp.create_subnet(
            server_id,
            name=name,
            subnet=subnet,
            type=type,
            lease_time_min=lease_min,
            lease_time_default=lease_default,
            lease_time_max=lease_max,
            routers=[v.strip() for v in routers.split(",") if v.strip()] if routers else [],
            dns_servers=[v.strip() for v in dns_servers.split(",") if v.strip()] if dns_servers else [],
        )
        print_result(subnet_data, format=format)
        print_success(f"DHCP subnet '{name}' created")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("leases")
def list_leases(
    subnet_id: int = typer.Option(..., "--subnet-id", help="Subnet ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List leases for a subnet."""
    client = get_client(url=url, token=token)
    try:
        leases = client.dhcp.list_subnet_leases(subnet_id)
        print_result(
            leases,
            format=format,
            columns=["id", "ip_address", "state", "hostname", "hw_address", "lease_end"],
        )
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("leases-active")
def list_active_leases(
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List active leases across all subnets."""
    client = get_client(url=url, token=token)
    try:
        leases = client.dhcp.list_active_leases()
        print_result(
            leases,
            format=format,
            columns=["id", "subnet_id", "ip_address", "state", "hostname", "lease_end"],
        )
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("lease-release")
def release_lease(
    lease_id: int = typer.Argument(..., help="Lease ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Release a lease by ID."""
    if not yes:
        confirm = typer.confirm(f"Release lease {lease_id}?")
        if not confirm:
            raise typer.Abort()

    client = get_client(url=url, token=token)
    try:
        result = client.dhcp.release_lease(lease_id)
        print_result(result, format=format)
        print_success(f"Lease {lease_id} released")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)
