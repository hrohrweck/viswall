"""Firewall commands."""

from typing import Any, Dict, Optional

import typer

from viswall_cli.utils import get_client
from viswall_cli.output import print_result, print_success, print_error
from viswall.exceptions import ViswallAPIError

app = typer.Typer(help="Manage firewall rules")


@app.command("list")
def list_rules(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List firewall rules for an instance."""
    client = get_client(url=url, token=token)
    try:
        rules = client.firewall.list_rules(instance_id)
        print_result(rules, format=format, columns=["id", "name", "action", "chain", "protocol", "dst_port"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def create(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    name: str = typer.Option(..., "--name", "-n", help="Rule name"),
    action: str = typer.Option(..., "--action", "-a", help="Action: accept, drop, reject"),
    chain: str = typer.Option("input", "--chain", "-c", help="Chain: input, output, forward"),
    protocol: str = typer.Option("tcp", "--protocol", "-p", help="Protocol: tcp, udp, icmp, any"),
    src_ip: Optional[str] = typer.Option(None, "--src-ip"),
    dst_ip: Optional[str] = typer.Option(None, "--dst-ip"),
    src_port: Optional[int] = typer.Option(None, "--src-port"),
    dst_port: Optional[int] = typer.Option(None, "--dst-port"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Create a firewall rule."""
    client = get_client(url=url, token=token)
    try:
        data: Dict[str, Any] = {
            "name": name,
            "action": action,
            "chain": chain,
            "protocol": protocol,
        }
        if src_ip:
            data["src_ip"] = src_ip
        if dst_ip:
            data["dst_ip"] = dst_ip
        if src_port:
            data["src_port"] = src_port
        if dst_port:
            data["dst_port"] = dst_port

        rule = client.firewall.create_rule(instance_id, **data)
        print_result(rule, format=format)
        print_success(f"Rule '{name}' created")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def delete(
    rule_id: int = typer.Argument(..., help="Rule ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Delete a firewall rule."""
    if not yes:
        confirm = typer.confirm(f"Delete rule {rule_id}?")
        if not confirm:
            raise typer.Abort()

    client = get_client(url=url, token=token)
    try:
        client.firewall.delete_rule(rule_id)
        print_success(f"Rule {rule_id} deleted")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def apply(
    instance_id: int = typer.Argument(..., help="Instance ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Apply firewall configuration to instance."""
    client = get_client(url=url, token=token)
    try:
        result = client.firewall.apply_rules(instance_id)
        print_success(f"Firewall rules applied to instance {instance_id}")
        if result:
            print_result(result, format="json")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)
