"""Mail commands."""

from typing import Any, Dict, Optional

import typer

from viswall_cli.utils import get_client
from viswall_cli.output import print_result, print_success, print_error
from viswall.exceptions import ViswallAPIError

app = typer.Typer(help="Manage mail domains and users")


@app.command("domains")
def list_domains(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List mail domains for an instance."""
    client = get_client(url=url, token=token)
    try:
        domains = client.mail.list_domains(instance_id)
        print_result(domains, format=format, columns=["id", "domain", "enabled", "users_count"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("domain-create")
def create_domain(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    domain: str = typer.Option(..., "--domain", "-d", help="Domain name"),
    dkim_enabled: bool = typer.Option(True, "--dkim/--no-dkim"),
    spam_enabled: bool = typer.Option(True, "--spam/--no-spam"),
    virus_enabled: bool = typer.Option(True, "--virus/--no-virus"),
    llm_enabled: bool = typer.Option(False, "--llm/--no-llm"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Create a mail domain."""
    client = get_client(url=url, token=token)
    try:
        result = client.mail.create_domain(
            instance_id,
            domain=domain,
            dkim_enabled=dkim_enabled,
            spam_enabled=spam_enabled,
            virus_enabled=virus_enabled,
            llm_enabled=llm_enabled,
        )
        print_result(result, format=format)
        print_success(f"Mail domain '{domain}' created")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("domain-delete")
def delete_domain(
    domain_id: int = typer.Argument(..., help="Domain ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Delete a mail domain."""
    if not yes:
        confirm = typer.confirm(f"Delete mail domain {domain_id}?")
        if not confirm:
            raise typer.Abort()

    client = get_client(url=url, token=token)
    try:
        client.mail.delete_domain(domain_id)
        print_success(f"Mail domain {domain_id} deleted")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("users")
def list_users(
    domain_id: int = typer.Option(..., "--domain-id", "-d", help="Domain ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List mail users for a domain."""
    client = get_client(url=url, token=token)
    try:
        users = client.mail.list_users(domain_id)
        print_result(users, format=format, columns=["id", "username", "email", "quota"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("user-create")
def create_user(
    domain_id: int = typer.Option(..., "--domain-id", "-d", help="Domain ID"),
    username: str = typer.Option(..., "--username", "-u", help="Username"),
    password: str = typer.Option(..., "--password", "-p", help="Password"),
    email: Optional[str] = typer.Option(None, "--email", "-e"),
    quota: int = typer.Option(1073741824, "--quota", help="Quota in bytes (default 1GB)"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Create a mail user."""
    client = get_client(url=url, token=token)
    try:
        data: Dict[str, Any] = {
            "username": username,
            "password": password,
            "quota": quota,
        }
        if email:
            data["email"] = email
        result = client.mail.create_user(domain_id, **data)
        print_result(result, format=format)
        print_success(f"Mail user '{username}' created")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("user-delete")
def delete_user(
    user_id: int = typer.Argument(..., help="User ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Delete a mail user."""
    if not yes:
        confirm = typer.confirm(f"Delete mail user {user_id}?")
        if not confirm:
            raise typer.Abort()

    client = get_client(url=url, token=token)
    try:
        client.mail.delete_user(user_id)
        print_success(f"Mail user {user_id} deleted")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("classify")
def test_classify(
    instance_id: int = typer.Option(..., "--instance-id", "-i", help="Instance ID"),
    subject: str = typer.Option(..., "--subject", "-s"),
    body: str = typer.Option(..., "--body", "-b"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Test email classification."""
    client = get_client(url=url, token=token)
    try:
        result = client.mail.test_classify(instance_id, subject=subject, body=body)
        print_result(result, format=format)
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)
