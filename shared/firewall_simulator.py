"""
Viswall Firewall Rule Simulator

Simulates network traffic against firewall rules to validate configurations
before deployment. Supports multi-firewall scenarios and test suites.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import json
import random
from datetime import datetime


class Protocol(Enum):
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    ANY = "any"


class Action(Enum):
    ACCEPT = "accept"
    DROP = "drop"
    REJECT = "reject"
    LOG = "log"
    NAT = "nat"


@dataclass
class NetworkPacket:
    """Represents a network packet for simulation"""
    src_ip: str
    dst_ip: str
    protocol: Protocol
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    interface_in: str = "eth0"
    interface_out: str = "eth1"
    flags: List[str] = field(default_factory=list)  # SYN, ACK, FIN, etc.
    payload_size: int = 64
    timestamp: datetime = field(default_factory=datetime.utcnow)
    connection_state: str = "NEW"  # NEW, ESTABLISHED, RELATED, INVALID
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "protocol": self.protocol.value,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "interface_in": self.interface_in,
            "interface_out": self.interface_out,
            "flags": self.flags,
            "payload_size": self.payload_size,
            "connection_state": self.connection_state
        }


@dataclass
class FirewallRule:
    """Simplified firewall rule for simulation"""
    id: int
    name: str
    chain: str  # input, output, forward, prerouting, postrouting
    action: Action
    src_ip: Optional[str] = None  # Can be CIDR or "any"
    dst_ip: Optional[str] = None
    protocol: Optional[Protocol] = None
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    interface_in: Optional[str] = None
    interface_out: Optional[str] = None
    state: Optional[str] = None  # NEW, ESTABLISHED, RELATED, INVALID
    log: bool = False
    order: int = 0
    enabled: bool = True
    
    def matches(self, packet: NetworkPacket) -> bool:
        """Check if packet matches this rule"""
        if not self.enabled:
            return False
        
        # Source IP check
        if self.src_ip and self.src_ip != "any":
            if "/" in self.src_ip:  # CIDR
                if not self._ip_in_network(packet.src_ip, self.src_ip):
                    return False
            elif packet.src_ip != self.src_ip:
                return False
        
        # Destination IP check
        if self.dst_ip and self.dst_ip != "any":
            if "/" in self.dst_ip:
                if not self._ip_in_network(packet.dst_ip, self.dst_ip):
                    return False
            elif packet.dst_ip != self.dst_ip:
                return False
        
        # Protocol check
        if self.protocol and self.protocol != Protocol.ANY:
            if packet.protocol != self.protocol:
                return False
        
        # Port checks
        if self.src_port and packet.src_port != self.src_port:
            return False
        if self.dst_port and packet.dst_port != self.dst_port:
            return False
        
        # Interface checks
        if self.interface_in and packet.interface_in != self.interface_in:
            return False
        if self.interface_out and packet.interface_out != self.interface_out:
            return False
        
        # Connection state
        if self.state and packet.connection_state != self.state:
            return False
        
        return True
    
    def _ip_in_network(self, ip: str, network: str) -> bool:
        """Check if IP is in CIDR network"""
        import ipaddress
        try:
            return ipaddress.ip_address(ip) in ipaddress.ip_network(network)
        except:
            return False


@dataclass
class SimulationResult:
    """Result of a single packet simulation"""
    packet: NetworkPacket
    matched_rule: Optional[FirewallRule]
    action: Action
    chain_traversed: List[str]
    rules_evaluated: int
    processing_time_ms: float
    logs: List[str] = field(default_factory=list)
    nat_translation: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "packet": self.packet.to_dict(),
            "matched_rule": {
                "id": self.matched_rule.id,
                "name": self.matched_rule.name,
                "action": self.matched_rule.action.value
            } if self.matched_rule else None,
            "final_action": self.action.value,
            "chain_traversed": self.chain_traversed,
            "rules_evaluated": self.rules_evaluated,
            "processing_time_ms": self.processing_time_ms,
            "logs": self.logs,
            "nat_translation": self.nat_translation
        }


@dataclass
class TestCase:
    """A test case for firewall validation"""
    id: str
    name: str
    description: str
    packet: NetworkPacket
    expected_action: Action
    expected_chain: Optional[str] = None
    critical: bool = False  # If True, failure blocks deployment
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "packet": self.packet.to_dict(),
            "expected_action": self.expected_action.value,
            "expected_chain": self.expected_chain,
            "critical": self.critical,
            "tags": self.tags
        }


@dataclass
class TestResult:
    """Result of running a test case"""
    test_case: TestCase
    passed: bool
    actual_action: Action
    actual_rule: Optional[FirewallRule]
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_case": self.test_case.to_dict(),
            "passed": self.passed,
            "actual_action": self.actual_action.value,
            "actual_rule": {
                "id": self.actual_rule.id,
                "name": self.actual_rule.name
            } if self.actual_rule else None,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms
        }


class FirewallSimulator:
    """Simulates firewall behavior with rules and packets"""
    
    def __init__(self, firewall_id: str, firewall_name: str):
        self.firewall_id = firewall_id
        self.firewall_name = firewall_name
        self.rules: List[FirewallRule] = []
        self.interfaces: Dict[str, str] = {}  # name -> type (wan/lan)
        self.nat_rules: List[FirewallRule] = []
        
    def add_rule(self, rule: FirewallRule):
        """Add a rule to the simulation"""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.order)
    
    def add_nat_rule(self, rule: FirewallRule):
        """Add a NAT rule"""
        self.nat_rules.append(rule)
        self.nat_rules.sort(key=lambda r: r.order)
    
    def set_interfaces(self, interfaces: Dict[str, str]):
        """Set interface types (wan/lan)"""
        self.interfaces = interfaces
    
    def simulate_packet(self, packet: NetworkPacket) -> SimulationResult:
        """Simulate a single packet through the firewall"""
        import time
        start_time = time.time()
        
        chain_traversed = []
        logs = []
        rules_evaluated = 0
        nat_translation = None
        
        # Determine chain based on interfaces
        chain = self._determine_chain(packet)
        chain_traversed.append(chain)
        
        # Check NAT first (prerouting)
        if chain == "forward":
            nat_rule = self._check_nat(packet, "prerouting")
            if nat_rule:
                nat_translation = self._apply_nat(packet, nat_rule)
                logs.append(f"NAT applied: {nat_rule.name}")
        
        # Evaluate rules in chain
        matched_rule = None
        final_action = Action.ACCEPT  # Default policy
        
        for rule in self.rules:
            if rule.chain != chain:
                continue
            
            rules_evaluated += 1
            
            if rule.matches(packet):
                matched_rule = rule
                final_action = rule.action
                
                if rule.log:
                    logs.append(f"Rule {rule.id} ({rule.name}): {rule.action.value}")
                
                if rule.action in [Action.DROP, Action.REJECT]:
                    break
        
        # Postrouting NAT for forwarded traffic
        if chain == "forward" and final_action == Action.ACCEPT:
            nat_rule = self._check_nat(packet, "postrouting")
            if nat_rule:
                if not nat_translation:
                    nat_translation = {}
                nat_translation["postrouting"] = nat_rule.name
        
        processing_time = (time.time() - start_time) * 1000
        
        return SimulationResult(
            packet=packet,
            matched_rule=matched_rule,
            action=final_action,
            chain_traversed=chain_traversed,
            rules_evaluated=rules_evaluated,
            processing_time_ms=processing_time,
            logs=logs,
            nat_translation=nat_translation
        )
    
    def _determine_chain(self, packet: NetworkPacket) -> str:
        """Determine which chain a packet belongs to"""
        src_type = self.interfaces.get(packet.interface_in, "unknown")
        dst_type = self.interfaces.get(packet.interface_out, "unknown")
        
        # Input: from WAN to firewall
        if src_type == "wan":
            return "input"
        
        # Forward: from LAN to WAN or inter-VLAN
        if src_type == "lan" and dst_type == "wan":
            return "forward"
        
        # Output: from firewall to anywhere
        return "output"
    
    def _check_nat(self, packet: NetworkPacket, nat_chain: str) -> Optional[FirewallRule]:
        """Check if NAT applies to packet"""
        for rule in self.nat_rules:
            if rule.chain == nat_chain and rule.matches(packet):
                return rule
        return None
    
    def _apply_nat(self, packet: NetworkPacket, rule: FirewallRule) -> Dict[str, Any]:
        """Apply NAT transformation"""
        return {
            "type": rule.action.value,
            "original_dst": packet.dst_ip,
            "translated_dst": rule.dst_ip  # Simplified
        }
    
    def run_test_suite(self, test_cases: List[TestCase]) -> Tuple[List[TestResult], Dict[str, Any]]:
        """Run a suite of test cases"""
        results = []
        passed = 0
        failed = 0
        critical_failures = []
        
        for test in test_cases:
            result = self._run_single_test(test)
            results.append(result)
            
            if result.passed:
                passed += 1
            else:
                failed += 1
                if test.critical:
                    critical_failures.append(test.id)
        
        summary = {
            "total": len(test_cases),
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / len(test_cases) * 100) if test_cases else 0,
            "critical_failures": critical_failures,
            "can_deploy": len(critical_failures) == 0 and failed == 0
        }
        
        return results, summary
    
    def _run_single_test(self, test_case: TestCase) -> TestResult:
        """Run a single test case"""
        import time
        start_time = time.time()
        
        result = self.simulate_packet(test_case.packet)
        
        # Check if result matches expectation
        passed = result.action == test_case.expected_action
        error_msg = None
        
        if not passed:
            error_msg = f"Expected {test_case.expected_action.value}, got {result.action.value}"
        
        if test_case.expected_chain and test_case.expected_chain not in result.chain_traversed:
            passed = False
            error_msg = f"Expected chain {test_case.expected_chain}, traversed {result.chain_traversed}"
        
        execution_time = (time.time() - start_time) * 1000
        
        return TestResult(
            test_case=test_case,
            passed=passed,
            actual_action=result.action,
            actual_rule=result.matched_rule,
            error_message=error_msg,
            execution_time_ms=execution_time
        )


class MultiFirewallSimulation:
    """Simulate traffic across multiple firewalls (e.g., site-to-site)"""
    
    def __init__(self):
        self.firewalls: Dict[str, FirewallSimulator] = {}
        self.topology: Dict[str, List[str]] = {}  # firewall_id -> connected_firewalls
    
    def add_firewall(self, firewall: FirewallSimulator):
        """Add a firewall to the simulation"""
        self.firewalls[firewall.firewall_id] = firewall
    
    def set_topology(self, topology: Dict[str, List[str]]):
        """Set network topology (which firewalls are connected)"""
        self.topology = topology
    
    def simulate_end_to_end(
        self,
        source_fw: str,
        dest_fw: str,
        packet: NetworkPacket
    ) -> Dict[str, Any]:
        """Simulate packet traversal across multiple firewalls"""
        
        path = self._calculate_path(source_fw, dest_fw)
        if not path:
            return {
                "error": "No path found between firewalls",
                "source": source_fw,
                "destination": dest_fw
            }
        
        results = []
        current_packet = packet
        
        for fw_id in path:
            fw = self.firewalls.get(fw_id)
            if not fw:
                continue
            
            result = fw.simulate_packet(current_packet)
            results.append({
                "firewall_id": fw_id,
                "firewall_name": fw.firewall_name,
                "result": result.to_dict()
            })
            
            # If packet is dropped, stop simulation
            if result.action in [Action.DROP, Action.REJECT]:
                break
            
            # Update packet for next hop (NAT changes)
            if result.nat_translation:
                current_packet = self._apply_nat_to_packet(
                    current_packet, result.nat_translation
                )
        
        return {
            "path": path,
            "hops": len(results),
            "final_action": results[-1]["result"]["final_action"] if results else "unknown",
            "firewall_results": results
        }
    
    def _calculate_path(self, source: str, dest: str) -> List[str]:
        """Calculate path between firewalls using BFS"""
        if source == dest:
            return [source]
        
        visited = {source}
        queue = [(source, [source])]
        
        while queue:
            current, path = queue.pop(0)
            
            for neighbor in self.topology.get(current, []):
                if neighbor == dest:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []  # No path found
    
    def _apply_nat_to_packet(
        self,
        packet: NetworkPacket,
        nat_translation: Dict[str, Any]
    ) -> NetworkPacket:
        """Apply NAT transformation to packet"""
        # Create new packet with translated addresses
        new_dst = nat_translation.get("translated_dst", packet.dst_ip)
        
        return NetworkPacket(
            src_ip=packet.src_ip,
            dst_ip=new_dst,
            protocol=packet.protocol,
            src_port=packet.src_port,
            dst_port=packet.dst_port,
            interface_in=packet.interface_in,
            interface_out=packet.interface_out,
            flags=packet.flags,
            payload_size=packet.payload_size,
            connection_state=packet.connection_state
        )
    
    def run_multi_firewall_tests(
        self,
        tests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run tests across multiple firewalls"""
        results = []
        all_passed = True
        
        for test in tests:
            source_fw = test.get("source_firewall")
            dest_fw = test.get("dest_firewall")
            packet_data = test.get("packet")
            expected_result = test.get("expected_result")
            
            packet = NetworkPacket(**packet_data)
            
            result = self.simulate_end_to_end(source_fw, dest_fw, packet)
            
            # Check if result matches expectation
            passed = result.get("final_action") == expected_result
            if not passed:
                all_passed = False
            
            results.append({
                "test_name": test.get("name"),
                "source": source_fw,
                "destination": dest_fw,
                "passed": passed,
                "result": result
            })
        
        return {
            "all_passed": all_passed,
            "tests": results,
            "can_deploy": all_passed
        }


class TestSuiteLibrary:
    """Library of pre-defined test cases for common scenarios"""
    
    @staticmethod
    def get_basic_connectivity_tests() -> List[TestCase]:
        """Get basic connectivity test cases"""
        return [
            TestCase(
                id="basic-internet-http",
                name="LAN to Internet HTTP",
                description="Verify HTTP traffic from LAN to internet works",
                packet=NetworkPacket(
                    src_ip="192.168.1.100",
                    dst_ip="8.8.8.8",
                    protocol=Protocol.TCP,
                    src_port=12345,
                    dst_port=80,
                    interface_in="eth1",
                    interface_out="eth0",
                    flags=["SYN"],
                    connection_state="NEW"
                ),
                expected_action=Action.ACCEPT,
                expected_chain="forward",
                critical=True,
                tags=["basic", "http", "lan-wan"]
            ),
            TestCase(
                id="basic-internet-https",
                name="LAN to Internet HTTPS",
                description="Verify HTTPS traffic from LAN to internet works",
                packet=NetworkPacket(
                    src_ip="192.168.1.100",
                    dst_ip="1.1.1.1",
                    protocol=Protocol.TCP,
                    src_port=12345,
                    dst_port=443,
                    interface_in="eth1",
                    interface_out="eth0",
                    flags=["SYN"],
                    connection_state="NEW"
                ),
                expected_action=Action.ACCEPT,
                expected_chain="forward",
                critical=True,
                tags=["basic", "https", "lan-wan"]
            ),
            TestCase(
                id="wan-ping",
                name="WAN Ping Response",
                description="Verify ping responses from firewall work",
                packet=NetworkPacket(
                    src_ip="203.0.113.1",
                    dst_ip="192.0.2.1",
                    protocol=Protocol.ICMP,
                    interface_in="eth0",
                    interface_out="lo"
                ),
                expected_action=Action.ACCEPT,
                expected_chain="input",
                critical=True,
                tags=["basic", "icmp", "ping"]
            ),
            TestCase(
                id="block-wan-ssh",
                name="Block WAN SSH",
                description="Verify SSH from internet is blocked",
                packet=NetworkPacket(
                    src_ip="203.0.113.100",
                    dst_ip="192.0.2.1",
                    protocol=Protocol.TCP,
                    src_port=54321,
                    dst_port=22,
                    interface_in="eth0",
                    interface_out="lo",
                    flags=["SYN"],
                    connection_state="NEW"
                ),
                expected_action=Action.DROP,
                critical=True,
                tags=["security", "ssh", "wan-block"]
            ),
            TestCase(
                id="established-allowed",
                name="Established Connections Allowed",
                description="Verify established connections are allowed back in",
                packet=NetworkPacket(
                    src_ip="8.8.8.8",
                    dst_ip="192.168.1.100",
                    protocol=Protocol.TCP,
                    src_port=443,
                    dst_port=12345,
                    interface_in="eth0",
                    interface_out="eth1",
                    flags=["SYN", "ACK"],
                    connection_state="ESTABLISHED"
                ),
                expected_action=Action.ACCEPT,
                critical=True,
                tags=["basic", "established", "return-traffic"]
            ),
        ]
    
    @staticmethod
    def get_security_tests() -> List[TestCase]:
        """Get security-focused test cases"""
        return [
            TestCase(
                id="block-spoofed-internal",
                name="Block Spoofed Internal Traffic",
                description="Block traffic claiming to be from internal network but coming from WAN",
                packet=NetworkPacket(
                    src_ip="192.168.1.50",  # Spoofed internal IP
                    dst_ip="192.168.1.100",
                    protocol=Protocol.TCP,
                    src_port=12345,
                    dst_port=22,
                    interface_in="eth0",  # Coming from WAN!
                    interface_out="eth1",
                    flags=["SYN"]
                ),
                expected_action=Action.DROP,
                critical=True,
                tags=["security", "spoofing", "wan"]
            ),
            TestCase(
                id="block-port-scan",
                name="Block Port Scan",
                description="Block rapid port scanning attempts",
                packet=NetworkPacket(
                    src_ip="203.0.113.200",
                    dst_ip="192.0.2.1",
                    protocol=Protocol.TCP,
                    src_port=12345,
                    dst_port=23,  # Telnet
                    interface_in="eth0",
                    interface_out="lo",
                    flags=["SYN"]
                ),
                expected_action=Action.DROP,
                critical=False,
                tags=["security", "port-scan", "telnet"]
            ),
            TestCase(
                id="block-invalid-state",
                name="Block Invalid State Packets",
                description="Block packets with invalid connection state",
                packet=NetworkPacket(
                    src_ip="203.0.113.50",
                    dst_ip="192.0.2.1",
                    protocol=Protocol.TCP,
                    src_port=12345,
                    dst_port=443,
                    interface_in="eth0",
                    interface_out="lo",
                    flags=["ACK"],  # ACK without SYN
                    connection_state="INVALID"
                ),
                expected_action=Action.DROP,
                critical=True,
                tags=["security", "invalid-state", "tcp"]
            ),
        ]
    
    @staticmethod
    def get_application_tests() -> List[TestCase]:
        """Get application-specific test cases"""
        return [
            TestCase(
                id="dns-udp",
                name="DNS UDP Query",
                description="Allow DNS queries over UDP",
                packet=NetworkPacket(
                    src_ip="192.168.1.100",
                    dst_ip="8.8.8.8",
                    protocol=Protocol.UDP,
                    src_port=12345,
                    dst_port=53,
                    interface_in="eth1",
                    interface_out="eth0"
                ),
                expected_action=Action.ACCEPT,
                critical=True,
                tags=["dns", "udp", "essential"]
            ),
            TestCase(
                id="smtp-outbound",
                name="SMTP Outbound",
                description="Allow outbound SMTP from mail server",
                packet=NetworkPacket(
                    src_ip="192.168.1.10",  # Mail server
                    dst_ip="203.0.113.10",
                    protocol=Protocol.TCP,
                    src_port=12345,
                    dst_port=25,
                    interface_in="eth1",
                    interface_out="eth0",
                    flags=["SYN"]
                ),
                expected_action=Action.ACCEPT,
                critical=False,
                tags=["mail", "smtp", "server"]
            ),
            TestCase(
                id="voip-sip",
                name="VoIP SIP Traffic",
                description="Allow SIP signaling for VoIP",
                packet=NetworkPacket(
                    src_ip="192.168.1.50",  # VoIP phone
                    dst_ip="203.0.113.20",  # SIP provider
                    protocol=Protocol.UDP,
                    src_port=5060,
                    dst_port=5060,
                    interface_in="eth1",
                    interface_out="eth0"
                ),
                expected_action=Action.ACCEPT,
                critical=False,
                tags=["voip", "sip", "udp"]
            ),
        ]
    
    @staticmethod
    def get_custom_test(
        name: str,
        src_ip: str,
        dst_ip: str,
        protocol: str,
        dst_port: int,
        expected_action: str,
        **kwargs
    ) -> TestCase:
        """Create a custom test case"""
        return TestCase(
            id=f"custom-{random.randint(1000, 9999)}",
            name=name,
            description=kwargs.get("description", ""),
            packet=NetworkPacket(
                src_ip=src_ip,
                dst_ip=dst_ip,
                protocol=Protocol(protocol),
                src_port=kwargs.get("src_port", random.randint(10000, 65000)),
                dst_port=dst_port,
                interface_in=kwargs.get("interface_in", "eth1"),
                interface_out=kwargs.get("interface_out", "eth0"),
                flags=kwargs.get("flags", ["SYN"]),
                connection_state=kwargs.get("connection_state", "NEW")
            ),
            expected_action=Action(expected_action),
            critical=kwargs.get("critical", False),
            tags=kwargs.get("tags", [])
        )


# Example usage
if __name__ == "__main__":
    # Create a firewall simulator
    fw = FirewallSimulator("fw-001", "Main Office Firewall")
    
    # Set interfaces
    fw.set_interfaces({"eth0": "wan", "eth1": "lan"})
    
    # Add some rules
    fw.add_rule(FirewallRule(
        id=1,
        name="Allow LAN to WAN",
        chain="forward",
        action=Action.ACCEPT,
        interface_in="eth1",
        interface_out="eth0",
        order=100
    ))
    
    fw.add_rule(FirewallRule(
        id=2,
        name="Block WAN SSH",
        chain="input",
        action=Action.DROP,
        protocol=Protocol.TCP,
        dst_port=22,
        interface_in="eth0",
        order=50
    ))
    
    # Get test suite
    tests = TestSuiteLibrary.get_basic_connectivity_tests()
    
    # Run tests
    results, summary = fw.run_test_suite(tests)
    
    print(f"Test Results: {summary['passed']}/{summary['total']} passed")
    print(f"Can deploy: {summary['can_deploy']}")
    
    for result in results:
        status = "✓" if result.passed else "✗"
        print(f"{status} {result.test_case.name}: {result.actual_action.value}")
