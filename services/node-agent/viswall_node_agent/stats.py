"""Per-interface byte counters from /proc/net/dev.

The agent runs host-network, so /proc/net/dev is the host's interface
statistics file. All interfaces are returned unfiltered — filtering
policy (drop lo/veth/bridges etc.) belongs to the api-gateway collector.
"""

from __future__ import annotations

from pathlib import Path

from viswall_node_agent.payloads import InterfaceCounters

DEFAULT_PROC_NET_DEV = Path("/proc/net/dev")


def parse_proc_net_dev(text: str) -> list[InterfaceCounters]:
    """Parse /proc/net/dev text into cumulative per-interface counters.

    Skips the two header lines and any row that has no name/field
    separator, fewer than the nine receive fields, or non-numeric
    counters.
    """
    counters: list[InterfaceCounters] = []
    for line in text.splitlines()[2:]:  # first two lines are headers
        if ":" not in line:
            continue
        name, raw = line.split(":", 1)
        fields = raw.split()
        if len(fields) < 9:
            continue
        try:
            counters.append(
                InterfaceCounters(
                    name=name.strip(),
                    rx_bytes=int(fields[0]),
                    tx_bytes=int(fields[8]),
                )
            )
        except ValueError:
            continue
    return counters


def read_interface_counters(
    path: Path = DEFAULT_PROC_NET_DEV,
) -> list[InterfaceCounters]:
    """Read cumulative counters for every host interface.

    Raises OSError when the file cannot be read; the endpoint maps that
    to HTTP 500.
    """
    return parse_proc_net_dev(path.read_text())
