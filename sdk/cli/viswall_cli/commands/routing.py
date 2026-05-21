"""Routing commands."""

from typing import Any, Dict, Optional

import typer

from viswall_cli.utils import get_client
from viswall_cli.output import print_result, print_success, print_error
from viswall.exceptions import ViswallAPIError

app = typer.Typer(help="Manage routing rules")


@app.command("rules")
def list_rules(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List routing rules for an instance."""
    client = get_client(url=url, token=token)
    try:
        rules = client.routing.list_rules(instance_id)
        print_result(rules, format=format, columns=["id", "name", "destination", "gateway", "priority", "enabled"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("rule-create")
def create_rule(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    name: str = typer.Option(..., "--name", "-n"),
    destination: str = typer.Option(..., "--destination", "-d", help="Destination CIDR"),
    gateway: str = typer.Option(..., "--gateway", "-g", help="Gateway IP"),
    priority: int = typer.Option(100, "--priority", "-p"),
    interface: Optional[str] = typer.Option(None, "--interface"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Create a routing rule."""
    client = get_client(url=url, token=token)
    try:
        data: Dict[str, Any] = {
            "name": name,
            "destination": destination,
            "gateway": gateway,
            "priority": priority,
        }
        if interface:
            data["interface"] = interface
        rule = client.routing.create_rule(instance_id, **data)
        print_result(rule, format=format)
        print_success(f"Routing rule '{name}' created")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("rule-delete")
def delete_rule(
    rule_id: int = typer.Argument(..., help="Rule ID"),
    yes: bool = typer.Option(False, "--yes", "-y"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Delete a routing rule."""
    if not yes:
        confirm = typer.confirm(f"Delete routing rule {rule_id}?")
        if not confirm:
            raise typer.Abort()

    client = get_client(url=url, token=token)
    try:
        client.routing.delete_rule(rule_id)
        print_success(f"Routing rule {rule_id} deleted")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("apply")
def apply_rules(
    instance_id: int = typer.Argument(..., help="Instance ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Apply routing configuration to instance."""
    client = get_client(url=url, token=token)
    try:
        result = client.routing.apply_rules(instance_id)
        print_success(f"Routing rules applied to instance {instance_id}")
        if result:
            print_result(result, format="json")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)
