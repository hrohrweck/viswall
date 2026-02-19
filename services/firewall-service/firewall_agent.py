"""
Viswall Firewall Service Agent

Manages Linux firewall, routing, and traffic control:
- nftables (modern iptables replacement)
- Traffic shaping (tc, CAKE, fq_codel)
- Policy-based routing
- Content filtering
- Connection tracking
- Rate limiting and DDoS protection
"""

import asyncio
import subprocess
import json
import re
import ipaddress
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime


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


@dataclass
class RoutingRule:
    id: int
    name: str
    source: Optional[str] = None
    destination: Optional[str] = None
    table: int = 254  # Main routing table
    gateway: Optional[str] = None
    interface: Optional[str] = None
    mark: Optional[int] = None  # fwmark for policy routing
    priority: int = 100


class NFTablesManager:
    """Manages nftables firewall rules (modern replacement for iptables)"""
    
    def __init__(self):
        self.ruleset: Dict[str, Any] = {}
        self.config_path = "/etc/nftables.conf"
    
    def generate_ruleset(
        self,
        interfaces: List[Dict[str, str]],
        firewall_rules: List[FirewallRule],
        nat_rules: List[NATRule],
        enable_logging: bool = True,
        enable_conntrack: bool = True
    ) -> str:
        """Generate complete nftables ruleset"""
        
        # Identify WAN and LAN interfaces
        wan_interfaces = [i["name"] for i in interfaces if i.get("type") == "wan"]
        lan_interfaces = [i["name"] for i in interfaces if i.get("type") == "lan"]
        
        ruleset = '''#!/usr/sbin/nft -f

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
'''.format(
            timestamp=datetime.utcnow().isoformat(),
            wan_ifs=", ".join([f'"{i}"' for i in wan_interfaces]) or '"eth0"',
            lan_ifs=", ".join([f'"{i}"' for i in lan_interfaces]) or '"eth1"'
        )
        
        # Define sets for blacklists/whitelists
        ruleset += '''
    # Dynamic sets for blacklists
    set blacklist_v4 {
        type ipv4_addr
        flags timeout
        timeout 1h
    }
    
    set port_scanners {
        type ipv4_addr
        flags timeout
        timeout 1d
    }
    
    set bruteforce_attempts {
        type ipv4_addr . inet_service
        flags timeout
        timeout 15m
    }
'''
        
        # Chains
        ruleset += '''
    # Input chain - traffic to firewall itself
    chain input {
        type filter hook input priority 0; policy drop;
        
        # Connection tracking
        ct state established,related accept
        ct state invalid drop
        
        # Loopback
        iif "lo" accept
        
        # Blacklist check
        ip saddr @blacklist_v4 drop
        
        # Rate limiting for new connections
        tcp flags syn limit rate 25/second burst 50 packets accept
        tcp flags syn drop
        
        # ICMP (ping) rate limiting
        ip protocol icmp limit rate 5/second accept
        ip6 nexthdr icmpv6 limit rate 5/second accept
        
        # SSH brute force protection
        tcp dport 22 add @bruteforce_attempts { ip saddr . tcp dport }
        tcp dport 22 @bruteforce_attempts size gt 5 drop
'''
        
        # Add custom rules
        for rule in sorted(firewall_rules, key=lambda r: r.order):
            if rule.chain == "input":
                ruleset += self._convert_rule_to_nft(rule)
        
        # Default policy section
        ruleset += '''
        # Management access (SSH, API)
        tcp dport { 22, 8000, 443 } accept
        
        # Log and drop everything else
        log prefix "[NFT DROP INPUT] " drop
    }
'''
        
        # Forward chain
        ruleset += '''
    # Forward chain - traffic passing through
    chain forward {
        type filter hook forward priority 0; policy drop;
        
        # Connection tracking
        ct state established,related accept
        ct state invalid drop
        
        # Blacklist check
        ip saddr @blacklist_v4 drop
        ip daddr @blacklist_v4 drop
        
        # Inter-VLAN routing (if configured)
        # iif @lan_interfaces oif @lan_interfaces accept
        
        # Port scanning detection
        tcp flags syn,tcp flags syn,ack add @port_scanners { ip saddr }
        ip saddr @port_scanners drop
'''
        
        # Add forward rules
        for rule in sorted(firewall_rules, key=lambda r: r.order):
            if rule.chain == "forward":
                ruleset += self._convert_rule_to_nft(rule)
        
        # Allow LAN to WAN
        ruleset += '''
        # Allow LAN to WAN
        iif @lan_interfaces oif @wan_interfaces accept
        
        # Log suspicious forwarded traffic
        log prefix "[NFT DROP FORWARD] " drop
    }
'''
        
        # Output chain
        ruleset += '''
    # Output chain - traffic from firewall
    chain output {
        type filter hook output priority 0; policy accept;
        
        # Connection tracking
        ct state established,related accept
    }
'''
        
        # NAT/Prerouting
        if nat_rules:
            ruleset += '''
    # Prerouting - DNAT
    chain prerouting {
        type nat hook prerouting priority -100;
'''
            for rule in nat_rules:
                if rule.type == "dnat":
                    ruleset += self._convert_nat_rule_to_nft(rule)
            ruleset += '''
    }
'''
            
            # Postrouting - SNAT/Masquerade
            ruleset += '''
    # Postrouting - SNAT/Masquerade
    chain postrouting {
        type nat hook postrouting priority 100;
        
        # Masquerade WAN traffic
        oif @wan_interfaces masquerade
'''
            for rule in nat_rules:
                if rule.type in ["snat", "masquerade"]:
                    ruleset += self._convert_nat_rule_to_nft(rule)
            ruleset += '''
    }
'''
        
        ruleset += '''
}
'''
        
        return ruleset
    
    def _convert_rule_to_nft(self, rule: FirewallRule) -> str:
        """Convert a FirewallRule to nftables syntax"""
        nft_rule = "        "
        
        # Match criteria
        conditions = []
        
        if rule.interface_in:
            conditions.append(f'iif "{rule.interface_in}"')
        if rule.interface_out:
            conditions.append(f'oif "{rule.interface_out}"')
        
        if rule.source and rule.source != "any":
            if "/" in rule.source:  # CIDR
                conditions.append(f'ip saddr {rule.source}')
            else:
                conditions.append(f'ip saddr {rule.source}')
        
        if rule.destination and rule.destination != "any":
            if "/" in rule.destination:
                conditions.append(f'ip daddr {rule.destination}')
            else:
                conditions.append(f'ip daddr {rule.destination}')
        
        if rule.protocol and rule.protocol != "any":
            conditions.append(f'ip protocol {rule.protocol}')
            
            if rule.source_port:
                conditions.append(f'{rule.protocol} sport {rule.source_port}')
            if rule.destination_port:
                conditions.append(f'{rule.protocol} dport {rule.destination_port}')
        
        if rule.state:
            conditions.append(f'ct state {rule.state}')
        
        if rule.limit:
            conditions.append(f'limit rate {rule.limit}')
        
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
        """Convert a NATRule to nftables syntax"""
        nft_rule = "        "
        conditions = []
        
        if rule.interface:
            conditions.append(f'iif "{rule.interface}"')
        
        if rule.source:
            conditions.append(f'ip saddr {rule.source}')
        if rule.destination:
            conditions.append(f'ip daddr {rule.destination}')
        
        if rule.protocol:
            conditions.append(f'ip protocol {rule.protocol}')
            if rule.port:
                conditions.append(f'{rule.protocol} dport {rule.port}')
        
        if conditions:
            nft_rule += " ".join(conditions) + " "
        
        if rule.type == "dnat":
            nft_rule += f'dnat to {rule.to_destination}'
        elif rule.type == "snat":
            nft_rule += f'snat to {rule.to_source}'
        elif rule.type == "masquerade":
            nft_rule += "masquerade"
        
        if rule.comment:
            nft_rule += f' comment "{rule.comment}"'
        
        nft_rule += "\n"
        return nft_rule
    
    async def apply_ruleset(self, ruleset: str) -> bool:
        """Apply nftables ruleset"""
        try:
            # Write config
            with open(self.config_path, 'w') as f:
                f.write(ruleset)
            
            # Validate ruleset
            proc = await asyncio.create_subprocess_exec(
                "nft", "-c", "-f", self.config_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                print(f"nftables validation failed: {stderr.decode()}")
                return False
            
            # Apply ruleset
            proc = await asyncio.create_subprocess_exec(
                "nft", "-f", self.config_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
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
                "nft", "list", "ruleset", "-j",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            return json.loads(stdout.decode())
        except:
            return {}
    
    async def add_to_blacklist(self, ip: str, timeout: str = "1h") -> bool:
        """Dynamically add IP to blacklist"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "nft", "add", "element", "inet", "viswall", "blacklist_v4",
                "{", ip, "timeout", timeout, "}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return proc.returncode == 0
        except:
            return False
    
    async def remove_from_blacklist(self, ip: str) -> bool:
        """Remove IP from blacklist"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "nft", "delete", "element", "inet", "viswall", "blacklist_v4",
                "{", ip, "}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return proc.returncode == 0
        except:
            return False


class TrafficControlManager:
    """Manages traffic shaping using tc (Traffic Control)"""
    
    def __init__(self):
        self.interfaces: List[str] = []
    
    async def setup_qos(
        self,
        interface: str,
        download_rate: int,  # kbps
        upload_rate: int,    # kbps
        algorithm: str = "cake"  # cake, fq_codel, htb
    ) -> bool:
        """Setup QoS on an interface"""
        try:
            # Clear existing qdisc
            await self._run_tc(["qdisc", "del", "dev", interface, "root"])
            
            if algorithm == "cake":
                # Common Applications Kept Enhanced (best for home/SMB)
                # Download (ingress)
                await self._run_tc([
                    "qdisc", "add", "dev", interface, "root", "handle", "1:",
                    "cake", "bandwidth", f"{download_rate}kbit",
                    "diffserv4", "dual-srchost", "nat", "wash"
                ])
                
            elif algorithm == "fq_codel":
                # Fair Queueing Controlled Delay (lower overhead)
                await self._run_tc([
                    "qdisc", "add", "dev", interface, "root", "handle", "1:",
                    "fq_codel", "flows", "1024", "quantum", "1514"
                ])
                
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
        await self._run_tc([
            "qdisc", "add", "dev", interface, "root", "handle", "1:",
            "htb", "default", "12"
        ])
        
        # Root class
        await self._run_tc([
            "class", "add", "dev", interface, "parent", "1:", "classid", "1:1",
            "htb", "rate", f"{rate}kbit", "burst", "15k"
        ])
        
        # Priority classes
        classes = [
            ("1:10", int(rate * 0.3), "100"),   # High priority: 30% - VoIP, SSH, DNS
            ("1:11", int(rate * 0.4), "200"),   # Normal: 40% - General traffic
            ("1:12", int(rate * 0.3), "300"),   # Low: 30% - Bulk downloads
        ]
        
        for classid, class_rate, prio in classes:
            await self._run_tc([
                "class", "add", "dev", interface, "parent", "1:1", "classid", classid,
                "htb", "rate", f"{class_rate}kbit", "ceil", f"{rate}kbit", "prio", prio
            ])
            
            # Add fq_codel to each class
            await self._run_tc([
                "qdisc", "add", "dev", interface, "parent", classid,
                "fq_codel"
            ])
        
        # Filters to classify traffic
        # VoIP (SIP)
        await self._add_filter(interface, "1:10", "udp", "5060")
        # DNS
        await self._add_filter(interface, "1:10", "udp", "53")
        # SSH
        await self._add_filter(interface, "1:10", "tcp", "22")
    
    async def _add_filter(self, interface: str, classid: str, protocol: str, port: str) -> None:
        """Add traffic filter"""
        await self._run_tc([
            "filter", "add", "dev", interface, "protocol", "ip", "parent", "1:0",
            "prio", "1", "u32",
            "match", "ip", "protocol", "6" if protocol == "tcp" else "17", "0xff",
            "match", protocol, "dport", port, "0xffff",
            "flowid", classid
        ])
    
    async def _run_tc(self, args: List[str]) -> Tuple[int, str, str]:
        """Run tc command"""
        proc = await asyncio.create_subprocess_exec(
            "tc", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout.decode(), stderr.decode()
    
    async def get_stats(self, interface: str) -> Dict[str, Any]:
        """Get traffic control statistics"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "tc", "-s", "qdisc", "show", "dev", interface,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            
            # Parse tc output
            stats = {}
            current_qdisc = None
            
            for line in stdout.decode().split('\n'):
                if 'qdisc' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        current_qdisc = parts[1]
                        stats[current_qdisc] = {'sent': 0, 'dropped': 0}
                elif current_qdisc and 'Sent' in line:
                    match = re.search(r'Sent (\d+) bytes (\d+) pkt', line)
                    if match:
                        stats[current_qdisc]['sent_bytes'] = int(match.group(1))
                        stats[current_qdisc]['sent_pkts'] = int(match.group(2))
                elif current_qdisc and 'dropped' in line:
                    match = re.search(r'dropped (\d+)', line)
                    if match:
                        stats[current_qdisc]['dropped'] = int(match.group(1))
            
            return stats
        except:
            return {}
    
    async def limit_per_ip(
        self,
        interface: str,
        rate: str = "10mbit",
        burst: str = "100k"
    ) -> bool:
        """Setup per-IP rate limiting"""
        try:
            # Create hash table for per-IP limiting
            await self._run_tc([
                "qdisc", "add", "dev", interface, "handle", "1:", "root", "htb"
            ])
            
            await self._run_tc([
                "class", "add", "dev", interface, "parent", "1:", "classid", "1:1",
                "htb", "rate", rate
            ])
            
            # Add filter that creates classes dynamically per source IP
            await self._run_tc([
                "filter", "add", "dev", interface, "protocol", "ip", "parent", "1:0",
                "prio", "1", "handle", "1:", "fw", "classid", "1:1"
            ])
            
            return True
        except:
            return False


class RoutingManager:
    """Manages policy-based routing"""
    
    RT_TABLES_PATH = "/etc/iproute2/rt_tables"
    
    async def add_routing_table(self, name: str, number: int) -> bool:
        """Add custom routing table"""
        try:
            # Check if already exists
            with open(self.RT_TABLES_PATH, 'r') as f:
                content = f.read()
                if name in content:
                    return True
            
            # Add table
            with open(self.RT_TABLES_PATH, 'a') as f:
                f.write(f"{number} {name}\n")
            
            return True
        except Exception as e:
            print(f"Failed to add routing table: {e}")
            return False
    
    async def add_route(
        self,
        destination: str,
        gateway: Optional[str] = None,
        interface: Optional[str] = None,
        table: str = "main",
        source: Optional[str] = None,
        metric: Optional[int] = None
    ) -> bool:
        """Add a route"""
        try:
            args = ["ip", "route", "add", destination]
            
            if gateway:
                args.extend(["via", gateway])
            if interface:
                args.extend(["dev", interface])
            if source:
                args.extend(["src", source])
            if metric:
                args.extend(["metric", str(metric)])
            
            args.extend(["table", table])
            
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return proc.returncode == 0
            
        except Exception as e:
            print(f"Failed to add route: {e}")
            return False
    
    async def add_policy_rule(
        self,
        table: int,
        priority: int,
        source: Optional[str] = None,
        destination: Optional[str] = None,
        mark: Optional[int] = None,
        interface: Optional[str] = None
    ) -> bool:
        """Add policy routing rule"""
        try:
            args = ["ip", "rule", "add"]
            
            if source:
                args.extend(["from", source])
            if destination:
                args.extend(["to", destination])
            if mark:
                args.extend(["fwmark", str(mark)])
            if interface:
                args.extend(["iif", interface])
            
            args.extend(["table", str(table), "prio", str(priority)])
            
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return proc.returncode == 0
            
        except Exception as e:
            print(f"Failed to add policy rule: {e}")
            return False
    
    async def setup_load_balancing(
        self,
        gateways: List[Dict[str, str]],
        method: str = "round_robin"  # round_robin, weighted, failover
    ) -> bool:
        """Setup multi-WAN load balancing"""
        try:
            # Create routing tables for each gateway
            for i, gw in enumerate(gateways):
                table_name = f"wan{i+1}"
                await self.add_routing_table(table_name, 100 + i)
                
                # Add default route in each table
                await self.add_route(
                    destination="default",
                    gateway=gw["gateway"],
                    interface=gw["interface"],
                    table=table_name
                )
            
            if method == "round_robin":
                # Add rules for each connection to different tables
                for i, _ in enumerate(gateways):
                    await self.add_policy_rule(
                        table=100 + i,
                        priority=100 + i,
                        mark=i + 1
                    )
            
            elif method == "failover":
                # Primary route with higher priority
                await self.add_policy_rule(
                    table=100,
                    priority=100
                )
                # Backup route
                await self.add_policy_rule(
                    table=101,
                    priority=200
                )
            
            return True
            
        except Exception as e:
            print(f"Load balancing setup failed: {e}")
            return False
    
    async def get_routes(self, table: str = "all") -> List[Dict[str, Any]]:
        """Get routing table"""
        try:
            args = ["ip", "route", "show"]
            if table != "all":
                args.extend(["table", table])
            
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            
            routes = []
            for line in stdout.decode().strip().split('\n'):
                if line and not line.startswith('broadcast'):
                    routes.append({'raw': line})
            
            return routes
        except:
            return []
    
    async def get_rules(self) -> List[Dict[str, Any]]:
        """Get policy routing rules"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ip", "rule", "show",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            
            rules = []
            for line in stdout.decode().strip().split('\n'):
                if line:
                    rules.append({'raw': line})
            
            return rules
        except:
            return []


class ContentFilterManager:
    """Manages content filtering (URL filtering, DPI)"""
    
    def __init__(self):
        self.blocked_categories: set = set()
        self.custom_blocks: set = set()
        self.custom_allows: set = set()
    
    def generate_squid_config(
        self,
        blocked_categories: List[str],
        custom_blocks: List[str],
        custom_allows: List[str],
        enable_ssl_bump: bool = False
    ) -> str:
        """Generate Squid proxy configuration for content filtering"""
        config = f'''# Viswall Squid Configuration
# Generated: {datetime.utcnow().isoformat()}

# Basic settings
http_port 3128
http_port 3129 intercept
https_port 3130 cert=/etc/squid/ssl_cert.pem key=/etc/squid/ssl_key.pem

# Cache settings
cache_mem 256 MB
maximum_object_size 512 MB
cache_dir ufs /var/spool/squid 10000 16 256

# Access logging
access_log daemon:/var/log/squid/access.log squid

# ACL definitions
acl localnet src 10.0.0.0/8
acl localnet src 172.16.0.0/12
acl localnet src 192.168.0.0/16
acl SSL_ports port 443
acl Safe_ports port 80
acl Safe_ports port 443
acl CONNECT method CONNECT

# Content filtering categories
'''
        
        # Add category blocks
        for category in blocked_categories:
            config += f'acl blocked_{category} dstdomain "/etc/squid/blocked_{category}.txt"\n'
        
        # Custom blocks/allows
        if custom_blocks:
            config += 'acl custom_blocked dstdomain "/etc/squid/custom_blocked.txt"\n'
        if custom_allows:
            config += 'acl custom_allowed dstdomain "/etc/squid/custom_allowed.txt"\n'
        
        config += '''
# Access rules
http_access deny !Safe_ports
http_access deny CONNECT !SSL_ports
http_access allow localhost manager
http_access deny manager
'''
        
        # Apply category blocks
        for category in blocked_categories:
            config += f'http_access deny blocked_{category}\n'
        
        if custom_blocks:
            config += 'http_access deny custom_blocked\n'
        if custom_allows:
            config += 'http_access allow custom_allowed\n'
        
        config += '''
http_access allow localnet
http_access allow localhost
http_access deny all

# SSL Bump (HTTPS inspection)
'''
        
        if enable_ssl_bump:
            config += '''
ssl_bump bump all
sslproxy_cert_error allow all
sslproxy_flags DONT_VERIFY_PEER
'''
        
        config += '''
# Refresh patterns
refresh_pattern ^ftp: 1440 20% 10080
refresh_pattern ^gopher: 1440 0% 1440
refresh_pattern -i (/cgi-bin/|\\?) 0 0% 0
refresh_pattern . 0 20% 4320
'''
        
        return config
    
    def generate_category_list(self, category: str) -> List[str]:
        """Generate domain list for a category"""
        # In production, this would fetch from a URL blacklist service
        # like shallalist, ut1-blacklist, or commercial feeds
        categories = {
            "adult": [".xxx", ".porn", ".adult"],
            "gambling": [".bet", ".casino", ".poker"],
            "malware": ["malware.example"],
            "social": ["facebook.com", "twitter.com", "instagram.com"],
        }
        return categories.get(category, [])


class FirewallAgent:
    """Main firewall agent coordinating all components"""
    
    def __init__(self):
        self.nftables = NFTablesManager()
        self.tc = TrafficControlManager()
        self.routing = RoutingManager()
        self.content = ContentFilterManager()
    
    async def deploy_firewall_config(
        self,
        interfaces: List[Dict[str, str]],
        rules: List[Dict[str, Any]],
        nat_rules: List[Dict[str, Any]],
        routing_rules: List[Dict[str, Any]],
        qos_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Deploy complete firewall configuration"""
        
        # Convert dict rules to objects
        fw_rules = [FirewallRule(**r) for r in rules]
        nat = [NATRule(**r) for r in nat_rules]
        
        # Generate and apply nftables
        ruleset = self.nftables.generate_ruleset(
            interfaces=interfaces,
            firewall_rules=fw_rules,
            nat_rules=nat
        )
        
        nft_ok = await self.nftables.apply_ruleset(ruleset)
        
        # Apply QoS if configured
        tc_ok = True
        if qos_config:
            for interface, config in qos_config.items():
                tc_ok = await self.tc.setup_qos(
                    interface=interface,
                    download_rate=config["download"],
                    upload_rate=config["upload"],
                    algorithm=config.get("algorithm", "cake")
                )
                if not tc_ok:
                    break
        
        # Apply routing rules
        routing_ok = True
        for rule in routing_rules:
            routing_ok = await self.routing.add_policy_rule(
                table=rule.get("table", 254),
                priority=rule.get("priority", 100),
                source=rule.get("source"),
                destination=rule.get("destination"),
                mark=rule.get("mark"),
                interface=rule.get("interface")
            )
            if not routing_ok:
                break
        
        return nft_ok and tc_ok and routing_ok
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive firewall statistics"""
        
        # Get nftables stats
        nft_stats = await self.nftables.get_stats()
        
        # Get conntrack info
        conntrack_count = 0
        try:
            proc = await asyncio.create_subprocess_exec(
                "conntrack", "-C",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            conntrack_count = int(stdout.decode().strip())
        except:
            pass
        
        return {
            "nftables": nft_stats,
            "connections": {
                "tracked": conntrack_count,
                "max": 262144  # Default nf_conntrack_max
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def block_ip(self, ip: str, reason: str = "manual") -> bool:
        """Block an IP address"""
        return await self.nftables.add_to_blacklist(ip)
    
    async def unblock_ip(self, ip: str) -> bool:
        """Unblock an IP address"""
        return await self.nftables.remove_from_blacklist(ip)


# Main entry point
async def main():
    """Firewall Agent main loop"""
    
    agent = FirewallAgent()
    
    print("Viswall Firewall Agent started")
    print("Features: nftables, traffic shaping, policy routing, content filtering")
    
    # Example deployment
    # await agent.deploy_firewall_config(
    #     interfaces=[
    #         {"name": "eth0", "type": "wan"},
    #         {"name": "eth1", "type": "lan"}
    #     ],
    #     rules=[
    #         {"id": 1, "name": "Allow HTTP", "chain": "forward", "protocol": "tcp", "destination_port": 80, "action": "accept", "order": 1}
    #     ],
    #     nat_rules=[],
    #     routing_rules=[],
    #     qos_config={"eth0": {"download": 100000, "upload": 50000, "algorithm": "cake"}}
    # )

if __name__ == "__main__":
    asyncio.run(main())
