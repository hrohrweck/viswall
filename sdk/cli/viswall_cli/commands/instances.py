"""Instance commands."""

from typing import Optional

import typer

from viswall_cli.utils import get_client
from viswall_cli.output import print_result, print_success, print_error
from viswall.exceptions import ViswallAPIError

app = typer.Typer(help="Manage Viswall instances")


@app.command("list")
def list_instances(
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List all instances."""
    client = get_client(url=url, token=token)
    try:
        instances = client.instances.list()
        print_result(instances, format=format, columns=["id", "name", "hostname", "status"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def create(
    name: str = typer.Argument(..., help="Instance name"),
    hostname: str = typer.Argument(..., help="Hostname or IP address"),
    api_endpoint: Optional[str] = typer.Option(None, "--api-endpoint"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Create a new instance."""
    client = get_client(url=url, token=token)
    try:
        data = {"name": name, "hostname": hostname}
        if api_endpoint:
            data["api_endpoint"] = api_endpoint
        instance = client.instances.create(**data)
        print_result(instance, format=format)
        print_success(f"Instance '{name}' created")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def get(
    instance_id: int = typer.Argument(..., help="Instance ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Get instance details."""
    client = get_client(url=url, token=token)
    try:
        instance = client.instances.get(instance_id)
        print_result(instance, format=format)
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def delete(
    instance_id: int = typer.Argument(..., help="Instance ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Delete an instance."""
    if not yes:
        confirm = typer.confirm(f"Are you sure you want to delete instance {instance_id}?")
        if not confirm:
            raise typer.Abort()

    client = get_client(url=url, token=token)
    try:
        client.instances.delete(instance_id)
        print_success(f"Instance {instance_id} deleted")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)
