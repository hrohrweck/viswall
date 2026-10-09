"""Mail commands."""

from typing import Any, Dict, List, Optional

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
    mta_forward_enabled: bool = typer.Option(False, "--mta-forward/--no-mta-forward"),
    mta_forward_host: Optional[str] = typer.Option(None, "--mta-forward-host"),
    mta_forward_port: int = typer.Option(25, "--mta-forward-port"),
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
            mta_forward_enabled=mta_forward_enabled,
            mta_forward_host=mta_forward_host,
            mta_forward_port=mta_forward_port,
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


@app.command("domain-update")
def update_domain(
    domain_id: int = typer.Argument(..., help="Domain ID"),
    mta_forward: Optional[bool] = typer.Option(None, "--mta-forward/--no-mta-forward"),
    mta_forward_host: Optional[str] = typer.Option(None, "--mta-forward-host"),
    mta_forward_port: Optional[int] = typer.Option(None, "--mta-forward-port"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Update a mail domain."""
    client = get_client(url=url, token=token)
    try:
        kwargs: Dict[str, Any] = {}
        if mta_forward is not None:
            kwargs["mta_forward_enabled"] = mta_forward
        if mta_forward_host is not None:
            kwargs["mta_forward_host"] = mta_forward_host
        if mta_forward_port is not None:
            kwargs["mta_forward_port"] = mta_forward_port
        result = client.mail.update_domain(domain_id, **kwargs)
        print_result(result, format=format)
        print_success(f"Mail domain {domain_id} updated")
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


@app.command("aliases")
def list_aliases(
    domain_id: int = typer.Option(..., "--domain-id", "-d", help="Domain ID"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List mail aliases for a domain."""
    client = get_client(url=url, token=token)
    try:
        aliases = client.mail.list_aliases(domain_id)
        print_result(aliases, format=format, columns=["id", "source", "destination", "enabled"])
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("alias-create")
def create_alias(
    domain_id: int = typer.Option(..., "--domain-id", "-d", help="Domain ID"),
    source: str = typer.Option(..., "--source", "-s", help="Alias address"),
    destination: List[str] = typer.Option(
        ..., "--destination", help="Destination address (repeatable)"
    ),
    enabled: bool = typer.Option(True, "--enabled/--no-enabled"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Create a mail alias (one alias per destination)."""
    client = get_client(url=url, token=token)
    try:
        results = []
        for dest in destination:
            result = client.mail.create_alias(
                domain_id, source=source, destination=dest, enabled=enabled
            )
            results.append(result)
        print_result(results, format=format)
        print_success(f"Mail alias '{source}' created")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("alias-update")
def update_alias(
    alias_id: int = typer.Argument(..., help="Alias ID"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
    destination: Optional[str] = typer.Option(None, "--destination"),
    enabled: Optional[bool] = typer.Option(None, "--enabled/--no-enabled"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
    format: str = typer.Option("json", "--format", "-f"),
) -> None:
    """Update a mail alias."""
    client = get_client(url=url, token=token)
    try:
        kwargs: Dict[str, Any] = {}
        if source is not None:
            kwargs["source"] = source
        if destination is not None:
            kwargs["destination"] = destination
        if enabled is not None:
            kwargs["enabled"] = enabled
        result = client.mail.update_alias(alias_id, **kwargs)
        print_result(result, format=format)
        print_success(f"Mail alias {alias_id} updated")
    except ViswallAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("alias-delete")
def delete_alias(
    alias_id: int = typer.Argument(..., help="Alias ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    token: Optional[str] = typer.Option(None, "--token", "-t"),
) -> None:
    """Delete a mail alias."""
    if not yes:
        confirm = typer.confirm(f"Delete mail alias {alias_id}?")
        if not confirm:
            raise typer.Abort()

    client = get_client(url=url, token=token)
    try:
        client.mail.delete_alias(alias_id)
        print_success(f"Mail alias {alias_id} deleted")
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
