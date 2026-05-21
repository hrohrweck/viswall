"""Groupware commands."""

from typing import Optional

import typer

from viswall_cli.utils import get_client
from viswall_cli.output import print_result, print_success, print_error
from viswall.exceptions import ViswallAPIError

app = typer.Typer(help="Manage SOGo groupware per domain")


@app.command("status")
def get_status(
    domain_id: int = typer.Argument(..., help="Domain ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Get groupware status for a mail domain."""
    client = get_client(url=url, token=token)
    try:
        status = client.groupware.get_status(domain_id)
        print_result(status, format=format)
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("enable")
def enable(
    domain_id: int = typer.Argument(..., help="Domain ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Enable groupware for a mail domain."""
    client = get_client(url=url, token=token)
    try:
        client.groupware.enable(domain_id)
        print_success(f"Groupware enabled for domain {domain_id}")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("disable")
def disable(
    domain_id: int = typer.Argument(..., help="Domain ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Disable groupware for a mail domain."""
    client = get_client(url=url, token=token)
    try:
        client.groupware.disable(domain_id)
        print_success(f"Groupware disabled for domain {domain_id}")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)
