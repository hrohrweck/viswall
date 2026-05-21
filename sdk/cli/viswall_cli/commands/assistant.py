"""Assistant commands."""

from typing import Optional

import typer

from viswall_cli.utils import get_client
from viswall_cli.output import print_result, print_success, print_error
from viswall.exceptions import ViswallAPIError

app = typer.Typer(help="Interact with the AI assistant")


@app.command("chat")
def chat(
    message: str = typer.Argument(..., help="Message to send"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Send a chat message to the assistant."""
    client = get_client(url=url, token=token)
    try:
        result = client.assistant.chat(message)
        print_result(result, format="json")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("suggest-rule")
def suggest_firewall_rule(
    description: str = typer.Argument(..., help="Rule description in natural language"),
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Ask the assistant to suggest a firewall rule."""
    client = get_client(url=url, token=token)
    try:
        result = client.assistant.suggest_firewall_rule(instance_id, description=description)
        print_result(result, format=format)
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)
