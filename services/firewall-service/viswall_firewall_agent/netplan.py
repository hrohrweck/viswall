"""Interface configuration via netplan — implemented in todo 9.

The render/apply flow (``netplan try --timeout`` with probe-then-confirm and
the live-state WAN guardrails) lands in todo 9. This module exists so the
package layout is complete and todo 9 has a home; nothing here is wired up yet.
"""

from __future__ import annotations


class NetplanManager:
    """Stub — todo 9 implements render/apply with try-auto-revert."""
