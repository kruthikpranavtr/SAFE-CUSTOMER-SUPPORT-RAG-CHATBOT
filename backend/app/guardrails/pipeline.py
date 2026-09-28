import uuid
import re
from typing import Dict, Any, Optional, List
from backend.app.guardrails.base import (
    GuardrailStatus, 
    ConfidenceLevel, 
    GuardrailType, 
    GuardrailSeverity, 
    GuardrailAction, 
    GuardrailResult
)
from backend.app.guardrails.input_guard import PIIGuardrail, DomainGuardrail, RateLimitGuardrail
from backend.app.guardrails.prompt_guard import PromptInjectionGuardrail
from backend.app.guardrails.output_guard import (
    EvidenceOnlyGuardrail, 
    AbstentionGuardrail, 
    SourceAttributionGuardrail, 
    EvidenceConsistencyGuardrail, 
    ConfidenceGuardrail
)
from backend.app.guardrails.safety_guard import HumanEscalationGuardrail, ActionConfirmationGuardrail
from backend.app.guardrails.audit_logger import audit_logger
from backend.app.rag.vector_store import vector_store
from backend.app.rag.llm import llm_service
from backend.app.utils.config import settings

class SafeSupportGuardrails:
    """
    Central orchestration engine implementing the full production guardrail pipeline:
    INPUT GUARD -> PROMPT GUARD -> RAG RETRIEVAL -> LLM -> OUTPUT GUARD -> AUDIT LOGGING.
    """
    def __init__(self):
        self.vector_store = vector_store
        self.llm = llm_service

    async def process_chat(
        self, 
        query: str, 
        session_id: Optional[str] = None, 
        user_id: Optional[str] = "demo-user",
        client_ip: Optional[str] = "127.0.0.1",
        language: str = "en"
    ) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        pii_warning = None
        guardrail_flags = []

        # ---------------------------------------------------------
        # STEP 1: INPUT GUARD - RATE LIMITING
        # ---------------------------------------------------------
        client_key = f"{user_id}_{client_ip}"
        rate_res = RateLimitGuardrail.evaluate(client_key)
        if not rate_res.passed:
            audit_logger.log_event(
                guardrail_type=GuardrailType.RATE_LIMIT,
                action=GuardrailAction.BLOCK,
                severity=GuardrailSeverity.HIGH,
                reason=rate_res.reason or "Rate limit exceeded",
                request_id=request_id,
                session_id=session_id,
                user_id=user_id,
                details=rate_res.details
            )
            return {
                "answer": "Too many requests. Please wait a moment before trying again.",
                "status": GuardrailStatus.BLOCKED,
                "confidence": ConfidenceLevel.UNABLE_TO_DETERMINE,
                "sources": [],
                "evidence_status": "BLOCKED",
                "requires_human": False,
                "verification_required": False,
                "pii_warning": None,
                "action_confirmation": None,
                "guardrail_flags": ["RATE_LIMIT_BLOCKED"]
            }

        # ---------------------------------------------------------
        # STEP 2: INPUT GUARD - PII DETECTION & REDACTION
        # ---------------------------------------------------------
        has_pii, clean_query, pii_types, pii_msg = PIIGuardrail.evaluate(query)
        if has_pii:
            pii_warning = pii_msg
            guardrail_flags.append(f"PII_DETECTED_{'_'.join(pii_types)}")
            audit_logger.log_event(
                guardrail_type=GuardrailType.PII,
                action=GuardrailAction.WARN,
                severity=GuardrailSeverity.MEDIUM,
                reason=f"PII types detected: {pii_types}. Redacted from LLM input.",
                request_id=request_id,
                session_id=session_id,
                user_id=user_id,
                details={"detected_types": pii_types}
            )

        # ---------------------------------------------------------
        # STEP 3: INPUT GUARD - ACTION CONFIRMATION (INFORM -> CONFIRM -> ACT)
        # ---------------------------------------------------------
        is_action, action_info = ActionConfirmationGuardrail.check_action_required(clean_query)
        if is_action:
            audit_logger.log_event(
                guardrail_type=GuardrailType.ACTION_CONFIRMATION,
                action=GuardrailAction.CONFIRM,
                severity=GuardrailSeverity.MEDIUM,
                reason=f"High-impact action '{action_info['action_name']}' requires user confirmation.",
                request_id=request_id,
                session_id=session_id,
                user_id=user_id,
                details=action_info
            )
            return {
                "answer": (
                    f"⚠️ **Action Confirmation Required**\n\n"
                    f"{action_info['confirmation_prompt']}\n\n"
                    f"Target: `{action_info['target_identifier']}`"
                ),
                "status": GuardrailStatus.CONFIRMATION_REQUIRED,
                "confidence": ConfidenceLevel.HIGH,
                "sources": [],
                "evidence_status": "ACTION_PENDING",
                "requires_human": False,
                "verification_required": True,
                "pii_warning": pii_warning,
                "action_confirmation": action_info,
                "guardrail_flags": guardrail_flags + ["ACTION_CONFIRMATION_REQUIRED"]
            }

        # ---------------------------------------------------------
        # STEP 4: INPUT GUARD - DOMAIN RESTRICTION
        # ---------------------------------------------------------
        domain_res = DomainGuardrail.evaluate(clean_query, language=language)
        if not domain_res.passed:
            audit_logger.log_event(
                guardrail_type=GuardrailType.DOMAIN_VIOLATION,
                action=GuardrailAction.REJECT,
                severity=GuardrailSeverity.LOW,
                reason=domain_res.reason or "Out of domain question",
                request_id=request_id,
                session_id=session_id,
                user_id=user_id,
                details=domain_res.details
            )
            return {
                "answer": domain_res.details.get("response", "I'm designed to help with customer-support questions."),
                "status": GuardrailStatus.BLOCKED,
                "confidence": ConfidenceLevel.UNABLE_TO_DETERMINE,
                "sources": [],
                "evidence_status": "OUT_OF_DOMAIN",
                "requires_human": False,
                "verification_required": False,
                "pii_warning": pii_warning,
                "action_confirmation": None,
                "guardrail_flags": guardrail_flags + ["OUT_OF_DOMAIN"]
            }

        # ---------------------------------------------------------
        # STEP 5: PROMPT GUARD - PROMPT INJECTION DETECTION
        # ---------------------------------------------------------
        injection_res = PromptInjectionGuardrail.evaluate_query(clean_query)
        if not injection_res.passed:
            audit_logger.log_event(
                guardrail_type=GuardrailType.PROMPT_INJECTION,
                action=GuardrailAction.BLOCK,
                severity=GuardrailSeverity.CRITICAL,
                reason=injection_res.reason or "Prompt injection detected",
                request_id=request_id,
                session_id=session_id,
                user_id=user_id,
                details=injection_res.details
            )
            return {
                "answer": "Security Notice: Your query contained instructions attempting to alter system guardrails. I can only assist with verified customer-support questions.",
                "status": GuardrailStatus.BLOCKED,
                "confidence": ConfidenceLevel.UNABLE_TO_DETERMINE,
                "sources": [],
                "evidence_status": "PROMPT_INJECTION_BLOCKED",
                "requires_human": False,
                "verification_required": False,
                "pii_warning": pii_warning,
                "action_confirmation": None,
                "guardrail_flags": guardrail_flags + ["PROMPT_INJECTION_BLOCKED"]
            }

        # ---------------------------------------------------------
        # STEP 6: RAG RETRIEVAL & UNTRUSTED DOCUMENT SANITIZATION
        # ---------------------------------------------------------
        candidate_chunks = self.vector_store.query(clean_query, top_k=settings.TOP_K_CHUNKS)

        # Sanitize retrieved chunks so document text cannot override system prompts
        for c in candidate_chunks:
            c["content_snippet"] = PromptInjectionGuardrail.sanitize_retrieved_chunk(c["content_snippet"])

        # ---------------------------------------------------------
        # STEP 7: OUTPUT GUARD - EVIDENCE-ONLY CHECK
        # ---------------------------------------------------------
        evidence_res = EvidenceOnlyGuardrail.evaluate(clean_query, candidate_chunks)
        if not evidence_res.passed:
            abstention = AbstentionGuardrail.create_abstention(clean_query, evidence_res.reason or "Insufficient evidence", language)
            audit_logger.log_event(
                guardrail_type=GuardrailType.ABSTENTION,
                action=GuardrailAction.ABSTAIN,
                severity=GuardrailSeverity.MEDIUM,
                reason=evidence_res.reason or "Insufficient evidence",
                request_id=request_id,
                session_id=session_id,
                user_id=user_id,
                details={"top_score": evidence_res.details.get("top_score", 0.0)}
            )
            return {
                **abstention,
                "pii_warning": pii_warning,
                "action_confirmation": None,
                "guardrail_flags": guardrail_flags + ["ABSTAINED_INSUFFICIENT_EVIDENCE"]
            }

        # ---------------------------------------------------------
        # STEP 8: LLM RESPONSE GENERATION
        # ---------------------------------------------------------
        top_chunk = candidate_chunks[0]
        raw_answer = await self.llm.generate_response(clean_query, candidate_chunks, "High", language)

        # ---------------------------------------------------------
        # STEP 9: OUTPUT GUARD - ANSWER-EVIDENCE CONSISTENCY CHECK
        # ---------------------------------------------------------
        consistency_status, claim_verifs, consistency_reason = EvidenceConsistencyGuardrail.verify_consistency(
            raw_answer, candidate_chunks
        )

        # If answer is contradictory or unsupported, trigger abstention
        if consistency_status in [GuardrailStatus.CONTRADICTED, GuardrailStatus.UNSUPPORTED]:
            audit_logger.log_event(
                guardrail_type=GuardrailType.EVIDENCE_CONSISTENCY,
                action=GuardrailAction.REJECT,
                severity=GuardrailSeverity.HIGH,
                reason=f"Evidence consistency check failed: {consistency_reason}",
                request_id=request_id,
                session_id=session_id,
                user_id=user_id,
                details={
                    "consistency_status": consistency_status.value,
                    "claims": [c.model_dump() for c in claim_verifs]
                }
            )
            abstention = AbstentionGuardrail.create_abstention(
                clean_query, 
                f"Generated response conflicted with verified company documents: {consistency_reason}",
                language
            )
            return {
                **abstention,
                "status": consistency_status,
                "pii_warning": pii_warning,
                "action_confirmation": None,
                "guardrail_flags": guardrail_flags + [f"CONSISTENCY_{consistency_status.value}"]
            }

        # ---------------------------------------------------------
        # STEP 10: CONFIDENCE & SOURCE ATTRIBUTION
        # ---------------------------------------------------------
        top_score = float(top_chunk.get("similarity_score", 0.5))
        distinct_coverage = 0.8 if len(candidate_chunks) >= 2 else 0.5
        confidence = ConfidenceGuardrail.calculate(top_score, distinct_coverage, consistency_status)

        sources = SourceAttributionGuardrail.build_sources(candidate_chunks)

        # Check if human escalation should be offered
        should_escalate, esc_reason = HumanEscalationGuardrail.should_escalate(
            clean_query, confidence.value, consistency_status.value
        )
        if should_escalate:
            audit_logger.log_event(
                guardrail_type=GuardrailType.HUMAN_ESCALATION,
                action=GuardrailAction.ESCALATE,
                severity=GuardrailSeverity.INFO,
                reason=esc_reason,
                request_id=request_id,
                session_id=session_id,
                user_id=user_id,
                details={"confidence": confidence.value, "consistency": consistency_status.value}
            )

        verification_notice = "⚠️ AI-generated information. Please review the cited source before making an important decision."

        return {
            "answer": raw_answer,
            "status": consistency_status,
            "confidence": confidence,
            "sources": sources,
            "evidence_status": consistency_status.value,
            "requires_human": should_escalate,
            "escalation_reason": esc_reason if should_escalate else None,
            "verification_required": True,
            "verification_notice": verification_notice,
            "pii_warning": pii_warning,
            "action_confirmation": None,
            "retrieval_score": top_score,
            "guardrail_flags": guardrail_flags + ["GUARDRAILS_PASSED"]
        }

guardrails_pipeline = SafeSupportGuardrails()
