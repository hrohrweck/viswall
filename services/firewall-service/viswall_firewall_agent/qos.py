"""Traffic shaping (tc) management for the Viswall firewall agent.

Ported from the former single-file agent
(``services/firewall-service/firewall_agent.py``, ``TrafficControlManager``) —
moved, not improved. QoS ``classes`` delivery and the stats shape fix are
todo 11.
"""

import asyncio
import re
from typing import Any, Dict, List, Tuple


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
    ) -> bool:
        """Setup QoS on an interface"""
        try:
            # Clear existing qdisc
            await self._run_tc(["qdisc", "del", "dev", interface, "root"])

            if algorithm == "cake":
                # Common Applications Kept Enhanced (best for home/SMB)
                # Download (ingress)
                await self._run_tc(
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
                    ]
                )

            elif algorithm == "fq_codel":
                # Fair Queueing Controlled Delay (lower overhead)
                await self._run_tc(
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
                    ]
                )

            elif algorithm == "htb":
                # Hierarchical Token Bucket (for complex shaping)
                await self._setup_htb(interface, download_rate)

            return True

        except Exception as e:
            print(f"QoS setup failed: {e}")
            return False

    async def _setup_htb(self, interface: str, rate: int) -> None:
        """Setup HTB for complex traffic classes"""
        # Root qdisc
        await self._run_tc(
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
                "12",
            ]
        )

        # Root class
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
                f"{rate}kbit",
                "burst",
                "15k",
            ]
        )

        # Priority classes
        classes = [
            ("1:10", int(rate * 0.3), "100"),  # High priority: 30% - VoIP, SSH, DNS
            ("1:11", int(rate * 0.4), "200"),  # Normal: 40% - General traffic
            ("1:12", int(rate * 0.3), "300"),  # Low: 30% - Bulk downloads
        ]

        for classid, class_rate, prio in classes:
            await self._run_tc(
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
                ]
            )

            # Add fq_codel to each class
            await self._run_tc(
                ["qdisc", "add", "dev", interface, "parent", classid, "fq_codel"]
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

    async def _add_filter(
        self, interface: str, classid: str, protocol: str, port: str
    ) -> None:
        """Add traffic filter (IPv4)"""
        await self._run_tc(
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
            ]
        )

    async def _add_filter_ipv6(
        self, interface: str, classid: str, protocol: str, port: str
    ) -> None:
        """Add traffic filter (IPv6) using flower classifier"""
        await self._run_tc(
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
            ]
        )

    async def _run_tc(self, args: List[str]) -> Tuple[int, str, str]:
        """Run tc command"""
        proc = await asyncio.create_subprocess_exec(
            "tc", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout.decode(), stderr.decode()

    async def get_stats(self, interface: str) -> Dict[str, Any]:
        """Get traffic control statistics"""
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

            # Parse tc output
            stats = {}
            current_qdisc = None

            for line in stdout.decode().split("\n"):
                if "qdisc" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        current_qdisc = parts[1]
                        stats[current_qdisc] = {"sent": 0, "dropped": 0}
                elif current_qdisc and "Sent" in line:
                    match = re.search(r"Sent (\d+) bytes (\d+) pkt", line)
                    if match:
                        stats[current_qdisc]["sent_bytes"] = int(match.group(1))
                        stats[current_qdisc]["sent_pkts"] = int(match.group(2))
                elif current_qdisc and "dropped" in line:
                    match = re.search(r"dropped (\d+)", line)
                    if match:
                        stats[current_qdisc]["dropped"] = int(match.group(1))

            return stats
        except:
            return {}

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
        except:
            return False
