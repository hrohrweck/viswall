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


site_to_site_app = typer.Typer(help="Manage WireGuard site-to-site tunnels")


@site_to_site_app.command("status")
def site_to_site_status(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """Show site-to-site tunnel status for an instance."""
    client = get_client(url=url, token=token)
    try:
        rows = client.vpn.get_site_to_site_status(instance_id)
        print_result(rows, format=format, columns=["server_id", "name", "status", "agent"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@site_to_site_app.command("init")
def site_to_site_init(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    endpoint: str = typer.Option(..., "--endpoint", help="Remote endpoint, e.g. base0.example.com:51820"),
    peer_public_key: str = typer.Option(
        ..., "--peer-public-key", help="Remote peer's WireGuard public key (44-char base64)"
    ),
    allowed_ips: Optional[str] = typer.Option(None, "--allowed-ips"),
    local_address: Optional[str] = typer.Option(None, "--local-address"),
    persistent_keepalive: Optional[int] = typer.Option(None, "--persistent-keepalive"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Initialize a site-to-site tunnel and push it to the VPN agent."""
    client = get_client(url=url, token=token)
    try:
        options: Dict[str, Any] = {}
        if allowed_ips:
            options["allowed_ips"] = allowed_ips
        if local_address:
            options["local_address"] = local_address
        if persistent_keepalive is not None:
            options["persistent_keepalive"] = persistent_keepalive
        result = client.vpn.initialize_site_to_site(
            instance_id, endpoint, peer_public_key, **options
        )
        print_result(result, format=format)
        print_success("Site-to-site tunnel initialized")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


app.add_typer(site_to_site_app, name="site-to-site")
