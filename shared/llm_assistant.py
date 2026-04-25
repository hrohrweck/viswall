"""
Viswall LLM Configuration Assistant

Helps administrators define configurations using natural language.
Can generate firewall rules, test cases, VPN configs, and more.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AssistantIntent(Enum):
    CREATE_FIREWALL_RULE = "create_firewall_rule"
    GENERATE_TEST_CASE = "generate_test_case"
    CREATE_VPN_CONFIG = "create_vpn_config"
    SETUP_MAIL_DOMAIN = "setup_mail_domain"
    EXPLAIN_CONFIGURATION = "explain_configuration"
    TROUBLESHOOT = "troubleshoot"
    OPTIMIZE_RULES = "optimize_rules"
    GENERATE_REPORT = "generate_report"
    UNKNOWN = "unknown"


@dataclass
class AssistantContext:
    instance_id: Optional[int] = None
    current_config: Optional[Dict[str, Any]] = None
    user_role: str = "admin"
    conversation_history: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []


class LLMConfigurationAssistant:
    """LLM-powered assistant for configuration management"""

    def __init__(
        self,
        db: Optional[Any] = None,
        provider: str = "openai",
        model: str = "gpt-4",
        api_key: Optional[str] = None,
    ):
        self.db = db
        self.provider = provider
        self.model = model
        self.api_key = api_key
    
    async def process_request(
        self,
        user_message: str,
        context: AssistantContext
    ) -> Dict[str, Any]:
        """Process a user request and return appropriate response"""
        
        # Determine intent
        intent = await self._classify_intent(user_message)
        
        # Route to appropriate handler
        handlers = {
            AssistantIntent.CREATE_FIREWALL_RULE: self._handle_firewall_rule_creation,
            AssistantIntent.GENERATE_TEST_CASE: self._handle_test_case_generation,
            AssistantIntent.CREATE_VPN_CONFIG: self._handle_vpn_config,
            AssistantIntent.SETUP_MAIL_DOMAIN: self._handle_mail_setup,
            AssistantIntent.EXPLAIN_CONFIGURATION: self._handle_explanation,
            AssistantIntent.TROUBLESHOOT: self._handle_troubleshooting,
            AssistantIntent.OPTIMIZE_RULES: self._handle_optimization,
            AssistantIntent.GENERATE_REPORT: self._handle_report_generation,
        }
        
        handler = handlers.get(intent, self._handle_unknown)
        return await handler(user_message, context)
    
    async def _classify_intent(self, message: str) -> AssistantIntent:
        """Classify the user's intent from their message"""
        message_lower = message.lower()
        
        # Simple keyword-based classification (in production, use LLM)
        if any(word in message_lower for word in ["firewall rule", "block", "allow", "permit", "deny", "port", "open port"]):
            return AssistantIntent.CREATE_FIREWALL_RULE
        
        if any(word in message_lower for word in ["test", "check if", "verify", "simulation"]):
            return AssistantIntent.GENERATE_TEST_CASE
        
        if any(word in message_lower for word in ["vpn", "wireguard", "ipsec", "openvpn", "tunnel"]):
            return AssistantIntent.CREATE_VPN_CONFIG
        
        if any(word in message_lower for word in ["mail", "email", "domain", "mx", "smtp"]):
            return AssistantIntent.SETUP_MAIL_DOMAIN
        
        if any(word in message_lower for word in ["explain", "how does", "what is", "why"]):
            return AssistantIntent.EXPLAIN_CONFIGURATION
        
        if any(word in message_lower for word in ["problem", "issue", "error", "not working", "broken"]):
            return AssistantIntent.TROUBLESHOOT
        
        if any(word in message_lower for word in ["optimize", "improve", "better", "clean up"]):
            return AssistantIntent.OPTIMIZE_RULES
        
        if any(word in message_lower for word in ["report", "summary", "overview", "status"]):
            return AssistantIntent.GENERATE_REPORT
        
        return AssistantIntent.UNKNOWN
    
    async def _handle_firewall_rule_creation(
        self,
        message: str,
        context: AssistantContext
    ) -> Dict[str, Any]:
        """Handle firewall rule creation requests"""
        
        prompt = f"""You are a firewall configuration expert. Analyze this request and extract firewall rule parameters.

User request: "{message}"

Extract the following information and respond in JSON format:
{{
    "rule_name": "descriptive name for the rule",
    "chain": "input|output|forward",
    "action": "accept|drop|reject",
    "protocol": "tcp|udp|icmp|any",
    "src_ip": "source IP or CIDR (null if not specified)",
    "dst_ip": "destination IP or CIDR (null if not specified)",
    "src_port": source port number (null if not specified),
    "dst_port": destination port number (null if not specified),
    "interface_in": "incoming interface (null if not specified)",
    "interface_out": "outgoing interface (null if not specified)",
    "log": true|false,
    "explanation": "explain what this rule does in simple terms",
    "security_notes": "any security considerations"
}}

If the request is unclear or incomplete, set "needs_clarification": true and "clarification_questions": ["question 1", "question 2"]"""

        response = await self._call_llm(prompt)
        
        try:
            rule_data = json.loads(response)
            
            if rule_data.get("needs_clarification"):
                return {
                    "type": "clarification_needed",
                    "message": "I need some clarification to create this rule:",
                    "questions": rule_data.get("clarification_questions", []),
                    "suggested_rule": None
                }
            
            return {
                "type": "firewall_rule_suggestion",
                "message": f"I've created a firewall rule based on your request: {rule_data.get('explanation')}",
                "rule": {
                    "id": -1,  # Temporary ID
                    "name": rule_data.get("rule_name", "New Rule"),
                    "chain": rule_data.get("chain", "forward"),
                    "action": rule_data.get("action", "accept"),
                    "protocol": rule_data.get("protocol"),
                    "src_ip": rule_data.get("src_ip"),
                    "dst_ip": rule_data.get("dst_ip"),
                    "src_port": rule_data.get("src_port"),
                    "dst_port": rule_data.get("dst_port"),
                    "interface_in": rule_data.get("interface_in"),
                    "interface_out": rule_data.get("interface_out"),
                    "log": rule_data.get("log", False),
                    "enabled": True,
                    "order": 100
                },
                "explanation": rule_data.get("explanation"),
                "security_notes": rule_data.get("security_notes"),
                "can_apply": True
            }
        except json.JSONDecodeError:
            return {
                "type": "error",
                "message": "I had trouble understanding your request. Could you rephrase it?",
                "suggested_rule": None
            }
    
    async def _handle_test_case_generation(
        self,
        message: str,
        context: AssistantContext
    ) -> Dict[str, Any]:
        """Handle test case generation requests"""
        
        prompt = f"""You are a network security testing expert. Generate test cases to verify firewall behavior.

User request: "{message}"

Generate test cases in JSON format:
{{
    "test_cases": [
        {{
            "name": "test name",
            "description": "what this test verifies",
            "packet": {{
                "src_ip": "source IP",
                "dst_ip": "destination IP",
                "protocol": "tcp|udp|icmp",
                "src_port": number or null,
                "dst_port": number or null,
                "interface_in": "eth0|eth1",
                "connection_state": "NEW|ESTABLISHED"
            }},
            "expected_action": "accept|drop",
            "critical": true|false,
            "tags": ["tag1", "tag2"]
        }}
    ],
    "explanation": "explain what these tests verify",
    "coverage_assessment": "what scenarios are covered"
}}"""

        response = await self._call_llm(prompt)
        
        try:
            data = json.loads(response)
            
            return {
                "type": "test_cases_generated",
                "message": f"I've generated {len(data.get('test_cases', []))} test cases for you.",
                "test_cases": data.get("test_cases", []),
                "explanation": data.get("explanation"),
                "coverage_assessment": data.get("coverage_assessment"),
                "can_run": True
            }
        except json.JSONDecodeError:
            return {
                "type": "error",
                "message": "I couldn't generate test cases from that request. Try being more specific about what you want to test.",
                "test_cases": []
            }
    
    async def _handle_vpn_config(
        self,
        message: str,
        context: AssistantContext
    ) -> Dict[str, Any]:
        """Handle VPN configuration requests"""
        
        prompt = f"""You are a VPN configuration expert. Help set up a VPN based on the user's needs.

User request: "{message}"

Respond in JSON format:
{{
    "recommendation": {{
        "protocol": "wireguard|ipsec|openvpn",
        "reasoning": "why this protocol is recommended",
        "topology": "road_warrior|site_to_site|mesh"
    }},
    "configuration": {{
        "server_config": {{
            "listen_port": number,
            "network_cidr": "VPN subnet",
            "dns_servers": ["dns1", "dns2"]
        }},
        "client_config": {{
            "split_tunnel": true|false,
            "routes": ["networks to route through VPN"]
        }}
    }},
    "security_settings": {{
        "cipher": "recommended cipher",
        "key_exchange": "DH group or curve"
    }},
    "explanation": "simple explanation of the setup"
}}"""

        response = await self._call_llm(prompt)
        
        try:
            data = json.loads(response)
            
            return {
                "type": "vpn_config_suggestion",
                "message": f"I've prepared a VPN configuration for you: {data.get('explanation')}",
                "recommendation": data.get("recommendation"),
                "configuration": data.get("configuration"),
                "security_settings": data.get("security_settings"),
                "can_apply": True
            }
        except json.JSONDecodeError:
            return {
                "type": "error",
                "message": "I couldn't parse the VPN configuration. Please provide more details about your use case.",
                "recommendation": None
            }
    
    async def _handle_mail_setup(
        self,
        message: str,
        context: AssistantContext
    ) -> Dict[str, Any]:
        """Handle mail domain setup requests"""
        
        prompt = f"""You are an email infrastructure expert. Help set up a mail domain.

User request: "{message}"

Respond in JSON format:
{{
    "domain_config": {{
        "domain": "domain name",
        "security_features": ["dkim", "dmarc", "spf"],
        "recommended_settings": {{
            "spam_threshold": 5.0,
            "virus_scan": true,
            "llm_enabled": false
        }}
    }},
    "dns_records": [
        {{
            "type": "MX|TXT|DKIM",
            "name": "record name",
            "value": "record value"
        }}
    ],
    "explanation": "setup explanation",
    "deliverability_tips": ["tip1", "tip2"]
}}"""

        response = await self._call_llm(prompt)
        
        try:
            data = json.loads(response)
            
            return {
                "type": "mail_setup_suggestion",
                "message": f"I've prepared a mail domain configuration for {data.get('domain_config', {}).get('domain')}",
                "domain_config": data.get("domain_config"),
                "dns_records": data.get("dns_records"),
                "explanation": data.get("explanation"),
                "deliverability_tips": data.get("deliverability_tips", []),
                "can_apply": True
            }
        except json.JSONDecodeError:
            return {
                "type": "error",
                "message": "I couldn't parse the mail configuration. Please provide the domain name and any specific requirements.",
                "domain_config": None
            }
    
    async def _handle_explanation(
        self,
        message: str,
        context: AssistantContext
    ) -> Dict[str, Any]:
        """Handle configuration explanation requests"""
        
        config_summary = json.dumps(context.current_config, indent=2) if context.current_config else "No configuration provided"
        
        prompt = f"""You are a network security educator. Explain this configuration in simple terms.

User question: "{message}"

Current configuration:
{config_summary}

Provide a clear, educational explanation suitable for a network administrator. Include:
1. What the configuration does
2. Why it's set up this way (if apparent)
3. Any security implications
4. Best practices related to this setup"""

        explanation = await self._call_llm(prompt)
        
        return {
            "type": "explanation",
            "message": "Here's an explanation of the configuration:",
            "explanation": explanation,
            "can_apply": False
        }
    
    async def _handle_troubleshooting(
        self,
        message: str,
        context: AssistantContext
    ) -> Dict[str, Any]:
        """Handle troubleshooting requests"""
        
        prompt = f"""You are a network troubleshooting expert. Help diagnose this issue.

User describes: "{message}"

Current configuration context:
{json.dumps(context.current_config, indent=2) if context.current_config else "N/A"}

Provide troubleshooting steps in JSON format:
{{
    "likely_causes": [
        {{
            "cause": "description of possible cause",
            "likelihood": "high|medium|low",
            "check": "how to verify this cause"
        }}
    ],
    "diagnostic_commands": ["command1", "command2"],
    "suggested_fixes": [
        {{
            "fix": "description of fix",
            "risk": "low|medium|high",
            "steps": ["step1", "step2"]
        }}
    ],
            "explanation": "overall assessment"
}}"""

        response = await self._call_llm(prompt)
        
        try:
            data = json.loads(response)
            
            return {
                "type": "troubleshooting_guide",
                "message": f"I've analyzed the issue: {data.get('explanation')}",
                "likely_causes": data.get("likely_causes", []),
                "diagnostic_commands": data.get("diagnostic_commands", []),
                "suggested_fixes": data.get("suggested_fixes", []),
                "can_apply": False
            }
        except json.JSONDecodeError:
            return {
                "type": "troubleshooting_guide",
                "message": "Here are some general troubleshooting steps:",
                "likely_causes": [
                    {"cause": "Rule ordering issue", "likelihood": "medium", "check": "Check if more specific rules are before general rules"},
                    {"cause": "Interface misconfiguration", "likelihood": "medium", "check": "Verify interface assignments"},
                    {"cause": "NAT not configured", "likelihood": "high" if "internet" in message.lower() else "low", "check": "Check NAT rules for outbound traffic"}
                ],
                "diagnostic_commands": ["nft list ruleset", "ip route show", "ping 8.8.8.8"],
                "suggested_fixes": [],
                "can_apply": False
            }
    
    async def _handle_optimization(
        self,
        message: str,
        context: AssistantContext
    ) -> Dict[str, Any]:
        """Handle rule optimization requests"""
        
        config_summary = json.dumps(context.current_config, indent=2) if context.current_config else "[]"
        
        prompt = f"""You are a firewall optimization expert. Analyze and suggest improvements.

Current firewall rules:
{config_summary}

Analyze these rules and suggest optimizations. Consider:
1. Rule consolidation (can multiple rules be combined?)
2. Rule ordering (most specific rules should come first)
3. Performance (logging, connection tracking overhead)
4. Security gaps (missing protections)

Respond in JSON format:
{{
    "optimizations": [
        {{
            "type": "reorder|consolidate|add|remove",
            "description": "what to change",
            "benefit": "performance|security|maintainability",
            "current_rules": [1, 2],
            "suggested_rules": [{{...}}]
        }}
    ],
    "security_gaps": ["gap1", "gap2"],
    "performance_impact": "estimated improvement"
}}"""

        response = await self._call_llm(prompt)
        
        try:
            data = json.loads(response)
            
            return {
                "type": "optimization_suggestions",
                "message": f"I've analyzed your configuration and found {len(data.get('optimizations', []))} potential improvements.",
                "optimizations": data.get("optimizations", []),
                "security_gaps": data.get("security_gaps", []),
                "performance_impact": data.get("performance_impact"),
                "can_apply": True
            }
        except json.JSONDecodeError:
            return {
                "type": "optimization_suggestions",
                "message": "Here are some general optimization tips:",
                "optimizations": [
                    {
                        "type": "reorder",
                        "description": "Move most frequently matched rules to the top",
                        "benefit": "performance"
                    },
                    {
                        "type": "consolidate",
                        "description": "Combine rules with same action and similar criteria",
                        "benefit": "maintainability"
                    }
                ],
                "security_gaps": ["Consider adding rate limiting for SYN floods"],
                "performance_impact": "minor",
                "can_apply": False
            }
    
    async def _handle_report_generation(
        self,
        message: str,
        context: AssistantContext
    ) -> Dict[str, Any]:
        """Handle report generation requests"""
        
        return {
            "type": "report_generated",
            "message": "I can generate reports for your configuration. What type of report would you like?",
            "report_types": [
                {"id": "security_audit", "name": "Security Audit", "description": "Analyze rules for security issues"},
                {"id": "performance_analysis", "name": "Performance Analysis", "description": "Identify performance bottlenecks"},
                {"id": "compliance_check", "name": "Compliance Check", "description": "Check against common standards (PCI-DSS, etc.)"},
                {"id": "change_summary", "name": "Change Summary", "description": "Summary of recent configuration changes"}
            ],
            "can_apply": False
        }
    
    async def _handle_unknown(
        self,
        message: str,
        context: AssistantContext
    ) -> Dict[str, Any]:
        """Handle unknown intents"""
        
        return {
            "type": "clarification_needed",
            "message": "I'm not sure what you'd like to do. I can help you with:",
            "capabilities": [
                "🛡️ Create firewall rules (e.g., 'Block SSH from the internet')",
                "🧪 Generate test cases (e.g., 'Create tests for web server access')",
                "🔐 Set up VPN (e.g., 'Create a VPN for remote workers')",
                "📧 Configure mail (e.g., 'Set up mail for example.com')",
                "📊 Explain configurations (e.g., 'Why is port 22 blocked?')",
                "🔧 Troubleshoot issues (e.g., 'Users cant access the internet')",
                "⚡ Optimize rules (e.g., 'Clean up my firewall rules')"
            ],
            "can_apply": False
        }
    
    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM with a prompt.

        Uses the LLM provider registry when a database session is available,
        otherwise falls back to the legacy provider/model/api_key configuration.
        """
        if self.db is not None:
            from shared.llm_client import LLMClientFactory, LLMError
            try:
                return await LLMClientFactory.chat_for_use_case(
                    db=self.db,
                    use_case="assistant_chat",
                    messages=[
                        {"role": "system", "content": "You are a helpful network security assistant."},
                        {"role": "user", "content": prompt},
                    ],
                )
            except LLMError as e:
                # Return a graceful fallback so the UI doesn't crash
                return f'{{"error": "{str(e)}"}}'

        # Legacy fallback — should not be reached in normal operation
        return "{}"
    
    async def generate_natural_language_summary(
        self,
        config_type: str,
        config: Dict[str, Any]
    ) -> str:
        """Generate a human-readable summary of a configuration"""
        
        prompt = f"""Summarize this {config_type} configuration in 2-3 sentences:

{json.dumps(config, indent=2)}

Make it clear and understandable for a network administrator."""

        return await self._call_llm(prompt)
    
    async def suggest_tests_for_rule(
        self,
        rule: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate test cases for a specific firewall rule"""
        
        prompt = f"""Generate test cases to verify this firewall rule works correctly:

Rule: {json.dumps(rule, indent=2)}

Generate tests that:
1. Verify the rule matches when it should
2. Verify the rule doesn't match when it shouldn't
3. Test edge cases

Respond in JSON format with a list of test cases."""

        response = await self._call_llm(prompt)
        
        try:
            data = json.loads(response)
            return data.get("test_cases", [])
        except:
            return []


# Pre-built prompt templates for common tasks
PROMPT_TEMPLATES = {
    "firewall_rule_from_description": """
Convert this description into a firewall rule:
"{description}"

Extract: source, destination, port, protocol, action, and any special conditions.
Respond in JSON format.
""",
    
    "security_audit": """
Perform a security audit of these firewall rules:
{rules}

Identify:
1. Security vulnerabilities
2. Missing protections
3. Overly permissive rules
4. Best practice violations

Rate each issue as Critical, High, Medium, or Low priority.
""",
    
    "rule_explanation": """
Explain this firewall rule in simple terms:
{rule}

Include:
- What traffic it affects
- What action it takes
- When it applies
- Any security implications
""",
    
    "test_scenario_generation": """
Given these firewall rules:
{rules}

Generate test scenarios covering:
1. Allowed traffic that should pass
2. Blocked traffic that should be stopped
3. Edge cases and corner cases
4. Security-specific tests

Each test should include: description, packet details, expected result
"""
}


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        assistant = LLMConfigurationAssistant()
        
        context = AssistantContext(
            instance_id=1,
            user_role="admin"
        )
        
        # Test firewall rule creation
        result = await assistant.process_request(
            "Block SSH access from the internet",
            context
        )
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())
