"""Todo-9 note: the firewall agent owns NO netplan code anymore.

Upstream divergence: interface management (netplan) is owned by the
node-agent. The old firewall-service ``netplan.py`` stub was deleted in
todo 9. This module locks that deletion in: the module must not exist and no
file in the package may import it (the word "netplan" may still appear as a
data path — snapshots.py copies /etc/netplan — but never as an import).
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

import viswall_firewall_agent


def _package_dir() -> Path:
    return Path(viswall_firewall_agent.__file__).parent


def _imported_modules() -> set[str]:
    """Every module name imported (statically) anywhere in the package."""
    imports: set[str] = set()
    for path in sorted(_package_dir().glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
    return imports


def test_netplan_module_file_does_not_exist() -> None:
    assert not (_package_dir() / "netplan.py").exists()


def test_netplan_module_not_importable() -> None:
    with pytest.raises(ImportError):
        importlib.import_module("viswall_firewall_agent.netplan")


def test_no_import_reference_to_netplan_remains() -> None:
    for module in _imported_modules():
        assert "netplan" not in module.lower(), module


def test_package_imports_cleanly_without_netplan() -> None:
    # Importing the package (and its modules) must not fail on a missing netplan.
    import viswall_firewall_agent.api  # noqa: F401
    import viswall_firewall_agent.nft  # noqa: F401
    import viswall_firewall_agent.qos  # noqa: F401
    import viswall_firewall_agent.routing  # noqa: F401
    import viswall_firewall_agent.snapshots  # noqa: F401
