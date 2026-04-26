"""Viswall CLI main entrypoint."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from viswall import ViswallClient
from viswall.exceptions import AuthenticationError, ViswallAPIError

from viswall_cli.config import Config, DEFAULT_CONFIG_FILE
from viswall_cli.output import print_error, print_success
from viswall_cli.commands import instances_app, firewall_app, users_app, metrics_app, dhcp_app

app = typer.Typer(
    name="viswall",
    help="Command-line interface for Viswall security appliance platform",
    no_args_is_help=True,
)
console = Console()


@app.command()
def login(
    url: str = typer.Option(..., "--url", "-u", help="Viswall instance URL"),
    username: str = typer.Option(..., "--username", "-U", help="Username"),
    password: str = typer.Option(..., "--password", "-p", help="Password", prompt=True, hide_input=True),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
) -> None:
    """Login and save credentials to config file."""
    client = ViswallClient(base_url=url)
    try:
        result = client.auth.login(username, password)
        token = result.get("access_token")
        if not token:
            print_error("Login failed: no access token in response")
            raise typer.Exit(1)

        config = Config(url=url, token=token)
        config.save(config_file)
        print_success(f"Logged in to {url}")
    except AuthenticationError as e:
        print_error(f"Authentication failed: {e}")
        raise typer.Exit(1)
    except ViswallAPIError as e:
        print_error(f"API error: {e}")
        raise typer.Exit(1)


@app.command()
def config_show(
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
) -> None:
    """Show current configuration."""
    config = Config.from_file(config_file)
    env_config = Config.from_env()
    merged = config.merge(env_config)

    if not merged.url and not merged.token:
        console.print("[dim]No configuration found.[/dim]")
        console.print(f"Config file: {config_file or DEFAULT_CONFIG_FILE}")
        return

    console.print(f"URL:   {merged.url or '[dim]not set[/dim]'}")
    if merged.token:
        masked = merged.token[:8] + "..." + merged.token[-4:]
        console.print(f"Token: {masked}")
    else:
        console.print("Token: [dim]not set[/dim]")


app.add_typer(instances_app, name="instances")
app.add_typer(firewall_app, name="firewall")
app.add_typer(users_app, name="users")
app.add_typer(metrics_app, name="metrics")
app.add_typer(dhcp_app, name="dhcp")


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
) -> None:
    """Viswall CLI — manage your security appliances."""
    if version:
        console.print("viswall-cli 0.1.0")
        raise typer.Exit()
