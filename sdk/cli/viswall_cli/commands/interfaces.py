"""Host interface management commands."""

from typing import Any, Dict, Optional

import typer

from viswall_cli.utils import get_client
from viswall_cli.output import print_result, print_success, print_error
from viswall.exceptions import ViswallAPIError

app = typer.Typer(help="Manage host network interfaces via the node agent")


@app.command("list")
def list_interfaces(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List configured (desired-state) interfaces for an instance."""
    client = get_client(url=url, token=token)
    try:
        interfaces = client.network.list_interfaces(instance_id)
        print_result(
            interfaces,
            format=format,
            columns=["id", "name", "type", "config_type", "ip_address", "gateway", "mtu", "enabled"],
        )
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("live")
def live_interfaces(
    instance_id: int = typer.Argument(..., help="Instance ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """Show live host interface state reported by the node agent."""
    client = get_client(url=url, token=token)
    try:
        state = client.network.live_interfaces(instance_id)
        print_result(state.get("interfaces", []), format=format)
        print_success(
            f"default route: {state.get('default_route_interface') or '-'}"
            f" via {state.get('default_gateway') or '-'}"
        )
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("create")
def create_interface(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    name: str = typer.Option(..., "--name", "-n", help="Interface name, e.g. ens18"),
    config_type: str = typer.Option("static", "--config-type", help="static or dhcp"),
    ip_address: Optional[str] = typer.Option(None, "--ip"),
    netmask: Optional[str] = typer.Option(None, "--netmask", help="e.g. 255.255.255.0"),
    gateway: Optional[str] = typer.Option(None, "--gateway", "-g"),
    mtu: Optional[int] = typer.Option(None, "--mtu"),
    iface_type: str = typer.Option("other", "--type", help="wan, lan, dmz or other"),
    enabled: bool = typer.Option(True, "--enabled/--disabled"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Add an interface to the instance's desired configuration."""
    client = get_client(url=url, token=token)
    try:
        interface = client.network.create_interface(
            instance_id,
            name=name,
            type=iface_type,
            config_type=config_type,
            ip_address=ip_address,
            netmask=netmask,
            gateway=gateway,
            mtu=mtu,
            enabled=enabled,
        )
        print_result(interface, format=format)
        print_success(f"Interface '{name}' added")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("update")
def update_interface(
    interface_id: int = typer.Argument(..., help="Interface ID"),
    ip_address: Optional[str] = typer.Option(None, "--ip"),
    netmask: Optional[str] = typer.Option(None, "--netmask"),
    gateway: Optional[str] = typer.Option(None, "--gateway", "-g"),
    mtu: Optional[int] = typer.Option(None, "--mtu"),
    enabled: Optional[bool] = typer.Option(None, "--enabled/--disabled"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Update desired state for one interface (apply separately)."""
    client = get_client(url=url, token=token)
    try:
        kwargs: Dict[str, Any] = {}
        if ip_address is not None:
            kwargs["ip_address"] = ip_address
        if netmask is not None:
            kwargs["netmask"] = netmask
        if gateway is not None:
            kwargs["gateway"] = gateway
        if mtu is not None:
            kwargs["mtu"] = mtu
        if enabled is not None:
            kwargs["enabled"] = enabled
        interface = client.network.update_interface(interface_id, **kwargs)
        print_result(interface, format=format)
        print_success(f"Interface {interface_id} updated")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("delete")
def delete_interface(
    interface_id: int = typer.Argument(..., help="Interface ID"),
    yes: bool = typer.Option(False, "--yes", "-y"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Remove an interface from the desired configuration."""
    if not yes:
        confirm = typer.confirm(f"Delete interface {interface_id}?")
        if not confirm:
            raise typer.Abort()

    client = get_client(url=url, token=token)
    try:
        client.network.delete_interface(interface_id)
        print_success(f"Interface {interface_id} removed")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("apply")
def apply_interfaces(
    instance_id: int = typer.Argument(..., help="Instance ID"),
    force: bool = typer.Option(
        False, "--force", "-f",
        help="Allow changes touching the default-route interface (may cut connectivity)",
    ),
    yes: bool = typer.Option(False, "--yes", "-y"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-F"),
) -> None:
    """Apply the desired interface configuration to the host."""
    if not yes:
        confirm = typer.confirm(
            f"Apply interface configuration on instance {instance_id}? "
            "Changes take effect immediately."
        )
        if not confirm:
            raise typer.Abort()

    client = get_client(url=url, token=token)
    try:
        result = client.network.apply_interfaces(instance_id, force=force)
        if result.get("success"):
            print_success(result.get("message", "applied"))
        else:
            print_error(result.get("message", "apply failed"))
        changes = result.get("changes", [])
        if changes:
            print_result(changes, format=format)
        if result.get("netplan_written"):
            print_success(f"persisted to {result.get('netplan_file')}")
        if not result.get("success"):
            raise typer.Exit(1)
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)
