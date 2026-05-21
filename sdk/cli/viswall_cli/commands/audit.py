"""Audit commands."""

from typing import Any, Optional

import typer

from viswall_cli.utils import get_client
from viswall_cli.output import print_result, print_error
from viswall.exceptions import ViswallAPIError

app = typer.Typer(help="Query audit logs")


@app.command("list")
def list_logs(
    limit: int = typer.Option(50, "--limit", "-l"),
    offset: int = typer.Option(0, "--offset"),
    resource_type: Optional[str] = typer.Option(None, "--resource-type"),
    action: Optional[str] = typer.Option(None, "--action"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List audit logs."""
    client = get_client(url=url, token=token)
    try:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if resource_type:
            params["resource_type"] = resource_type
        if action:
            params["action"] = action
        logs = client.audit.list_logs(**params)
        print_result(logs, format=format, columns=["id", "action", "resource_type", "resource_id", "user_id", "created_at"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("instance")
def instance_logs(
    instance_id: int = typer.Argument(..., help="Instance ID"),
    limit: int = typer.Option(50, "--limit", "-l"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """Get audit logs for a specific instance."""
    client = get_client(url=url, token=token)
    try:
        logs = client.audit.get_instance_logs(instance_id, limit=limit)
        print_result(logs, format=format, columns=["id", "action", "resource_type", "resource_id", "user_id", "created_at"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)
