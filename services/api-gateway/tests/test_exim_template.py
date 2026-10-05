"""Pure file-read assertions for the Exim4 config template.

These tests guard the MTA-forwarding router wiring in the rendered template
without needing a running Exim/Postgres. They assert on raw string content.
"""

from __future__ import annotations

from pathlib import Path

TEMPLATE = (
    Path(__file__).resolve().parents[2]
    / "mail-service"
    / "config"
    / "exim4.conf.tmpl"
)


def _template_text() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def _router_block(text: str, name: str) -> str:
    """Return the block of lines belonging to router ``name``.

    A router starts at a line equal to ``name:`` (column 0) and extends until
    the next column-0 line that begins a new router (``<word>:``) or a new
    section (``begin ...``).
    """
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == f"{name}:" and line == line.lstrip():
            start = index
            break
    if start is None:
        raise AssertionError(f"router block {name!r} not found")

    block: list[str] = []
    for line in lines[start:]:
        if block and line and not line[0].isspace():
            break
        block.append(line)
    return "\n".join(block)


def _router_start_index(text: str, name: str) -> int:
    for index, line in enumerate(text.splitlines()):
        if line == f"{name}:":
            return index
    raise AssertionError(f"router block {name!r} not found")


def test_mta_forward_router_exists() -> None:
    text = _template_text()
    assert "mta_forward:" in text


def test_mta_forward_uses_manualroute_driver() -> None:
    block = _router_block(_template_text(), "mta_forward")
    assert "driver = manualroute" in block


def test_mta_forward_sets_no_more() -> None:
    block = _router_block(_template_text(), "mta_forward")
    assert "no_more" in block


def test_mta_forward_uses_remote_smtp_transport() -> None:
    block = _router_block(_template_text(), "mta_forward")
    assert "transport = remote_smtp" in block


def test_mta_forward_enabled_condition_lookup() -> None:
    block = _router_block(_template_text(), "mta_forward")
    assert "mta_forward_enabled=TRUE" in block


def test_mta_forward_precedes_alias_copy() -> None:
    text = _template_text()
    assert _router_start_index(text, "mta_forward") < _router_start_index(
        text, "alias_copy"
    )


def test_mta_forward_route_data_host_and_port() -> None:
    block = _router_block(_template_text(), "mta_forward")
    assert "mta_forward_host || '::' || mta_forward_port::text" in block
