"""Viswall node agent — host interface discovery, live apply and persistence.

Runs in a container that shares the host network namespace
(`network_mode: host`) with NET_ADMIN, so netlink changes affect the
host's real interfaces. Desired-state persistence is written as a
netplan file so configuration survives reboots.
"""

__version__ = "1.0.0"
