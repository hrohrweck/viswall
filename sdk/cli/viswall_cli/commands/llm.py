"""LLM admin commands."""

from typing import Optional

import typer

from viswall_cli.utils import get_client
from viswall_cli.output import print_result, print_success, print_error
from viswall.exceptions import ViswallAPIError

app = typer.Typer(help="Manage LLM providers and models")


@app.command("providers")
def list_providers(
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List LLM providers."""
    client = get_client(url=url, token=token)
    try:
        providers = client.llm_admin.list_providers()
        print_result(providers, format=format, columns=["id", "name", "provider_type", "enabled"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("provider-create")
def create_provider(
    name: str = typer.Option(..., "--name", "-n"),
    provider_type: str = typer.Option(..., "--type", "-t", help="openai, anthropic, ollama"),
    api_key: Optional[str] = typer.Option(None, "--api-key"),
    base_url: Optional[str] = typer.Option(None, "--base-url"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Create an LLM provider."""
    client = get_client(url=url, token=token)
    try:
        data = {"name": name, "provider_type": provider_type}
        if api_key:
            data["api_key"] = api_key
        if base_url:
            data["base_url"] = base_url
        result = client.llm_admin.create_provider(**data)
        print_result(result, format=format)
        print_success(f"LLM provider '{name}' created")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("provider-delete")
def delete_provider(
    provider_id: int = typer.Argument(..., help="Provider ID"),
    yes: bool = typer.Option(False, "--yes", "-y"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Delete an LLM provider."""
    if not yes:
        confirm = typer.confirm(f"Delete LLM provider {provider_id}?")
        if not confirm:
            raise typer.Abort()

    client = get_client(url=url, token=token)
    try:
        client.llm_admin.delete_provider(provider_id)
        print_success(f"LLM provider {provider_id} deleted")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("provider-test")
def test_provider(
    provider_id: int = typer.Argument(..., help="Provider ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Test an LLM provider connection."""
    client = get_client(url=url, token=token)
    try:
        result = client.llm_admin.test_provider(provider_id)
        print_result(result, format=format)
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("models")
def list_models(
    provider_id: Optional[int] = typer.Option(None, "--provider-id", "-p"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List LLM models."""
    client = get_client(url=url, token=token)
    try:
        models = client.llm_admin.list_models(provider_id=provider_id)
        print_result(models, format=format, columns=["id", "name", "provider_id", "enabled"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)
