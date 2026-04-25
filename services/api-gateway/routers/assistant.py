from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from shared.database import get_db
from shared.security import require_auth, require_admin
from shared.schemas import LLMConfig
from shared.models import LLMUseCaseConfig
from shared.llm_assistant import (
    LLMConfigurationAssistant, AssistantContext,
    AssistantIntent
)

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================

class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    instance_id: Optional[int] = None
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    type: str  # firewall_rule_suggestion, test_cases_generated, explanation, etc.
    message: str
    data: Optional[Dict[str, Any]] = None
    can_apply: bool = False
    follow_up_questions: Optional[List[str]] = None


class RuleSuggestionRequest(BaseModel):
    description: str
    instance_id: Optional[int] = None


class RuleSuggestionResponse(BaseModel):
    rule: Dict[str, Any]
    explanation: str
    security_notes: str
    suggested_tests: List[Dict[str, Any]]


class TestGenerationRequest(BaseModel):
    description: str
    rules: Optional[List[Dict[str, Any]]] = None
    instance_id: Optional[int] = None


class TestGenerationResponse(BaseModel):
    test_cases: List[Dict[str, Any]]
    explanation: str
    coverage_assessment: str


class ConfigExplanationRequest(BaseModel):
    config_type: str  # firewall, vpn, mail, etc.
    config: Dict[str, Any]
    question: Optional[str] = None


class SecurityAuditRequest(BaseModel):
    rules: List[Dict[str, Any]]
    standard: Optional[str] = None  # pci-dss, iso27001, etc.


class SecurityAuditResponse(BaseModel):
    findings: List[Dict[str, Any]]
    risk_score: int  # 0-100
    recommendations: List[str]
    compliance_status: Dict[str, str]


# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Main chat endpoint for the LLM assistant.

    Handles natural language requests for:
    - Creating firewall rules
    - Generating test cases
    - Setting up VPN
    - Configuring mail domains
    - Explaining configurations
    - Troubleshooting issues
    """

    # Initialize assistant with database session for provider registry lookup
    assistant = LLMConfigurationAssistant(db=db)

    # Build context
    context = AssistantContext(
        instance_id=request.instance_id,
        current_config=request.context,
        user_role="admin"  # Would get from user lookup
    )

    # Process the request
    result = await assistant.process_request(request.message, context)
    
    # Convert to response format
    response = ChatResponse(
        type=result.get("type", "unknown"),
        message=result.get("message", ""),
        can_apply=result.get("can_apply", False)
    )
    
    # Include data based on type
    if result.get("type") == "firewall_rule_suggestion":
        response.data = {
            "rule": result.get("rule"),
            "explanation": result.get("explanation"),
            "security_notes": result.get("security_notes")
        }
        
        # Generate suggested tests for this rule
        suggested_tests = await assistant.suggest_tests_for_rule(result.get("rule", {}))
        response.data["suggested_tests"] = suggested_tests
        
    elif result.get("type") == "test_cases_generated":
        response.data = {
            "test_cases": result.get("test_cases", []),
            "explanation": result.get("explanation"),
            "coverage_assessment": result.get("coverage_assessment")
        }
        
    elif result.get("type") == "vpn_config_suggestion":
        response.data = {
            "recommendation": result.get("recommendation"),
            "configuration": result.get("configuration"),
            "security_settings": result.get("security_settings")
        }
        
    elif result.get("type") == "mail_setup_suggestion":
        response.data = {
            "domain_config": result.get("domain_config"),
            "dns_records": result.get("dns_records"),
            "deliverability_tips": result.get("deliverability_tips")
        }
        
    elif result.get("type") == "explanation":
        response.data = {
            "explanation": result.get("explanation")
        }
        
    elif result.get("type") == "troubleshooting_guide":
        response.data = {
            "likely_causes": result.get("likely_causes", []),
            "diagnostic_commands": result.get("diagnostic_commands", []),
            "suggested_fixes": result.get("suggested_fixes", [])
        }
        
    elif result.get("type") == "optimization_suggestions":
        response.data = {
            "optimizations": result.get("optimizations", []),
            "security_gaps": result.get("security_gaps", []),
            "performance_impact": result.get("performance_impact")
        }
        
    elif result.get("type") == "clarification_needed":
        response.follow_up_questions = result.get("questions") or result.get("capabilities", [])
    
    return response


@router.post("/suggest-firewall-rule", response_model=RuleSuggestionResponse)
async def suggest_firewall_rule(
    request: RuleSuggestionRequest,
    user_id: int = Depends(require_auth)
):
    """
    Get a firewall rule suggestion from a natural language description.
    
    Example: "Allow web server access from anywhere"
    """
    
    assistant = LLMConfigurationAssistant()
    context = AssistantContext(instance_id=request.instance_id, user_role="admin")
    
    result = await assistant.process_request(
        f"Create firewall rule: {request.description}",
        context
    )
    
    if result.get("type") != "firewall_rule_suggestion":
        raise HTTPException(status_code=400, detail="Could not generate rule from description")
    
    # Generate tests for the suggested rule
    suggested_tests = await assistant.suggest_tests_for_rule(result.get("rule", {}))
    
    return RuleSuggestionResponse(
        rule=result.get("rule", {}),
        explanation=result.get("explanation", ""),
        security_notes=result.get("security_notes", ""),
        suggested_tests=suggested_tests
    )


@router.post("/generate-tests", response_model=TestGenerationResponse)
async def generate_tests(
    request: TestGenerationRequest,
    user_id: int = Depends(require_auth)
):
    """
    Generate test cases based on a description.
    
    Example: "Test that web traffic works but SSH is blocked from outside"
    """
    
    assistant = LLMConfigurationAssistant()
    context = AssistantContext(
        instance_id=request.instance_id,
        current_config={"rules": request.rules} if request.rules else None,
        user_role="admin"
    )
    
    result = await assistant.process_request(
        f"Generate test cases: {request.description}",
        context
    )
    
    if result.get("type") != "test_cases_generated":
        raise HTTPException(status_code=400, detail="Could not generate tests")
    
    return TestGenerationResponse(
        test_cases=result.get("test_cases", []),
        explanation=result.get("explanation", ""),
        coverage_assessment=result.get("coverage_assessment", "")
    )


@router.post("/explain-configuration")
async def explain_configuration(
    request: ConfigExplanationRequest,
    user_id: int = Depends(require_auth)
):
    """
    Get a natural language explanation of a configuration.
    """
    
    assistant = LLMConfigurationAssistant()
    context = AssistantContext(
        current_config=request.config,
        user_role="admin"
    )
    
    question = request.question or "Explain this configuration"
    result = await assistant.process_request(question, context)
    
    return {
        "explanation": result.get("explanation", ""),
        "configuration_summary": await assistant.generate_natural_language_summary(
            request.config_type,
            request.config
        )
    }


@router.post("/security-audit", response_model=SecurityAuditResponse)
async def perform_security_audit(
    request: SecurityAuditRequest,
    user_id: int = Depends(require_admin)
):
    """
    Perform a security audit on firewall rules.
    
    Analyzes rules for security issues and compliance with standards.
    """
    
    assistant = LLMConfigurationAssistant()
    
    # Use the optimization handler with security focus
    context = AssistantContext(
        current_config={"rules": request.rules},
        user_role="admin"
    )
    
    result = await assistant._handle_optimization(
        f"Security audit for {request.standard or 'general'} compliance",
        context
    )
    
    # Calculate risk score based on findings
    security_gaps = result.get("security_gaps", [])
    risk_score = max(0, 100 - len(security_gaps) * 10)
    
    # Map gaps to findings
    findings = []
    for gap in security_gaps:
        findings.append({
            "severity": "high" if "critical" in gap.lower() else "medium",
            "category": "security",
            "description": gap,
            "affected_rules": [],
            "remediation": "Review and implement appropriate protections"
        })
    
    return SecurityAuditResponse(
        findings=findings,
        risk_score=risk_score,
        recommendations=result.get("optimizations", []),
        compliance_status={
            request.standard or "general": "compliant" if risk_score > 80 else "needs_improvement"
        }
    )


@router.post("/troubleshoot")
async def troubleshoot_issue(
    description: str,
    instance_id: Optional[int] = None,
    current_config: Optional[Dict] = None,
    user_id: int = Depends(require_auth)
):
    """
    Get troubleshooting assistance for a network/firewall issue.
    """
    
    assistant = LLMConfigurationAssistant()
    context = AssistantContext(
        instance_id=instance_id,
        current_config=current_config,
        user_role="admin"
    )
    
    result = await assistant.process_request(
        f"Troubleshoot: {description}",
        context
    )
    
    return result


# ============================================================================
# CONVERSATION MANAGEMENT
# ============================================================================

@router.get("/conversations")
async def list_conversations(
    user_id: int = Depends(require_auth)
):
    """List user's past conversations with the assistant"""
    # Would fetch from database
    return {
        "conversations": [
            {
                "id": "conv-001",
                "title": "Firewall rules for web server",
                "last_message": "2 hours ago",
                "message_count": 12
            }
        ]
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user_id: int = Depends(require_auth)
):
    """Get a specific conversation history"""
    # Would fetch from database
    return {
        "id": conversation_id,
        "messages": []
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user_id: int = Depends(require_auth)
):
    """Delete a conversation"""
    return {"status": "deleted"}


# ============================================================================
# ASSISTANT CAPABILITIES
# ============================================================================

@router.get("/capabilities")
async def get_assistant_capabilities(
    user_id: int = Depends(require_auth)
):
    """Get list of things the assistant can help with"""
    
    return {
        "categories": [
            {
                "id": "firewall",
                "name": "Firewall Rules",
                "icon": "🛡️",
                "description": "Create, modify, and optimize firewall rules",
                "examples": [
                    "Block SSH from the internet",
                    "Allow HTTP and HTTPS to web server",
                    "Create rule for port forwarding"
                ]
            },
            {
                "id": "testing",
                "name": "Test Generation",
                "icon": "🧪",
                "description": "Generate test cases for your configurations",
                "examples": [
                    "Test web server access",
                    "Verify SSH is blocked from WAN",
                    "Create comprehensive test suite"
                ]
            },
            {
                "id": "vpn",
                "name": "VPN Setup",
                "icon": "🔐",
                "description": "Configure VPN servers and clients",
                "examples": [
                    "Set up WireGuard for remote workers",
                    "Create site-to-site VPN",
                    "Configure IPsec for mobile devices"
                ]
            },
            {
                "id": "mail",
                "name": "Mail Configuration",
                "icon": "📧",
                "description": "Configure email domains and security",
                "examples": [
                    "Set up mail for my domain",
                    "Configure DKIM signing",
                    "Enable spam filtering"
                ]
            },
            {
                "id": "explanation",
                "name": "Explain & Learn",
                "icon": "📚",
                "description": "Get explanations of configurations",
                "examples": [
                    "Why is this rule here?",
                    "Explain my firewall setup",
                    "What does DMARC do?"
                ]
            },
            {
                "id": "troubleshoot",
                "name": "Troubleshooting",
                "icon": "🔧",
                "description": "Diagnose and fix issues",
                "examples": [
                    "Users can't access internet",
                    "VPN not connecting",
                    "Mail delivery failing"
                ]
            },
            {
                "id": "optimization",
                "name": "Optimization",
                "icon": "⚡",
                "description": "Improve performance and security",
                "examples": [
                    "Clean up my firewall rules",
                    "Optimize for better performance",
                    "Security audit"
                ]
            }
        ],
        "tips": [
            "Be specific about IPs, ports, and protocols",
            "Mention the direction of traffic (LAN to WAN, etc.)",
            "Ask for test cases to verify your rules work",
            "Use the simulator to test before applying"
        ]
    }


@router.get("/config", response_model=LLMConfig)
async def get_llm_config(
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get current LLM configuration (assistant_chat use case)."""
    result = await db.execute(
        select(LLMUseCaseConfig).where(LLMUseCaseConfig.use_case == "assistant_chat")
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="LLM configuration not found")

    return LLMConfig(
        provider=config.provider.provider_type if config.provider else "openai",
        model=config.model.name if config.model else "gpt-4",
        api_key=config.provider.api_key if config.provider else None,
        api_base=config.provider.base_url if config.provider else None,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        system_prompt=config.system_prompt or "You are a helpful network security assistant.",
    )


@router.post("/config", response_model=LLMConfig)
async def update_llm_config(
    config: LLMConfig,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update LLM configuration (admin only) — modifies the assistant_chat use case."""
    result = await db.execute(
        select(LLMUseCaseConfig).where(LLMUseCaseConfig.use_case == "assistant_chat")
    )
    use_case = result.scalar_one_or_none()
    if not use_case:
        raise HTTPException(status_code=404, detail="LLM use-case config not found")

    use_case.temperature = config.temperature
    use_case.max_tokens = config.max_tokens
    use_case.system_prompt = config.system_prompt
    await db.commit()
    await db.refresh(use_case)

    return LLMConfig(
        provider=use_case.provider.provider_type if use_case.provider else "openai",
        model=use_case.model.name if use_case.model else "gpt-4",
        api_key=use_case.provider.api_key if use_case.provider else None,
        api_base=use_case.provider.base_url if use_case.provider else None,
        temperature=use_case.temperature,
        max_tokens=use_case.max_tokens,
        system_prompt=use_case.system_prompt or "",
    )
