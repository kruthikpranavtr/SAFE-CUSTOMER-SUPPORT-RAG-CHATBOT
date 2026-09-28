from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class GuardrailStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    ABSTAINED = "ABSTAINED"
    ESCALATED = "ESCALATED"
    BLOCKED = "BLOCKED"
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNABLE_TO_DETERMINE = "UNABLE_TO_DETERMINE"

class GuardrailType(str, Enum):
    PII = "PII"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    DOMAIN_VIOLATION = "DOMAIN_VIOLATION"
    RATE_LIMIT = "RATE_LIMIT"
    EVIDENCE_ONLY = "EVIDENCE_ONLY"
    EVIDENCE_CONSISTENCY = "EVIDENCE_CONSISTENCY"
    ABSTENTION = "ABSTENTION"
    CONFIDENCE = "CONFIDENCE"
    SOURCE_ATTRIBUTION = "SOURCE_ATTRIBUTION"
    HUMAN_ESCALATION = "HUMAN_ESCALATION"
    ACTION_CONFIRMATION = "ACTION_CONFIRMATION"
    CLARIFICATION = "CLARIFICATION"

class GuardrailSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class GuardrailAction(str, Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    REDACT = "REDACT"
    REJECT = "REJECT"
    ABSTAIN = "ABSTAIN"
    ESCALATE = "ESCALATE"
    BLOCK = "BLOCK"
    CONFIRM = "CONFIRM"

class GuardrailResult(BaseModel):
    passed: bool
    guardrail_type: GuardrailType
    action: GuardrailAction
    severity: GuardrailSeverity = GuardrailSeverity.INFO
    reason: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

class ClaimVerification(BaseModel):
    claim: str
    is_supported: bool
    is_contradicted: bool = False
    evidence_snippet: Optional[str] = None
    similarity: float = 0.0

class StructuredSource(BaseModel):
    document_name: str
    page_number: int = 1
    section: Optional[str] = "General"
    snippet: str
    source_id: str
    similarity_score: float = 0.0
