"""DNS commands."""

from typing import Any, Dict, Optional

import typer

from viswall_cli.utils import get_client
from viswall_cli.output import print_result, print_success, print_error
from viswall.exceptions import ViswallAPIError

app = typer.Typer(help="Manage DNS servers, zones, and records")


@app.command("servers")
def list_servers(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List DNS servers for an instance."""
    client = get_client(url=url, token=token)
    try:
        servers = client.dns.list_servers(instance_id)
        print_result(servers, format=format, columns=["id", "name", "port", "status", "zones_count"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("server-create")
def create_server(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    name: str = typer.Option(..., "--name", "-n"),
    port: int = typer.Option(53, "--port"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive"),
    authoritative: bool = typer.Option(True, "--authoritative/--no-authoritative"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Create a DNS server."""
    client = get_client(url=url, token=token)
    try:
        server = client.dns.create_server(
            instance_id,
            name=name,
            port=port,
            is_recursive=recursive,
            is_authoritative=authoritative,
        )
        print_result(server, format=format)
        print_success(f"DNS server '{name}' created")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("server-delete")
def delete_server(
    server_id: int = typer.Argument(..., help="Server ID"),
    yes: bool = typer.Option(False, "--yes", "-y"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Delete a DNS server."""
    if not yes:
        confirm = typer.confirm(f"Delete DNS server {server_id}?")
        if not confirm:
            raise typer.Abort()

    client = get_client(url=url, token=token)
    try:
        client.dns.delete_server(server_id)
        print_success(f"DNS server {server_id} deleted")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("zones")
def list_zones(
    server_id: int = typer.Option(..., "--server-id", "-s", help="Server ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List DNS zones for a server."""
    client = get_client(url=url, token=token)
    try:
        zones = client.dns.list_zones(server_id)
        print_result(zones, format=format, columns=["id", "name", "zone_type", "enabled", "records_count"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("zone-create")
def create_zone(
    server_id: int = typer.Option(..., "--server-id", "-s", help="Server ID"),
    name: str = typer.Option(..., "--name", "-n", help="Zone name"),
    zone_type: str = typer.Option("master", "--type", "-t", help="master, slave, forward, stub"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Create a DNS zone."""
    client = get_client(url=url, token=token)
    try:
        zone = client.dns.create_zone(server_id, name=name, zone_type=zone_type)
        print_result(zone, format=format)
        print_success(f"DNS zone '{name}' created")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("zone-delete")
def delete_zone(
    zone_id: int = typer.Argument(..., help="Zone ID"),
    yes: bool = typer.Option(False, "--yes", "-y"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Delete a DNS zone."""
    if not yes:
        confirm = typer.confirm(f"Delete DNS zone {zone_id}?")
        if not confirm:
            raise typer.Abort()

    client = get_client(url=url, token=token)
    try:
        client.dns.delete_zone(zone_id)
        print_success(f"DNS zone {zone_id} deleted")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("records")
def list_records(
    zone_id: int = typer.Option(..., "--zone-id", "-z", help="Zone ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List DNS records for a zone."""
    client = get_client(url=url, token=token)
    try:
        records = client.dns.list_records(zone_id)
        print_result(records, format=format, columns=["id", "name", "record_type", "content", "ttl"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("record-create")
def create_record(
    zone_id: int = typer.Option(..., "--zone-id", "-z", help="Zone ID"),
    name: str = typer.Option(..., "--name", "-n"),
    record_type: str = typer.Option(..., "--type", "-t", help="A, AAAA, CNAME, MX, TXT, NS, PTR, SRV, SOA, CAA"),
    content: str = typer.Option(..., "--content", "-c"),
    ttl: int = typer.Option(3600, "--ttl"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Create a DNS record."""
    client = get_client(url=url, token=token)
    try:
        record = client.dns.create_record(
            zone_id, name=name, record_type=record_type, content=content, ttl=ttl
        )
        print_result(record, format=format)
        print_success(f"DNS record '{name} {record_type}' created")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("record-delete")
def delete_record(
    record_id: int = typer.Argument(..., help="Record ID"),
    yes: bool = typer.Option(False, "--yes", "-y"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Delete a DNS record."""
    if not yes:
        confirm = typer.confirm(f"Delete DNS record {record_id}?")
        if not confirm:
            raise typer.Abort()

    client = get_client(url=url, token=token)
    try:
        client.dns.delete_record(record_id)
        print_success(f"DNS record {record_id} deleted")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)
