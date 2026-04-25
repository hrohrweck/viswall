"""Metrics commands."""

from typing import Optional

import typer

from viswall_cli.utils import get_client
from viswall_cli.output import print_result, print_error
from viswall.exceptions import ViswallAPIError

app = typer.Typer(help="View metrics and monitoring data")


@app.command("latest")
def latest(
    instance_id: int = typer.Argument(..., help="Instance ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Get latest metrics for an instance."""
    client = get_client(url=url, token=token)
    try:
        metrics = client.metrics.get_latest(instance_id)
        print_result(metrics, format=format)
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def overview(
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Get global metrics overview."""
    client = get_client(url=url, token=token)
    try:
        data = client.metrics.get_overview()
        print_result(data, format=format)
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)
