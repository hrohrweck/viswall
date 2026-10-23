"""WireGuard site-to-site CLIENT manager.

Ownership model (single-owner, resolves the dual-owner trap): the
``wg-quick@client`` systemd unit REMAINS the single lifecycle owner of the
tunnel. This module only

  (a) renders and atomically writes ``/etc/wireguard/client.conf``, and
  (b) restarts/enables/disables that unit via
      ``nsenter -t 1 -m -u -i -n -- systemctl ...``.

It never runs ``wg-quick up/down`` as a second manager — two owners racing
the same interface leave a state neither can explain.

State-sync rules:

  * stop  = ``systemctl disable wg-quick@client`` + ``systemctl stop``
  * start = ``systemctl enable`` + ``systemctl start``
  * after ANY failed apply: restore the ``.viswall-backup`` file AND restart
    the unit (a failed unit stays failed until restarted).
  * startup reconcile is GATED behind ``$STATE_DIR/takeover`` — without that
    marker the agent never touches the unit's run/enabled state.

All subprocess calls below are READ-ONLY except ``_systemctl`` (nsenter) and
``write_config`` (the config file). ``wg`` is only ever invoked as
``wg show`` (read-only status).
"""

from __future__ import annotations

import ipaddress
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("/etc/wireguard/client.conf")
BACKUP_SUFFIX = ".viswall-backup"

_HANDSHAKE_LINE_RE = re.compile(r"latest handshake:\s+([^\n]*?)\s+ago")
_HANDSHAKE_TOKEN_RE = re.compile(r"(\d+)\s+(hour|minute|second)s?")
_HANDSHAKE_SECONDS = {"second": 1, "minute": 60, "hour": 3600}
_TRANSFER_RE = re.compile(r"transfer:\s+(\S+)\s+(\S+)\s+received,\s+(\S+)\s+(\S+)\s+sent")
_ENDPOINT_RE = re.compile(r"endpoint:\s+(\S+)")
_ALLOWED_IPS_RE = re.compile(r"allowed ips:\s+(\S[^\n]*)")
_SIZE_UNITS = {"B": 1, "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3, "TiB": 1024**4}

#: WireGuard keys are 32 bytes rendered as 44 base64 chars + trailing "=".
_WG_KEY_RE = re.compile(r"^[A-Za-z0-9+/]{43}=$")

#: Characters that could break out of a config line (newline injection into
#: a root-run wg-quick config is RCE — PostUp etc.) or alter an assignment.
_FORBIDDEN_CONFIG_CHARS = ("\n", "\r", "=")


class WgClientError(Exception):
    """Base class for WireGuard client manager failures."""


class WgConfigValidationError(WgClientError, ValueError):
    """A value that would land in client.conf failed validation."""


def validate_wg_key(value: str | None, label: str) -> str | None:
    """44-char base64 WireGuard key (the trailing '=' is the sole allowed one)."""
    if value is None:
        return None
    if not _WG_KEY_RE.fullmatch(value):
        raise WgConfigValidationError(
            f"{label} must be a 44-character base64 WireGuard key"
        )
    return value


def validate_local_address(value: str) -> str:
    """Strict IPv4Interface/IPv6Interface — an address with its prefix."""
    if any(ch in value for ch in _FORBIDDEN_CONFIG_CHARS):
        raise WgConfigValidationError("local_address contains forbidden characters")
    try:
        ipaddress.ip_interface(value)
    except ValueError as exc:
        raise WgConfigValidationError(
            f"local_address must be an IPv4/IPv6 address with prefix: {value!r}"
        ) from exc
    return value


def validate_allowed_ips(value: str) -> str:
    """Comma-separated CIDRs; every token must parse as an ip_network."""
    tokens = [token.strip() for token in value.split(",") if token.strip()]
    if not tokens:
        raise WgConfigValidationError("allowed_ips must list at least one CIDR")
    for token in tokens:
        if any(ch in token for ch in _FORBIDDEN_CONFIG_CHARS):
            raise WgConfigValidationError("allowed_ips contains forbidden characters")
        try:
            ipaddress.ip_network(token, strict=False)
        except ValueError as exc:
            raise WgConfigValidationError(
                f"invalid CIDR in allowed_ips: {token!r}"
            ) from exc
    return value


def validate_endpoint(value: str) -> str:
    """``host``, ``host:port`` or bracketed ``[v6]:port`` — nothing else."""
    if any(ch in value for ch in _FORBIDDEN_CONFIG_CHARS):
        raise WgConfigValidationError("endpoint contains forbidden characters")
    if value.startswith("["):
        match = re.fullmatch(r"\[[0-9a-fA-F:.]+\](?::(\d+))?", value)
        if not match:
            raise WgConfigValidationError(f"invalid endpoint: {value!r}")
        port = match.group(1)
    else:
        parts = value.split(":")
        if len(parts) > 2 or not re.fullmatch(r"[A-Za-z0-9.\-]+", parts[0]):
            raise WgConfigValidationError(f"invalid endpoint: {value!r}")
        port = parts[1] if len(parts) == 2 else None
    if port is not None:
        try:
            if not 1 <= int(port) <= 65535:
                raise ValueError
        except ValueError as exc:
            raise WgConfigValidationError(f"invalid endpoint port: {value!r}") from exc
    return value


def validate_config(model: "WgClientConfig") -> None:
    """Reject any model that would render an unsafe client.conf.

    Called by ``render_config`` so every path (API apply, direct write) is
    guarded at the final render seam.
    """
    validate_local_address(model.address)
    validate_endpoint(model.endpoint)
    validate_wg_key(model.peer_public_key, "peer_public_key")
    validate_wg_key(model.private_key, "private_key")
    validate_allowed_ips(model.allowed_ips)
    if not isinstance(model.persistent_keepalive, int) or not 0 <= model.persistent_keepalive <= 65535:
        raise WgConfigValidationError(
            "persistent_keepalive must be an integer between 0 and 65535"
        )


class WgUnitError(WgClientError):
    """A systemctl (enable/disable/start/stop) action on the unit failed."""

    def __init__(self, action: str, service: str, returncode: int, stderr: str) -> None:
        self.action = action
        self.service = service
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(
            f"systemctl {action} {service} exited {returncode}: {stderr.strip()}"
        )


class WgApplyError(WgClientError):
    """Applying a rendered config failed after the unit restart attempt.

    ``WgClientManager.apply`` restores the backup and restarts the unit
    before raising this, so the tunnel is back on its previous config when
    the caller sees the error.
    """

    def __init__(self, service: str, returncode: int, stderr: str) -> None:
        self.service = service
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(
            f"restart {service} exited {returncode}: {stderr.strip()}"
        )


@dataclass(frozen=True, slots=True)
class WgClientConfig:
    """Desired state of the site-to-site client tunnel config file.

    ``private_key`` and ``dns`` are optional: a partial model must render to
    a parseable file (key commented out, DNS omitted) instead of crashing.
    """

    address: str
    endpoint: str
    peer_public_key: str
    allowed_ips: str
    private_key: str | None = None
    dns: str | None = None
    persistent_keepalive: int = 25


def render_config(model: WgClientConfig) -> str:
    """Render the wg-quick config text for ``model``.

    Comment text mirrors the live ``/etc/wireguard/client.conf`` so a render
    from the current model diff-drifts only in whitespace/comments. Raises
    :class:`WgConfigValidationError` when any value would inject into the
    config (newline/CR/`=`), parse as a bad CIDR/address/endpoint, or is not
    a well-formed WireGuard key.
    """
    validate_config(model)
    lines: list[str] = []
    lines.append("[Interface]")
    if model.private_key:
        lines.append(f"PrivateKey = {model.private_key}")
    else:
        lines.append("#PrivateKey = (not provided - supply on next apply)")
    lines.append(f"Address = {model.address}  # Must match AllowedIPs on the server")
    if model.dns:
        lines.append(f"DNS = {model.dns}  # Optional: Set DNS servers")
    lines.append("")
    lines.append("[Peer]")
    lines.append(f"PublicKey = {model.peer_public_key}")
    lines.append(f"Endpoint = {model.endpoint}")
    lines.append(
        f"AllowedIPs = {model.allowed_ips}"
        "  # Route all traffic through VPN (or use 10.0.0.0/24 for VPN-only)"
    )
    lines.append(f"PersistentKeepalive = {model.persistent_keepalive}")
    return "\n".join(lines) + "\n"


@dataclass(frozen=True, slots=True)
class WgStatus:
    """Live tunnel status parsed from ``wg show`` + ``ip -j addr show``."""

    up: bool
    interface: str = "client"
    address: str | None = None
    endpoint: str | None = None
    latest_handshake_sec: int | None = None
    transfer_rx: int | None = None
    transfer_tx: int | None = None
    allowed_ips: str | None = None


def _parse_size(value: str, unit: str) -> int | None:
    """Convert ``("15.21", "GiB")`` to bytes; None when unparseable."""
    multiplier = _SIZE_UNITS.get(unit)
    if multiplier is None:
        return None
    try:
        return int(float(value) * multiplier)
    except ValueError:
        return None


def _parse_handshake_sec(output: str) -> int | None:
    """Parse ``latest handshake`` age into seconds.

    wg-quick's ``wg show`` renders the age as ``N/A``, ``58 seconds ago`` or
    compound ``1 minute, 15 seconds ago`` / ``2 hours, 3 minutes ago`` — the
    single-unit regex therefore must not be trusted.
    """
    match = _HANDSHAKE_LINE_RE.search(output)
    if not match:
        return None
    phrase = match.group(1)
    if phrase == "N/A" or not _HANDSHAKE_TOKEN_RE.search(phrase):
        return None
    total = 0
    for value, unit in _HANDSHAKE_TOKEN_RE.findall(phrase):
        total += int(value) * _HANDSHAKE_SECONDS[unit]
    return total


def _parse_wg_show(output: str) -> tuple[int | None, int | None, int | None, str | None, str | None]:
    """Return (handshake_sec, transfer_rx, transfer_tx, endpoint, allowed_ips)."""
    handshake = _parse_handshake_sec(output)

    transfer: re.Match[str] | None = _TRANSFER_RE.search(output)
    rx: int | None = None
    tx: int | None = None
    if transfer:
        rx = _parse_size(transfer.group(1), transfer.group(2))
        tx = _parse_size(transfer.group(3), transfer.group(4))

    endpoint: str | None = None
    match = _ENDPOINT_RE.search(output)
    if match:
        endpoint = match.group(1)

    allowed_ips: str | None = None
    match = _ALLOWED_IPS_RE.search(output)
    if match:
        allowed_ips = match.group(1)

    return handshake, rx, tx, endpoint, allowed_ips


class WgClientManager:
    """Renders/writes the client config and steers the wg-quick unit."""

    def __init__(
        self,
        interface: str = "client",
        wg_service: str = "wg-quick@client",
        config_path: Path = DEFAULT_CONFIG_PATH,
        state_dir: Path = Path("/var/lib/viswall-vpn"),
    ) -> None:
        self.interface = interface
        self.wg_service = wg_service
        self.config_path = config_path
        self.state_dir = state_dir

    @property
    def backup_path(self) -> Path:
        return self.config_path.with_name(self.config_path.name + BACKUP_SUFFIX)

    # -- unit steering (the ONLY mutating systemctl surface) -----------------

    def _systemctl(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run systemctl on the host via nsenter; NEVER executed in tests."""
        return subprocess.run(
            ["nsenter", "-t", "1", "-m", "-u", "-i", "-n", "--", "systemctl", *args],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    def start(self) -> None:
        """start = enable + start (state-sync rule)."""
        self._systemctl("enable", self.wg_service)
        result = self._systemctl("start", self.wg_service)
        if result.returncode != 0:
            raise WgUnitError("start", self.wg_service, result.returncode, result.stderr)

    def stop(self) -> None:
        """stop = disable + stop (state-sync rule)."""
        self._systemctl("disable", self.wg_service)
        result = self._systemctl("stop", self.wg_service)
        if result.returncode != 0:
            raise WgUnitError("stop", self.wg_service, result.returncode, result.stderr)

    # -- config file ----------------------------------------------------------

    def write_config(self, model: WgClientConfig) -> Path:
        """Backup the current config, then atomically write the rendered one.

        tmp file + ``os.replace`` (atomic on the same filesystem), mode 0600,
        and a ``client.conf.viswall-backup`` copy taken BEFORE every write.
        """
        if self.config_path.exists():
            shutil.copy2(self.config_path, self.backup_path)
        rendered = render_config(model)
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{self.config_path.name}.", suffix=".tmp", dir=self.config_path.parent
        )
        try:
            with os.fdopen(fd, "w") as handle:
                handle.write(rendered)
            os.chmod(tmp_name, 0o600)
            os.replace(tmp_name, self.config_path)
        except BaseException:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        return self.config_path

    def restore_backup(self) -> bool:
        """Restore the ``.viswall-backup`` copy over the config (mode 0600)."""
        if not self.backup_path.exists():
            return False
        shutil.copy2(self.backup_path, self.config_path)
        os.chmod(self.config_path, 0o600)
        return True

    def apply(self, model: WgClientConfig) -> None:
        """write + ``systemctl restart``; on failure restore backup AND restart.

        A failed unit stays failed until restarted, so the rollback path
        restarts the unit with the restored config before raising.
        """
        self.write_config(model)
        result = self._systemctl("restart", self.wg_service)
        if result.returncode != 0:
            self.restore_backup()
            self._systemctl("restart", self.wg_service)
            raise WgApplyError(self.wg_service, result.returncode, result.stderr)

    # -- takeover gate ----------------------------------------------------------

    def takeover_enabled(self) -> bool:
        """Startup reconcile is gated behind ``$STATE_DIR/takeover``."""
        return (self.state_dir / "takeover").exists()

    # -- status (read-only) ------------------------------------------------------

    def status(self) -> WgStatus:
        """Live status from ``ip -j addr show`` + ``wg show`` (read-only).

        Interface-absent is tolerated and reported as ``up=False`` instead of
        raising — the agent must answer status even before the tunnel exists.
        """
        ip_result = subprocess.run(
            ["ip", "-j", "addr", "show", self.interface],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if ip_result.returncode != 0 or not ip_result.stdout.strip():
            return WgStatus(up=False, interface=self.interface)

        address: str | None = None
        try:
            for iface in json.loads(ip_result.stdout):
                for info in iface.get("addr_info", []):
                    if info.get("family") == "inet":
                        address = f"{info['local']}/{info['prefixlen']}"
                        break
        except (json.JSONDecodeError, KeyError, TypeError):
            address = None

        wg_result = subprocess.run(
            ["wg", "show", self.interface],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        handshake, rx, tx, endpoint, allowed_ips = _parse_wg_show(wg_result.stdout)
        return WgStatus(
            up=True,
            interface=self.interface,
            address=address,
            endpoint=endpoint,
            latest_handshake_sec=handshake,
            transfer_rx=rx,
            transfer_tx=tx,
            allowed_ips=allowed_ips,
        )
