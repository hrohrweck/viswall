"""Shared utilities for CLI commands."""

from pathlib import Path
from typing import Optional

import typer

from viswall import ViswallClient
from viswall_cli.config import Config
from viswall_cli.output import print_error


def get_client(
    url: Optional[str] = None,
    token: Optional[str] = None,
    config_file: Optional[Path] = None,
) -> ViswallClient:
    """Create a ViswallClient from CLI options, env vars, and config file."""
    file_config = Config.from_file(config_file)
    env_config = Config.from_env()
    cli_config = Config(url=url, token=token)

    # Priority: CLI > env > file
    config = file_config.merge(env_config).merge(cli_config)

    if not config.url:
        print_error(
            "No URL configured. Set --url, VISWALL_URL environment variable, "
            "or run 'viswall login' to configure."
        )
        raise typer.Exit(1)

    if not config.token:
        print_error(
            "No token configured. Set --token, VISWALL_TOKEN environment variable, "
            "or run 'viswall login' to configure."
        )
        raise typer.Exit(1)

    return ViswallClient(base_url=config.url, token=config.token)
