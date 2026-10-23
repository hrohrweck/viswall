"""Traffic shaping (tc) management for the Viswall firewall agent.

Ported from the former single-file agent
(``services/firewall-service/firewall_agent.py``, ``TrafficControlManager``).

Todo 11 changes:

* ``setup_qos`` consumes the QoS ``classes`` list sent by the gateway. With
  ``algorithm="htb"`` and a non-empty list, the classes drive the hierarchy:
  class N becomes ``1:{10+N}`` with ``rate=min_rate_kbps``,
  ``ceil=max_rate_kbps`` and ``prio=priority``, an ``fq_codel`` leaf and one
  u32/flower filter per ``match_ports`` entry (tcp+udp for ``match_protocol
  == "any"``). Without classes the historical 30/40/30 default hierarchy is
  applied unchanged.
* Class payloads are validated *before* the first tc invocation, so a
  malformed payload raises :class:`QoSValidationError` and leaves the live
  qdisc untouched (the API maps it to 422).
* ``get_stats`` returns the contract shape
  ``{"queues": [{name, bytes, packets, dropped, rate}], "raw": "<tc -s>"}``
  instead of a qdisc-keyed dict, matching the gateway's QoSStatsResponse
  mapping.
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

#: First minor id used for HTB leaf classes (1:10, 1:11, ...).
HTB_CLASS_BASE_ID = 10

#: Protocols accepted in ``match_protocol``; "any" expands to tcp + udp.
_SUPPORTED_PROTOCOLS = {"any", "tcp", "udp"}

_SENT_RE = re.compile(r"Sent (\d+) bytes (\d+) pkt")
_DROPPED_RE = re.compile(r"\(dropped (\d+)")
_BANDWIDTH_RE = re.compile(r"\b(?:bandwidth|rate)\s+([0-9.]+[a-zA-Z/]*)")
_QDISC_LINE_RE = re.compile(r"^qdisc\s+(\S+)\s+(\S+)")


class QoSValidationError(ValueError):
    """Raised when a QoS class payload cannot be applied as-is."""


class QoSApplyError(RuntimeError):
    """A tc command in the apply pipeline failed (carries the step name)."""


def _number(value: Any, label: str, index: int, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise QoSValidationError(f"class {index}: {label} must be a number")
    if isinstance(value, float) and not value.is_integer():
        raise QoSValidationError(f"class {index}: {label} must be an integer")
    number = int(value)
    if number < minimum:
        raise QoSValidationError(
            f"class {index}: {label} must be >= {minimum} (got {number})"
        )
    return number


def _optional_number(
    value: Any, label: str, index: int, minimum: int = 1
) -> Optional[int]:
    if value is None:
        return None
    return _number(value, label, index, minimum)


def _normalize_classes(classes: Any) -> List[Dict[str, Any]]:
    """Validate a gateway class list and return a normalized copy.

    Raises :class:`QoSValidationError` on any malformed entry. Called before
    the qdisc is deleted so an invalid payload cannot partially apply.
    """
    if not isinstance(classes, (list, tuple)):
        raise QoSValidationError("classes must be a list")

    normalized: List[Dict[str, Any]] = []
    for index, entry in enumerate(classes):
        if not isinstance(entry, dict):
            raise QoSValidationError(f"class {index} must be an object")

        min_rate = entry.get("min_rate_kbps", entry.get("min_rate"))
        if min_rate is None:
            raise QoSValidationError(f"class {index}: min_rate_kbps is required")
        max_rate = entry.get("max_rate_kbps", entry.get("max_rate"))

        ports = entry.get("match_ports") or []
        if not isinstance(ports, (list, tuple)):
            raise QoSValidationError(f"class {index}: match_ports must be a list")
        clean_ports: List[int] = []
        for port in ports:
            clean_ports.append(_number(port, "match_ports entry", index))
            if clean_ports[-1] > 65535:
                raise QoSValidationError(
                    f"class {index}: match_ports entry {clean_ports[-1]} "
                    "exceeds 65535"
                )

        protocol = entry.get("match_protocol") or "any"
        if not isinstance(protocol, str):
            raise QoSValidationError(f"class {index}: match_protocol must be a string")
        protocol = protocol.lower()
        if protocol not in _SUPPORTED_PROTOCOLS:
            raise QoSValidationError(
                f"class {index}: unsupported match_protocol {protocol!r} "
                f"(expected one of {sorted(_SUPPORTED_PROTOCOLS)})"
            )

        priority = entry.get("priority", index + 1)
        if isinstance(priority, bool) or not isinstance(priority, int):
            raise QoSValidationError(f"class {index}: priority must be an integer")
        if not 0 <= priority <= 7:
            raise QoSValidationError(
                f"class {index}: priority must be between 0 and 7"
            )

        normalized.append(
            {
                "name": str(entry.get("name") or f"class-{index}"),
                "priority": priority,
                "min_rate_kbps": _number(min_rate, "min_rate_kbps", index),
                "max_rate_kbps": _optional_number(max_rate, "max_rate_kbps", index),
                "match_ports": clean_ports,
                "match_protocol": protocol,
            }
        )

    return normalized


def _parse_qdisc_stats(output: str) -> List[Dict[str, Any]]:
    """Parse ``tc -s qdisc show`` text into the gateway queue shape."""
    queues: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None

    for raw_line in output.splitlines():
        line = raw_line.strip()
        qdisc_match = _QDISC_LINE_RE.match(line)
        if qdisc_match:
            kind, handle = qdisc_match.group(1), qdisc_match.group(2)
            bandwidth = _BANDWIDTH_RE.search(line)
            current = {
                "name": handle if handle not in ("", "0:") else kind,
                "bytes": 0,
                "packets": 0,
                "dropped": 0,
                "rate": bandwidth.group(1) if bandwidth else "",
            }
            queues.append(current)
            continue

        if current is None:
            continue

        sent = _SENT_RE.search(line)
        if sent:
            current["bytes"] = int(sent.group(1))
            current["packets"] = int(sent.group(2))

        dropped = _DROPPED_RE.search(line)
        if dropped:
            current["dropped"] = int(dropped.group(1))

    return queues


class TrafficControlManager:
    """Manages traffic shaping using tc (Traffic Control)"""

    def __init__(self):
        self.interfaces: List[str] = []

    async def setup_qos(
        self,
        interface: str,
        download_rate: int,  # kbps
        upload_rate: int,  # kbps
        algorithm: str = "cake",  # cake, fq_codel, htb
        classes: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> bool:
        """Setup QoS on an interface.

        ``classes`` is the gateway-serialized QoSClass list. It only affects
        ``algorithm="htb"``; other algorithms ignore it. Validation happens
        before any tc command runs.

        F2 MINOR #10: every qdisc/class/filter ADD is returncode-checked — a
        failed step raises :class:`QoSApplyError` and this method returns
        False instead of silently reporting success on a half-installed tree.

        Rate semantics: the root qdisc shapes EGRESS only. For cake/fq_codel
        the ``download_rate`` is applied as the qdisc ``bandwidth`` (egress
        direction) and ``upload_rate`` is UNUSED — true ingress shaping needs
        an IFB/mirred redirect, which is out of scope; treat ``upload_rate``
        as egress-only metadata for these algorithms.
        """
        # Validate first: a malformed class list must not touch the qdisc.
        normalized_classes = _normalize_classes(classes) if classes else []

        try:
            # Clear existing qdisc (tolerated: a fresh interface has none).
            await self._run_tc(["qdisc", "del", "dev", interface, "root"])

            if algorithm == "cake":
                # Common Applications Kept Enhanced (best for home/SMB)
                await self._tc_checked(
                    [
                        "qdisc",
                        "add",
                        "dev",
                        interface,
                        "root",
                        "handle",
                        "1:",
                        "cake",
                        "bandwidth",
                        f"{download_rate}kbit",
                        "diffserv4",
                        "dual-srchost",
                        "nat",
                        "wash",
                    ],
                    "cake qdisc add",
                )

            elif algorithm == "fq_codel":
                # Fair Queueing Controlled Delay (lower overhead)
                await self._tc_checked(
                    [
                        "qdisc",
                        "add",
                        "dev",
                        interface,
                        "root",
                        "handle",
                        "1:",
                        "fq_codel",
                        "flows",
                        "1024",
                        "quantum",
                        "1514",
                    ],
                    "fq_codel qdisc add",
                )

            elif algorithm == "htb":
                # Hierarchical Token Bucket (for complex shaping)
                await self._setup_htb(interface, download_rate, normalized_classes)

            return True

        except (QoSApplyError, OSError) as exc:
            logger.error("QoS setup failed on %s: %s", interface, exc)
            return False

    async def _setup_htb(
        self,
        interface: str,
        rate: int,
        classes: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> None:
        """Setup HTB for complex traffic classes.

        When ``classes`` is non-empty it defines the leaf hierarchy; otherwise
        the legacy 30/40/30 default hierarchy with VoIP/DNS/SSH filters is
        installed.
        """
        classes = list(classes or [])

        if classes:
            default_minor = str(HTB_CLASS_BASE_ID + len(classes) - 1)
        else:
            default_minor = "12"

        # Root qdisc
        await self._tc_checked(
            [
                "qdisc",
                "add",
                "dev",
                interface,
                "root",
                "handle",
                "1:",
                "htb",
                "default",
                default_minor,
            ],
            "htb root qdisc add",
        )

        # Root class
        await self._tc_checked(
            [
                "class",
                "add",
                "dev",
                interface,
                "parent",
                "1:",
                "classid",
                "1:1",
                "htb",
                "rate",
                f"{rate}kbit",
                "burst",
                "15k",
            ],
            "htb root class add",
        )

        if classes:
            await self._add_class_leaves(interface, rate, classes)
            return

        # Legacy default hierarchy: (classid, rate, prio)
        default_classes = [
            ("1:10", int(rate * 0.3), "100"),  # High priority: 30% - VoIP, SSH, DNS
            ("1:11", int(rate * 0.4), "200"),  # Normal: 40% - General traffic
            ("1:12", int(rate * 0.3), "300"),  # Low: 30% - Bulk downloads
        ]

        for classid, class_rate, prio in default_classes:
            await self._tc_checked(
                [
                    "class",
                    "add",
                    "dev",
                    interface,
                    "parent",
                    "1:1",
                    "classid",
                    classid,
                    "htb",
                    "rate",
                    f"{class_rate}kbit",
                    "ceil",
                    f"{rate}kbit",
                    "prio",
                    prio,
                ],
                f"htb class {classid} add",
            )

            # Add fq_codel to each class
            await self._tc_checked(
                ["qdisc", "add", "dev", interface, "parent", classid, "fq_codel"],
                f"fq_codel leaf {classid} add",
            )

        # Filters to classify traffic (dual-stack)
        # VoIP (SIP)
        await self._add_filter(interface, "1:10", "udp", "5060")
        await self._add_filter_ipv6(interface, "1:10", "udp", "5060")
        # DNS
        await self._add_filter(interface, "1:10", "udp", "53")
        await self._add_filter_ipv6(interface, "1:10", "udp", "53")
        # SSH
        await self._add_filter(interface, "1:10", "tcp", "22")
        await self._add_filter_ipv6(interface, "1:10", "tcp", "22")

    async def _add_class_leaves(
        self, interface: str, root_rate: int, classes: Sequence[Dict[str, Any]]
    ) -> None:
        """Install one HTB leaf + fq_codel + filters per gateway class."""
        for index, spec in enumerate(classes):
            classid = f"1:{HTB_CLASS_BASE_ID + index}"
            ceil_rate = spec.get("max_rate_kbps") or root_rate

            await self._tc_checked(
                [
                    "class",
                    "add",
                    "dev",
                    interface,
                    "parent",
                    "1:1",
                    "classid",
                    classid,
                    "htb",
                    "rate",
                    f"{spec['min_rate_kbps']}kbit",
                    "ceil",
                    f"{ceil_rate}kbit",
                    "prio",
                    str(spec["priority"]),
                ],
                f"htb class {classid} add",
            )

            await self._tc_checked(
                ["qdisc", "add", "dev", interface, "parent", classid, "fq_codel"],
                f"fq_codel leaf {classid} add",
            )

            protocols = (
                ("tcp", "udp")
                if spec["match_protocol"] == "any"
                else (spec["match_protocol"],)
            )
            for port in spec["match_ports"]:
                for protocol in protocols:
                    await self._add_filter(interface, classid, protocol, str(port))
                    await self._add_filter_ipv6(
                        interface, classid, protocol, str(port)
                    )

    async def _add_filter(
        self, interface: str, classid: str, protocol: str, port: str
    ) -> None:
        """Add traffic filter (IPv4)"""
        await self._tc_checked(
            [
                "filter",
                "add",
                "dev",
                interface,
                "protocol",
                "ip",
                "parent",
                "1:0",
                "prio",
                "1",
                "u32",
                "match",
                "ip",
                "protocol",
                "6" if protocol == "tcp" else "17",
                "0xff",
                "match",
                protocol,
                "dport",
                port,
                "0xffff",
                "flowid",
                classid,
            ],
            f"filter {protocol}:{port} -> {classid} add",
        )

    async def _add_filter_ipv6(
        self, interface: str, classid: str, protocol: str, port: str
    ) -> None:
        """Add traffic filter (IPv6) using flower classifier"""
        await self._tc_checked(
            [
                "filter",
                "add",
                "dev",
                interface,
                "protocol",
                "ipv6",
                "parent",
                "1:0",
                "prio",
                "1",
                "flower",
                "ip_proto",
                protocol,
                "dst_port",
                port,
                "flowid",
                classid,
            ],
            f"filter6 {protocol}:{port} -> {classid} add",
        )

    async def _run_tc(self, args: List[str]) -> Tuple[int, str, str]:
        """Run tc command"""
        proc = await asyncio.create_subprocess_exec(
            "tc", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout.decode(), stderr.decode()

    async def _tc_checked(self, args: List[str], step: str) -> None:
        """Run a tc ADD step and raise QoSApplyError on any failure."""
        rc, _, stderr = await self._run_tc(args)
        if rc != 0:
            raise QoSApplyError(f"{step} failed ({rc}): {stderr.strip()}")

    async def get_stats(self, interface: str) -> Dict[str, Any]:
        """Get traffic control statistics in the gateway contract shape.

        Returns ``{"queues": [{name, bytes, packets, dropped, rate}], "raw":
        "<tc -s output>"}`` so ``QoSStatsResponse.queues`` can be populated by
        the gateway.
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                "tc",
                "-s",
                "qdisc",
                "show",
                "dev",
                interface,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
        except Exception as e:
            print(f"QoS stats failed: {e}")
            return {"queues": [], "raw": ""}

        raw = stdout.decode(errors="replace")
        return {"queues": _parse_qdisc_stats(raw), "raw": raw}

    async def limit_per_ip(
        self, interface: str, rate: str = "10mbit", burst: str = "100k"
    ) -> bool:
        """Setup per-IP rate limiting"""
        try:
            # Create hash table for per-IP limiting
            await self._run_tc(
                ["qdisc", "add", "dev", interface, "handle", "1:", "root", "htb"]
            )

            await self._run_tc(
                [
                    "class",
                    "add",
                    "dev",
                    interface,
                    "parent",
                    "1:",
                    "classid",
                    "1:1",
                    "htb",
                    "rate",
                    rate,
                ]
            )

            # Add filter that creates classes dynamically per source IP (dual-stack)
            for proto in ("ip", "ipv6"):
                await self._run_tc(
                    [
                        "filter",
                        "add",
                        "dev",
                        interface,
                        "protocol",
                        proto,
                        "parent",
                        "1:0",
                        "prio",
                        "1",
                        "handle",
                        "1:",
                        "fw",
                        "classid",
                        "1:1",
                    ]
                )

            return True
        except Exception:
            return False
