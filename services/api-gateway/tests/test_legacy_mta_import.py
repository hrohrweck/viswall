"""Unit tests for legacy MTA-forwarding import in scripts/migrate_legacy_mail.py.

The migration script is loaded as a module (NOT executed) so its pure helper can
be exercised without touching any database.
"""
import importlib.util
from pathlib import Path

import pytest


def _script_path() -> Path:
    for base in Path(__file__).resolve().parents:
        cand = base / "scripts" / "migrate_legacy_mail.py"
        if cand.is_file():
            return cand
    raise FileNotFoundError("scripts/migrate_legacy_mail.py not found in any parent")


def _load_module():
    spec = importlib.util.spec_from_file_location("migrate_legacy_mail", _script_path())
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def migrate_mod():
    return _load_module()


@pytest.mark.parametrize(
    ("staticroute", "staticroute_ip"),
    [
        (1, "83.164.137.172"),
        (1, "avg.net4you.net"),
    ],
)
def test_mta_fields_enabled_when_staticroute_set_and_host_present(migrate_mod, staticroute, staticroute_ip):
    """Given staticroute=1 and a non-empty target host, forwarding is enabled on port 25."""
    assert migrate_mod.mta_fields_from_legacy(staticroute, staticroute_ip) == (True, staticroute_ip, 25)


@pytest.mark.parametrize(
    ("staticroute", "staticroute_ip"),
    [
        (0, "1.2.3.4"),
        (1, ""),
        (1, None),
    ],
)
def test_mta_fields_disabled_without_staticroute_or_host(migrate_mod, staticroute, staticroute_ip):
    """Given no staticroute or no target host, forwarding is disabled with host None."""
    assert migrate_mod.mta_fields_from_legacy(staticroute, staticroute_ip) == (False, None, 25)
