"""Viswall CLI configuration management."""

import os
from pathlib import Path
from typing import Optional

import yaml


DEFAULT_CONFIG_DIR = Path.home() / ".config" / "viswall"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"


class Config:
    """CLI configuration.

    The bearer token is read from the environment or the config file and
    sent as an Authorization header to `url`. Both inputs are attacker-
    controllable files, so the URL is validated to an http(s) origin and
    the token is only ever persisted with owner-only file permissions.
    """

    def __init__(self, url: Optional[str] = None, token: Optional[str] = None):
        if url and not url.lower().startswith(("http://", "https://")):
            raise ValueError(
                f"invalid url {url!r}: must start with http:// or https://"
            )
        self.url = url
        self.token = token

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            url=os.environ.get("VISWALL_URL"),
            token=os.environ.get("VISWALL_TOKEN"),
        )

    @classmethod
    def from_file(cls, path: Optional[Path] = None) -> "Config":
        """Load configuration from file."""
        config_path = path or DEFAULT_CONFIG_FILE
        if not config_path.exists():
            return cls()

        # A token stored by an older CLI version may be group/world
        # readable — tighten it before reading (ssh-style).
        if config_path.stat().st_mode & 0o077:
            config_path.chmod(0o600)

        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

        return cls(
            url=data.get("url"),
            token=data.get("token"),
        )

    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        config_path = Path(path or DEFAULT_CONFIG_FILE).expanduser().resolve()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {}
        if self.url:
            data["url"] = self.url
        if self.token:
            data["token"] = self.token

        # The file carries a bearer token, so create/keep it owner-only.
        fd = os.open(config_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
        config_path.chmod(0o600)

    def merge(self, other: "Config") -> "Config":
        """Merge another config, preferring non-None values from other."""
        return Config(
            url=other.url or self.url,
            token=other.token or self.token,
        )

    def is_complete(self) -> bool:
        """Check if config has all required values."""
        return bool(self.url and self.token)
