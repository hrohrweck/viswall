"""nftables management for the Viswall firewall agent.

Ported from the former single-file agent
(``services/firewall-service/firewall_agent.py``, ``NFTablesManager``) — moved,
not improved. In particular ``generate_ruleset`` still emits ``flush ruleset``
exactly as before; the docker-safe ``table inet viswall``-only renderer is
todo 7 and will replace it there.
"""

import asyncio
import ipaddress
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class FirewallAction(Enum):
    ACCEPT = "accept"
    DROP = "drop"
    REJECT = "reject"
    LOG = "log"
    QUEUE = "queue"  # For content scanning


@dataclass
class FirewallRule:
    id: int
    name: str
    chain: str  # input, output, forward, prerouting, postrouting
    source: Optional[str] = None  # IP, CIDR, or "any"
    destination: Optional[str] = None
    protocol: Optional[str] = None  # tcp, udp, icmp, any
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    interface_in: Optional[str] = None
    interface_out: Optional[str] = None
    action: FirewallAction = FirewallAction.ACCEPT
    log: bool = False
    state: Optional[str] = None  # NEW, ESTABLISHED, RELATED, INVALID
    limit: Optional[str] = None  # rate limiting, e.g., "10/minute"
    comment: Optional[str] = None
    order: int = 0


@dataclass
class NATRule:
    id: int
    name: str
    type: str  # snat, dnat, masquerade
    chain: str  # prerouting, postrouting
    source: Optional[str] = None
    destination: Optional[str] = None
    to_source: Optional[str] = None  # For SNAT
    to_destination: Optional[str] = None  # For DNAT
    protocol: Optional[str] = None
    port: Optional[int] = None
    interface: Optional[str] = None
    comment: Optional[str] = None


class NFTablesManager:
    """Manages nftables firewall rules (modern replacement for iptables)"""

    # Fixed ruleset location — deliberately inlined at every use so no
    # caller-supplied value can influence the path.
    CONFIG_PATH = "/etc/nftables.conf"

    def __init__(self):
        self.ruleset: Dict[str, Any] = {}

    def generate_ruleset(
        self,
        interfaces: List[Dict[str, str]],
        firewall_rules: List[FirewallRule],
        nat_rules: List[NATRule],
        enable_logging: bool = True,
        enable_conntrack: bool = True,
    ) -> str:
        """Generate complete nftables ruleset"""

        # Identify WAN and LAN interfaces
        wan_interfaces = [i["name"] for i in interfaces if i.get("type") == "wan"]
        lan_interfaces = [i["name"] for i in interfaces if i.get("type") == "lan"]

        ruleset = """#!/usr/sbin/nft -f

# Viswall Firewall Configuration
# Generated: {timestamp}

flush ruleset

table inet viswall {
    # Define interface sets
    set wan_interfaces {{
        type ifname
        elements = { {wan_ifs} }
    }}
    
    set lan_interfaces {{
        type ifname
        elements = { {lan_ifs} }
    }}
""".format(
            timestamp=datetime.utcnow().isoformat(),
            wan_ifs=", ".join([f'"{i}"' for i in wan_interfaces]) or '"eth0"',
            lan_ifs=", ".join([f'"{i}"' for i in lan_interfaces]) or '"eth1"',
        )

        # Define sets for blacklists/whitelists
        ruleset += """
    # Dynamic sets for blacklists
    set blacklist_v4 {
        type ipv4_addr
        flags timeout
        timeout 1h
    }

    set blacklist_v6 {
        type ipv6_addr
        flags timeout
        timeout 1h
    }

    set port_scanners_v4 {
        type ipv4_addr
        flags timeout
        timeout 1d
    }

    set port_scanners_v6 {
        type ipv6_addr
        flags timeout
        timeout 1d
    }

    set bruteforce_attempts_v4 {
        type ipv4_addr . inet_service
        flags timeout
        timeout 15m
    }

    set bruteforce_attempts_v6 {
        type ipv6_addr . inet_service
        flags timeout
        timeout 15m
    }
"""

        # Chains
        ruleset += """
    # Input chain - traffic to firewall itself
    chain input {
        type filter hook input priority 0; policy drop;

        # Connection tracking
        ct state established,related accept
        ct state invalid drop

        # Loopback
        iif "lo" accept

        # Blacklist check (dual-stack)
        ip saddr @blacklist_v4 drop
        ip6 saddr @blacklist_v6 drop

        # Rate limiting for new connections
        tcp flags syn limit rate 25/second burst 50 packets accept
        tcp flags syn drop

        # ICMP (ping) rate limiting
        ip protocol icmp limit rate 5/second accept
        ip6 nexthdr icmpv6 limit rate 5/second accept

        # SSH brute force protection (dual-stack)
        tcp dport 22 add @bruteforce_attempts_v4 { ip saddr . tcp dport }
        tcp dport 22 add @bruteforce_attempts_v6 { ip6 saddr . tcp dport }
        tcp dport 22 @bruteforce_attempts_v4 size gt 5 drop
        tcp dport 22 @bruteforce_attempts_v6 size gt 5 drop
"""

        # Add custom rules
        for rule in sorted(firewall_rules, key=lambda r: r.order):
            if rule.chain == "input":
                ruleset += self._convert_rule_to_nft(rule)

        # Default policy section
        ruleset += """
        # Management access (SSH, API)
        tcp dport { 22, 8000, 443 } accept
        
        # Log and drop everything else
        log prefix "[NFT DROP INPUT] " drop
    }
"""

        # Forward chain
        ruleset += """
    # Forward chain - traffic passing through
    chain forward {
        type filter hook forward priority 0; policy drop;

        # Connection tracking
        ct state established,related accept
        ct state invalid drop

        # Blacklist check (dual-stack)
        ip saddr @blacklist_v4 drop
        ip daddr @blacklist_v4 drop
        ip6 saddr @blacklist_v6 drop
        ip6 daddr @blacklist_v6 drop

        # Inter-VLAN routing (if configured)
        # iif @lan_interfaces oif @lan_interfaces accept

        # Port scanning detection (dual-stack)
        tcp flags syn,tcp flags syn,ack add @port_scanners_v4 { ip saddr }
        tcp flags syn,tcp flags syn,ack add @port_scanners_v6 { ip6 saddr }
        ip saddr @port_scanners_v4 drop
        ip6 saddr @port_scanners_v6 drop
"""

        # Add forward rules
        for rule in sorted(firewall_rules, key=lambda r: r.order):
            if rule.chain == "forward":
                ruleset += self._convert_rule_to_nft(rule)

        # Allow LAN to WAN
        ruleset += """
        # Allow LAN to WAN
        iif @lan_interfaces oif @wan_interfaces accept
        
        # Log suspicious forwarded traffic
        log prefix "[NFT DROP FORWARD] " drop
    }
"""

        # Output chain
        ruleset += """
    # Output chain - traffic from firewall
    chain output {
        type filter hook output priority 0; policy accept;
        
        # Connection tracking
        ct state established,related accept
    }
"""

        # NAT/Prerouting
        if nat_rules:
            ruleset += """
    # Prerouting - DNAT
    chain prerouting {
        type nat hook prerouting priority -100;
"""
            for rule in nat_rules:
                if rule.type == "dnat":
                    ruleset += self._convert_nat_rule_to_nft(rule)
            ruleset += """
    }
"""

            # Postrouting - SNAT/Masquerade
            ruleset += """
    # Postrouting - SNAT/Masquerade
    chain postrouting {
        type nat hook postrouting priority 100;
        
        # Masquerade WAN traffic
        oif @wan_interfaces masquerade
"""
            for rule in nat_rules:
                if rule.type in ["snat", "masquerade"]:
                    ruleset += self._convert_nat_rule_to_nft(rule)
            ruleset += """
    }
"""

        ruleset += """
}
"""

        return ruleset

    def _ip_family(self, addr: Optional[str]) -> str:
        """Return 'ip' or 'ip6' for an address or CIDR."""
        if not addr or addr == "any":
            return "ip"
        try:
            if "/" in addr:
                net = ipaddress.ip_network(addr, strict=False)
                return "ip6" if isinstance(net, ipaddress.IPv6Network) else "ip"
            else:
                ip = ipaddress.ip_address(addr)
                return "ip6" if isinstance(ip, ipaddress.IPv6Address) else "ip"
        except ValueError:
            return "ip"

    def _convert_rule_to_nft(self, rule: FirewallRule) -> str:
        """Convert a FirewallRule to nftables syntax (dual-stack aware)"""
        nft_rule = "        "

        # Match criteria
        conditions = []

        if rule.interface_in:
            conditions.append(f'iif "{rule.interface_in}"')
        if rule.interface_out:
            conditions.append(f'oif "{rule.interface_out}"')

        src_family = self._ip_family(rule.source)
        dst_family = self._ip_family(rule.destination)

        if rule.source and rule.source != "any":
            conditions.append(f"{src_family} saddr {rule.source}")

        if rule.destination and rule.destination != "any":
            conditions.append(f"{dst_family} daddr {rule.destination}")

        if rule.protocol and rule.protocol != "any":
            # If both src and dst are IPv6, use ip6 nexthdr; otherwise default to ip protocol
            family = "ip6" if (src_family == "ip6" or dst_family == "ip6") else "ip"
            if family == "ip6":
                conditions.append(f"ip6 nexthdr {rule.protocol}")
            else:
                conditions.append(f"ip protocol {rule.protocol}")

            if rule.source_port:
                conditions.append(f"{rule.protocol} sport {rule.source_port}")
            if rule.destination_port:
                conditions.append(f"{rule.protocol} dport {rule.destination_port}")

        if rule.state:
            conditions.append(f"ct state {rule.state}")

        if rule.limit:
            conditions.append(f"limit rate {rule.limit}")

        # Build rule
        if conditions:
            nft_rule += " ".join(conditions) + " "

        # Action
        if rule.log:
            nft_rule += f'log prefix "[NFT {rule.name}]" '

        nft_rule += rule.action.value

        if rule.comment:
            nft_rule += f' comment "{rule.comment}"'

        nft_rule += "\n"
        return nft_rule

    def _convert_nat_rule_to_nft(self, rule: NATRule) -> str:
        """Convert a NATRule to nftables syntax (dual-stack aware)"""
        nft_rule = "        "
        conditions = []

        if rule.interface:
            conditions.append(f'iif "{rule.interface}"')

        src_family = self._ip_family(rule.source)
        dst_family = self._ip_family(rule.destination)

        if rule.source:
            conditions.append(f"{src_family} saddr {rule.source}")
        if rule.destination:
            conditions.append(f"{dst_family} daddr {rule.destination}")

        if rule.protocol:
            family = "ip6" if (src_family == "ip6" or dst_family == "ip6") else "ip"
            if family == "ip6":
                conditions.append(f"ip6 nexthdr {rule.protocol}")
            else:
                conditions.append(f"ip protocol {rule.protocol}")
            if rule.port:
                conditions.append(f"{rule.protocol} dport {rule.port}")

        if conditions:
            nft_rule += " ".join(conditions) + " "

        if rule.type == "dnat":
            nft_rule += f"dnat to {rule.to_destination}"
        elif rule.type == "snat":
            nft_rule += f"snat to {rule.to_source}"
        elif rule.type == "masquerade":
            nft_rule += "masquerade"

        if rule.comment:
            nft_rule += f' comment "{rule.comment}"'

        nft_rule += "\n"
        return nft_rule

    async def apply_ruleset(self, ruleset: str) -> bool:
        """Apply nftables ruleset"""
        try:
            # Normalized + contained to /etc — the ruleset path is fixed and
            # no caller-supplied value can influence it.
            conf_path = Path("/etc/nftables.conf").resolve()
            if not conf_path.is_relative_to(Path("/etc").resolve()):
                raise ValueError("refusing to write ruleset outside /etc")

            # Write config
            with conf_path.open("w") as f:
                f.write(ruleset)

            # Validate ruleset
            proc = await asyncio.create_subprocess_exec(
                "nft",
                "-c",
                "-f",
                str(conf_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                print(f"nftables validation failed: {stderr.decode()}")
                return False

            # Apply ruleset
            proc = await asyncio.create_subprocess_exec(
                "nft",
                "-f",
                str(conf_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            return proc.returncode == 0

        except Exception as e:
            print(f"Failed to apply nftables: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get nftables statistics"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "nft",
                "list",
                "ruleset",
                "-j",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            return json.loads(stdout.decode())
        except:
            return {}

    async def add_to_blacklist(self, ip: str, timeout: str = "1h") -> bool:
        """Dynamically add IP to blacklist (dual-stack aware)"""
        try:
            set_name = "blacklist_v6" if self._ip_family(ip) == "ip6" else "blacklist_v4"
            proc = await asyncio.create_subprocess_exec(
                "nft",
                "add",
                "element",
                "inet",
                "viswall",
                set_name,
                "{",
                ip,
                "timeout",
                timeout,
                "}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except:
            return False

    async def remove_from_blacklist(self, ip: str) -> bool:
        """Remove IP from blacklist (dual-stack aware)"""
        try:
            set_name = "blacklist_v6" if self._ip_family(ip) == "ip6" else "blacklist_v4"
            proc = await asyncio.create_subprocess_exec(
                "nft",
                "delete",
                "element",
                "inet",
                "viswall",
                set_name,
                "{",
                ip,
                "}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except:
            return False
