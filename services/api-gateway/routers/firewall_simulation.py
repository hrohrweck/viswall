from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum

from shared.security import require_auth, require_admin
from shared.firewall_simulator import (
    FirewallSimulator, MultiFirewallSimulation,
    TestSuiteLibrary, NetworkPacket, Protocol, Action,
    FirewallRule, TestCase
)

router = APIRouter()


# ============================================================================
# Pydantic Models for API
# ============================================================================

class ProtocolEnum(str, Enum):
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    ANY = "any"


class ActionEnum(str, Enum):
    ACCEPT = "accept"
    DROP = "drop"
    REJECT = "reject"
    LOG = "log"


class PacketSpec(BaseModel):
    src_ip: str
    dst_ip: str
    protocol: ProtocolEnum
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    interface_in: str = "eth0"
    interface_out: str = "eth1"
    flags: List[str] = []
    connection_state: str = "NEW"


class RuleSpec(BaseModel):
    id: int
    name: str
    chain: str  # input, output, forward
    action: ActionEnum
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    protocol: Optional[ProtocolEnum] = None
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    interface_in: Optional[str] = None
    interface_out: Optional[str] = None
    state: Optional[str] = None
    log: bool = False
    order: int = 0
    enabled: bool = True


class TestCaseSpec(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = ""
    packet: PacketSpec
    expected_action: ActionEnum
    expected_chain: Optional[str] = None
    critical: bool = False
    tags: List[str] = []


class SimulationRequest(BaseModel):
    instance_id: int
    rules: List[RuleSpec]
    interfaces: Dict[str, str]  # interface_name -> type (wan/lan)
    packet: PacketSpec


class SimulationResponse(BaseModel):
    packet: Dict[str, Any]
    matched_rule: Optional[Dict[str, Any]]
    final_action: str
    chain_traversed: List[str]
    rules_evaluated: int
    processing_time_ms: float
    logs: List[str]
    nat_translation: Optional[Dict[str, Any]]


class TestSuiteRequest(BaseModel):
    instance_id: int
    rules: List[RuleSpec]
    interfaces: Dict[str, str]
    tests: List[TestCaseSpec]


class TestResultResponse(BaseModel):
    test_case: Dict[str, Any]
    passed: bool
    actual_action: str
    actual_rule: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time_ms: float


class TestSuiteResponse(BaseModel):
    total: int
    passed: int
    failed: int
    pass_rate: float
    critical_failures: List[str]
    can_deploy: bool
    results: List[TestResultResponse]


class MultiFirewallRequest(BaseModel):
    firewalls: List[Dict[str, Any]]  # id, name, rules, interfaces
    topology: Dict[str, List[str]]  # firewall_id -> connected_ids
    source_firewall: str
    dest_firewall: str
    packet: PacketSpec


class MultiFirewallTestRequest(BaseModel):
    firewalls: List[Dict[str, Any]]
    topology: Dict[str, List[str]]
    tests: List[Dict[str, Any]]  # source, dest, packet, expected_action


# ============================================================================
# SIMULATION ENDPOINTS
# ============================================================================

@router.post("/simulate/single", response_model=SimulationResponse)
async def simulate_single_firewall(
    request: SimulationRequest,
    user_id: int = Depends(require_auth)
):
    """
    Simulate a single packet through a firewall configuration.
    
    Returns detailed information about which rules matched and the final action.
    """
    # Create simulator
    sim = FirewallSimulator(
        firewall_id=f"instance-{request.instance_id}",
        firewall_name=f"Instance {request.instance_id}"
    )
    
    # Set interfaces
    sim.set_interfaces(request.interfaces)
    
    # Add rules
    for rule_spec in sorted(request.rules, key=lambda r: r.order):
        rule = FirewallRule(
            id=rule_spec.id,
            name=rule_spec.name,
            chain=rule_spec.chain,
            action=Action(rule_spec.action.value),
            src_ip=rule_spec.src_ip,
            dst_ip=rule_spec.dst_ip,
            protocol=Protocol(rule_spec.protocol.value) if rule_spec.protocol else None,
            src_port=rule_spec.src_port,
            dst_port=rule_spec.dst_port,
            interface_in=rule_spec.interface_in,
            interface_out=rule_spec.interface_out,
            state=rule_spec.state,
            log=rule_spec.log,
            order=rule_spec.order,
            enabled=rule_spec.enabled
        )
        sim.add_rule(rule)
    
    # Create packet
    packet = NetworkPacket(
        src_ip=request.packet.src_ip,
        dst_ip=request.packet.dst_ip,
        protocol=Protocol(request.packet.protocol.value),
        src_port=request.packet.src_port,
        dst_port=request.packet.dst_port,
        interface_in=request.packet.interface_in,
        interface_out=request.packet.interface_out,
        flags=request.packet.flags,
        connection_state=request.packet.connection_state
    )
    
    # Run simulation
    result = sim.simulate_packet(packet)
    
    return SimulationResponse(
        packet=result.packet.to_dict(),
        matched_rule={
            "id": result.matched_rule.id,
            "name": result.matched_rule.name,
            "action": result.matched_rule.action.value
        } if result.matched_rule else None,
        final_action=result.action.value,
        chain_traversed=result.chain_traversed,
        rules_evaluated=result.rules_evaluated,
        processing_time_ms=result.processing_time_ms,
        logs=result.logs,
        nat_translation=result.nat_translation
    )


@router.post("/simulate/test-suite", response_model=TestSuiteResponse)
async def run_test_suite(
    request: TestSuiteRequest,
    user_id: int = Depends(require_auth)
):
    """
    Run a comprehensive test suite against a firewall configuration.
    
    Tests can be marked as 'critical' - if any critical test fails,
    deployment should be blocked.
    """
    # Create simulator
    sim = FirewallSimulator(
        firewall_id=f"instance-{request.instance_id}",
        firewall_name=f"Instance {request.instance_id}"
    )
    
    # Set interfaces and rules
    sim.set_interfaces(request.interfaces)
    
    for rule_spec in sorted(request.rules, key=lambda r: r.order):
        rule = FirewallRule(
            id=rule_spec.id,
            name=rule_spec.name,
            chain=rule_spec.chain,
            action=Action(rule_spec.action.value),
            src_ip=rule_spec.src_ip,
            dst_ip=rule_spec.dst_ip,
            protocol=Protocol(rule_spec.protocol.value) if rule_spec.protocol else None,
            src_port=rule_spec.src_port,
            dst_port=rule_spec.dst_port,
            interface_in=rule_spec.interface_in,
            interface_out=rule_spec.interface_out,
            state=rule_spec.state,
            log=rule_spec.log,
            order=rule_spec.order,
            enabled=rule_spec.enabled
        )
        sim.add_rule(rule)
    
    # Convert test cases
    test_cases = []
    for test_spec in request.tests:
        test = TestCase(
            id=test_spec.id or f"test-{len(test_cases)}",
            name=test_spec.name,
            description=test_spec.description,
            packet=NetworkPacket(
                src_ip=test_spec.packet.src_ip,
                dst_ip=test_spec.packet.dst_ip,
                protocol=Protocol(test_spec.packet.protocol.value),
                src_port=test_spec.packet.src_port,
                dst_port=test_spec.packet.dst_port,
                interface_in=test_spec.packet.interface_in,
                interface_out=test_spec.packet.interface_out,
                flags=test_spec.packet.flags,
                connection_state=test_spec.packet.connection_state
            ),
            expected_action=Action(test_spec.expected_action.value),
            expected_chain=test_spec.expected_chain,
            critical=test_spec.critical,
            tags=test_spec.tags
        )
        test_cases.append(test)
    
    # Run tests
    results, summary = sim.run_test_suite(test_cases)
    
    return TestSuiteResponse(
        total=summary["total"],
        passed=summary["passed"],
        failed=summary["failed"],
        pass_rate=summary["pass_rate"],
        critical_failures=summary["critical_failures"],
        can_deploy=summary["can_deploy"],
        results=[
            TestResultResponse(
                test_case=r.test_case.to_dict(),
                passed=r.passed,
                actual_action=r.actual_action.value,
                actual_rule={
                    "id": r.actual_rule.id,
                    "name": r.actual_rule.name
                } if r.actual_rule else None,
                error_message=r.error_message,
                execution_time_ms=r.execution_time_ms
            )
            for r in results
        ]
    )


@router.post("/simulate/multi-firewall")
async def simulate_multi_firewall(
    request: MultiFirewallRequest,
    user_id: int = Depends(require_auth)
):
    """
    Simulate packet traversal across multiple firewalls.
    
    Useful for testing site-to-site VPNs, multi-hop routing,
    and distributed firewall policies.
    """
    # Create multi-firewall simulation
    multi_sim = MultiFirewallSimulation()
    
    # Add firewalls
    for fw_data in request.firewalls:
        fw = FirewallSimulator(
            firewall_id=fw_data["id"],
            firewall_name=fw_data["name"]
        )
        fw.set_interfaces(fw_data["interfaces"])
        
        for rule_data in fw_data.get("rules", []):
            rule = FirewallRule(**rule_data)
            fw.add_rule(rule)
        
        multi_sim.add_firewall(fw)
    
    # Set topology
    multi_sim.set_topology(request.topology)
    
    # Create packet
    packet = NetworkPacket(
        src_ip=request.packet.src_ip,
        dst_ip=request.packet.dst_ip,
        protocol=Protocol(request.packet.protocol.value),
        src_port=request.packet.src_port,
        dst_port=request.packet.dst_port,
        interface_in=request.packet.interface_in,
        interface_out=request.packet.interface_out,
        flags=request.packet.flags,
        connection_state=request.packet.connection_state
    )
    
    # Run simulation
    result = multi_sim.simulate_end_to_end(
        request.source_firewall,
        request.dest_firewall,
        packet
    )
    
    return result


@router.post("/simulate/multi-firewall/tests")
async def run_multi_firewall_tests(
    request: MultiFirewallTestRequest,
    user_id: int = Depends(require_auth)
):
    """
    Run tests across multiple firewalls.
    """
    # Create multi-firewall simulation
    multi_sim = MultiFirewallSimulation()
    
    # Add firewalls
    for fw_data in request.firewalls:
        fw = FirewallSimulator(
            firewall_id=fw_data["id"],
            firewall_name=fw_data["name"]
        )
        fw.set_interfaces(fw_data["interfaces"])
        
        for rule_data in fw_data.get("rules", []):
            rule = FirewallRule(**rule_data)
            fw.add_rule(rule)
        
        multi_sim.add_firewall(fw)
    
    # Set topology
    multi_sim.set_topology(request.topology)
    
    # Run tests
    result = multi_sim.run_multi_firewall_tests(request.tests)
    
    return result


# ============================================================================
# PREDEFINED TEST SUITES
# ============================================================================

@router.get("/test-suites/basic")
async def get_basic_test_suite(user_id: int = Depends(require_auth)):
    """Get the basic connectivity test suite"""
    tests = TestSuiteLibrary.get_basic_connectivity_tests()
    return {
        "name": "Basic Connectivity",
        "description": "Essential tests for basic firewall functionality",
        "tests": [t.to_dict() for t in tests]
    }


@router.get("/test-suites/security")
async def get_security_test_suite(user_id: int = Depends(require_auth)):
    """Get the security-focused test suite"""
    tests = TestSuiteLibrary.get_security_tests()
    return {
        "name": "Security",
        "description": "Tests for security-related rules and protections",
        "tests": [t.to_dict() for t in tests]
    }


@router.get("/test-suites/application")
async def get_application_test_suite(user_id: int = Depends(require_auth)):
    """Get application-specific test suite"""
    tests = TestSuiteLibrary.get_application_tests()
    return {
        "name": "Applications",
        "description": "Tests for specific applications (DNS, VoIP, Mail)",
        "tests": [t.to_dict() for t in tests]
    }


@router.get("/test-suites/all")
async def get_all_test_suites(user_id: int = Depends(require_auth)):
    """Get all predefined test suites"""
    return {
        "suites": [
            {
                "id": "basic",
                "name": "Basic Connectivity",
                "description": "Essential connectivity tests",
                "test_count": 5
            },
            {
                "id": "security",
                "name": "Security",
                "description": "Security-focused tests",
                "test_count": 3
            },
            {
                "id": "application",
                "name": "Applications",
                "description": "Application-specific tests",
                "test_count": 3
            }
        ]
    }


# ============================================================================
# VISUAL SIMULATION ENDPOINTS
# ============================================================================

@router.post("/simulate/visual")
async def get_visual_simulation_data(
    request: SimulationRequest,
    user_id: int = Depends(require_auth)
):
    """
    Get data for visual packet flow simulation.
    
    Returns step-by-step data for animating packet flow through rules.
    """
    # Run simulation
    sim = FirewallSimulator(
        firewall_id=f"instance-{request.instance_id}",
        firewall_name=f"Instance {request.instance_id}"
    )
    
    sim.set_interfaces(request.interfaces)
    
    for rule_spec in sorted(request.rules, key=lambda r: r.order):
        rule = FirewallRule(
            id=rule_spec.id,
            name=rule_spec.name,
            chain=rule_spec.chain,
            action=Action(rule_spec.action.value),
            src_ip=rule_spec.src_ip,
            dst_ip=rule_spec.dst_ip,
            protocol=Protocol(rule_spec.protocol.value) if rule_spec.protocol else None,
            src_port=rule_spec.src_port,
            dst_port=rule_spec.dst_port,
            interface_in=rule_spec.interface_in,
            interface_out=rule_spec.interface_out,
            state=rule_spec.state,
            log=rule_spec.log,
            order=rule_spec.order,
            enabled=rule_spec.enabled
        )
        sim.add_rule(rule)
    
    packet = NetworkPacket(
        src_ip=request.packet.src_ip,
        dst_ip=request.packet.dst_ip,
        protocol=Protocol(request.packet.protocol.value),
        src_port=request.packet.src_port,
        dst_port=request.packet.dst_port,
        interface_in=request.packet.interface_in,
        interface_out=request.packet.interface_out,
        flags=request.packet.flags,
        connection_state=request.packet.connection_state
    )
    
    result = sim.simulate_packet(packet)
    
    # Build visual steps
    steps = []
    
    # Step 1: Packet entry
    steps.append({
        "step": 1,
        "type": "entry",
        "description": f"Packet enters via {packet.interface_in}",
        "packet": packet.to_dict(),
        "position": {"x": 0, "y": 50}
    })
    
    # Step 2: Chain selection
    chain = result.chain_traversed[0] if result.chain_traversed else "unknown"
    steps.append({
        "step": 2,
        "type": "chain_selection",
        "description": f"Packet routed to '{chain}' chain",
        "chain": chain,
        "position": {"x": 100, "y": 50}
    })
    
    # Steps for each rule evaluation
    step_num = 3
    y_pos = 100
    
    for i, rule in enumerate(request.rules):
        if rule.chain == chain:
            matched = result.matched_rule and result.matched_rule.id == rule.id
            
            steps.append({
                "step": step_num,
                "type": "rule_evaluation",
                "description": f"Evaluating rule: {rule.name}",
                "rule": rule.dict(),
                "matched": matched,
                "position": {"x": 200, "y": y_pos}
            })
            
            step_num += 1
            y_pos += 60
            
            if matched:
                break
    
    # Final action step
    steps.append({
        "step": step_num,
        "type": "action",
        "description": f"Final action: {result.action.value}",
        "action": result.action.value,
        "position": {"x": 400, "y": 50}
    })
    
    return {
        "packet": packet.to_dict(),
        "steps": steps,
        "final_result": result.to_dict()
    }
