import re
from typing import Dict, Any, Tuple, Optional, List
from backend.app.guardrails.base import (
    GuardrailStatus, 
    GuardrailType, 
    GuardrailSeverity, 
    GuardrailAction, 
    GuardrailResult
)

HUMAN_REQUEST_PATTERNS = [
    r'\b(?:talk\s+to|speak\s+with|transfer\s+me\s+to|connect\s+me\s+to|contact)\s+(?:a\s+)?(?:human|person|agent|representative|supervisor)\b',
    r'\b(?:i\s+want\s+a\s+human|human\s+support|live\s+agent|real\s+person)\b',
    r'\b(?:dispute|lawyer|legal\s+action|fraud|file\s+a\s+complaint)\b',
    r'\b(?:மனித\s+ஆதரவு|நேரடி\s+உதவி)\b'
]

ACTION_PATTERNS = [
    (r'\b(?:cancel\s+(?:my\s+)?order\s*(?:#?\s*([a-zA-Z0-9_\-]+))?)\b', "Order Cancellation"),
    (r'\b(?:delete\s+(?:my\s+)?account)\b', "Account Deletion"),
    (r'\b(?:chargeback|refund\s+(?:my\s+)?credit\s+card)\b', "Direct Chargeback"),
    (r'\b(?:change\s+(?:my\s+)?shipping\s+address\s*(?:to\s+(.+))?)\b', "Address Modification")
]

class HumanEscalationGuardrail:
    """
    GUARDRAIL 9 — HUMAN ESCALATION
    Evaluates whether the conversation should be transitioned to a human agent.
    Triggers on:
    - User explicit request for human
    - Legal/billing disputes
    - Abstention / Missing evidence
    - Low confidence / Contradictory evidence
    """
    @classmethod
    def should_escalate(
        cls, 
        query: str, 
        confidence: str, 
        evidence_status: str, 
        user_disputes: bool = False
    ) -> Tuple[bool, str]:
        query_lower = query.lower()
        for p in HUMAN_REQUEST_PATTERNS:
            if re.search(p, query_lower):
                return True, "Customer explicitly requested human agent assistance."

        if user_disputes:
            return True, "Customer disputed the accuracy of the AI-generated answer."

        if evidence_status in ["UNSUPPORTED", "CONTRADICTED"]:
            return True, "Evidence was unverified or contradictory. Human intervention required."

        if confidence in ["LOW", "UNABLE_TO_DETERMINE", "Low", "Unable to determine"]:
            return True, "AI confidence is low or unable to determine."

        return False, ""

class ActionConfirmationGuardrail:
    """
    GUARDRAIL 12 — ACTION CONFIRMATION
    Implements: INFORM → CONFIRM → ACT
    Ensures that high-impact operations (order cancellation, account deletion, address update)
    are NEVER executed silently without explicit interactive user confirmation.
    """
    @classmethod
    def check_action_required(cls, query: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        query_lower = query.lower()
        for pattern, action_name in ACTION_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                param = match.group(1) if match.lastindex and match.lastindex >= 1 else None
                action_info = {
                    "action_name": action_name,
                    "target_identifier": param or "current order/account",
                    "confirmation_prompt": (
                        f"You are about to initiate '{action_name}'"
                        f"{f' for {param}' if param else ''}. "
                        f"Please confirm to proceed."
                    ),
                    "requires_confirmation": True
                }
                return True, action_info

        return False, None
