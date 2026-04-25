"""User commands."""

from typing import Optional

import typer

from viswall_cli.utils import get_client
from viswall_cli.output import print_result, print_success, print_error
from viswall.exceptions import ViswallAPIError

app = typer.Typer(help="Manage users")


@app.command("list")
def list_users(
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List all users."""
    client = get_client(url=url, token=token)
    try:
        users = client.users.list()
        print_result(users, format=format, columns=["id", "username", "email", "role", "created_at"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def create(
    username: str = typer.Argument(..., help="Username"),
    email: str = typer.Argument(..., help="Email address"),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True),
    role: str = typer.Option("user", "--role", "-r", help="Role: admin or user"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Create a new user."""
    client = get_client(url=url, token=token)
    try:
        user = client.users.create(
            username=username,
            email=email,
            password=password,
            role=role,
        )
        print_result(user, format=format)
        print_success(f"User '{username}' created")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)
