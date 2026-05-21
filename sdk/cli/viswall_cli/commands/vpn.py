"""VPN commands."""

from typing import Any, Dict, Optional

import typer

from viswall_cli.utils import get_client
from viswall_cli.output import print_result, print_success, print_error
from viswall.exceptions import ViswallAPIError

app = typer.Typer(help="Manage VPN servers and clients")


@app.command("servers")
def list_servers(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List VPN servers for an instance."""
    client = get_client(url=url, token=token)
    try:
        servers = client.vpn.list_servers(instance_id)
        print_result(servers, format=format, columns=["id", "name", "protocol", "port", "status"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("server-create")
def create_server(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    name: str = typer.Option(..., "--name", "-n", help="Server name"),
    protocol: str = typer.Option(..., "--protocol", "-p", help="Protocol: wireguard, openvpn, ipsec, l2tp, pptp"),
    port: int = typer.Option(51820, "--port", help="Listen port"),
    network: str = typer.Option(..., "--network", help="Client tunnel network CIDR"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Create a VPN server."""
    client = get_client(url=url, token=token)
    try:
        server = client.vpn.create_server(
            instance_id, name=name, protocol=protocol, port=port, network=network
        )
        print_result(server, format=format)
        print_success(f"VPN server '{name}' created")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("server-delete")
def delete_server(
    server_id: int = typer.Argument(..., help="Server ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Delete a VPN server."""
    if not yes:
        confirm = typer.confirm(f"Delete VPN server {server_id}?")
        if not confirm:
            raise typer.Abort()

    client = get_client(url=url, token=token)
    try:
        client.vpn.delete_server(server_id)
        print_success(f"VPN server {server_id} deleted")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("start")
def start_server(
    server_id: int = typer.Argument(..., help="Server ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Start a VPN server."""
    client = get_client(url=url, token=token)
    try:
        client.vpn.start_server(server_id)
        print_success(f"VPN server {server_id} started")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("stop")
def stop_server(
    server_id: int = typer.Argument(..., help="Server ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Stop a VPN server."""
    client = get_client(url=url, token=token)
    try:
        client.vpn.stop_server(server_id)
        print_success(f"VPN server {server_id} stopped")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("restart")
def restart_server(
    server_id: int = typer.Argument(..., help="Server ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Restart a VPN server."""
    client = get_client(url=url, token=token)
    try:
        client.vpn.restart_server(server_id)
        print_success(f"VPN server {server_id} restarted")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("clients")
def list_clients(
    server_id: int = typer.Option(..., "--server-id", "-s", help="Server ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List VPN clients for a server."""
    client = get_client(url=url, token=token)
    try:
        clients = client.vpn.list_clients(server_id)
        print_result(clients, format=format, columns=["id", "name", "ip_address", "enabled"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("client-create")
def create_client(
    server_id: int = typer.Option(..., "--server-id", "-s", help="Server ID"),
    name: str = typer.Option(..., "--name", "-n", help="Client name"),
    email: Optional[str] = typer.Option(None, "--email", "-e"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Create a VPN client."""
    client = get_client(url=url, token=token)
    try:
        data: Dict[str, Any] = {"name": name}
        if email:
            data["email"] = email
        result = client.vpn.create_client(server_id, **data)
        print_result(result, format=format)
        print_success(f"VPN client '{name}' created")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("client-config")
def get_client_config(
    client_id: int = typer.Argument(..., help="Client ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Get VPN client configuration."""
    client = get_client(url=url, token=token)
    try:
        config = client.vpn.get_client_config(client_id)
        print_result(config, format="json")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)
