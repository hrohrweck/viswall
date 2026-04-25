"""Viswall CLI configuration management."""

import os
from pathlib import Path
from typing import Optional

import yaml


DEFAULT_CONFIG_DIR = Path.home() / ".config" / "viswall"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"


class Config:
    """CLI configuration."""

    def __init__(self, url: Optional[str] = None, token: Optional[str] = None):
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

        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

        return cls(
            url=data.get("url"),
            token=data.get("token"),
        )

    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        config_path = path or DEFAULT_CONFIG_FILE
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {}
        if self.url:
            data["url"] = self.url
        if self.token:
            data["token"] = self.token

        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    def merge(self, other: "Config") -> "Config":
        """Merge another config, preferring non-None values from other."""
        return Config(
            url=other.url or self.url,
            token=other.token or self.token,
        )

    def is_complete(self) -> bool:
        """Check if config has all required values."""
        return bool(self.url and self.token)
