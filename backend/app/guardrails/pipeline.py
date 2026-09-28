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

# Conversation Engine Imports
from backend.app.conversation.intent_detector import IntentDetector, ConversationIntent
from backend.app.conversation.memory_manager import ConversationMemory
from backend.app.conversation.query_rewriter import ContextualQueryRewriter
from backend.app.conversation.clarification_engine import ClarificationEngine
from backend.app.conversation.suggestions_engine import SuggestionsEngine
from backend.app.conversation.action_engine import ActionEngine

class SafeSupportGuardrails:
    """
    Central orchestration engine implementing the full conversational guardrail pipeline:
    INPUT GUARD -> PROMPT GUARD -> CONVERSATION MEMORY -> INTENT -> 
    CLARIFICATION -> CONTEXTUAL RAG -> LLM -> OUTPUT GUARD -> AUDIT LOGGING.
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
                "intent": ConversationIntent.UNKNOWN.value,
                "suggestions": ["Try again in a moment"],
                "rewritten_query": query,
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
        # STEP 3: ACTION CONFIRMATION & EXECUTION (INFORM -> CONFIRM -> ACT)
        # ---------------------------------------------------------
        clean_lower = clean_query.lower().strip()

        # Check if user is confirming a pending action
        is_confirm = any(kw in clean_lower for kw in [
            "confirm", "proceed", "yes, cancel", "yes, please cancel", "yes, confirm", "yes i confirm"
        ])
        if is_confirm and ("cancel" in clean_lower or "yes" in clean_lower or "order" in clean_lower or clean_lower in ["confirm", "proceed"]):
            # Extract order id if specified in confirmation, else fallback to Nova-9876
            order_id = "Nova-9876"
            match = re.search(r'#?(?:nova|order)?\s*[-#]?\s*(\d{4,6}|[a-zA-Z0-9_\-]+)', clean_query, re.IGNORECASE)
            if match and len(match.group(1)) >= 4:
                order_id = match.group(0).replace(" ", "")
            exec_res = ActionEngine.execute_cancellation(order_id)
            audit_logger.log_event(
                guardrail_type=GuardrailType.ACTION_CONFIRMATION,
                action=GuardrailAction.ALLOW if exec_res["success"] else GuardrailAction.REJECT,
                severity=GuardrailSeverity.MEDIUM,
                reason="User confirmed action execution.",
                request_id=request_id,
                session_id=session_id,
                user_id=user_id,
                details=exec_res
            )
            return {
                "answer": exec_res["message"],
                "status": GuardrailStatus.SUPPORTED if exec_res["success"] else GuardrailStatus.ABSTAINED,
                "confidence": ConfidenceLevel.HIGH,
                "sources": [],
                "evidence_status": "ACTION_EXECUTED",
                "requires_human": not exec_res["success"],
                "verification_required": True,
                "verification_notice": "⚠️ Action result verified in store database.",
                "pii_warning": pii_warning,
                "action_confirmation": None,
                "intent": ConversationIntent.CANCELLATION.value,
                "suggestions": ["Check order refund timeline", "What is your return policy?", "Speak with human support"],
                "rewritten_query": clean_query,
                "guardrail_flags": guardrail_flags + ["ACTION_EXECUTED"]
            }

        # Check order status lookup
        is_order_lookup, order_msg = ActionEngine.handle_order_lookup(clean_query)
        if is_order_lookup and "cancel" not in clean_lower:
            suggestions = [
                "Cancel this order",
                "What is your return policy?",
                "Contact human support"
            ]
            return {
                "answer": order_msg,
                "status": GuardrailStatus.SUPPORTED,
                "confidence": ConfidenceLevel.HIGH,
                "sources": [],
                "evidence_status": "ORDER_STATUS_VERIFIED",
                "requires_human": False,
                "verification_required": True,
                "verification_notice": "⚠️ Order details retrieved from verified store records.",
                "pii_warning": pii_warning,
                "action_confirmation": None,
                "intent": ConversationIntent.ORDER_STATUS.value,
                "suggestions": suggestions,
                "rewritten_query": clean_query,
                "guardrail_flags": guardrail_flags + ["ORDER_STATUS_LOOKUP"]
            }

        # Check if high-impact action requires confirmation
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
                "verification_notice": "⚠️ High-impact action halted until verified by customer.",
                "pii_warning": pii_warning,
                "action_confirmation": action_info,
                "intent": ConversationIntent.CANCELLATION.value,
                "suggestions": ["Confirm Order Cancellation", "Keep my order", "Speak with human agent"],
                "rewritten_query": clean_query,
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
                "intent": ConversationIntent.OUT_OF_SCOPE.value,
                "suggestions": ["Speak with a human agent", "How long do I have to request a refund?", "What does the warranty cover?"],
                "rewritten_query": clean_query,
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
                "intent": ConversationIntent.OUT_OF_SCOPE.value,
                "suggestions": ["What is your refund policy?", "How long does shipping take?", "Speak with human support"],
                "rewritten_query": clean_query,
                "guardrail_flags": guardrail_flags + ["PROMPT_INJECTION_BLOCKED"]
            }

        # ---------------------------------------------------------
        # STEP 6: CONVERSATION MEMORY & INTENT DETECTION
        # ---------------------------------------------------------
        recent_messages = ConversationMemory.get_recent_messages(session_id, limit=6) if session_id else []
        session_ctx = ConversationMemory.get_session_context(session_id) if session_id else {}
        active_topic = session_ctx.get("active_topic")
        last_intent = session_ctx.get("last_intent")

        intent, intent_conf = IntentDetector.detect_intent(
            clean_query, 
            previous_intent=last_intent
        )

        # ---------------------------------------------------------
        # STEP 6B: NATURAL GREETINGS (SECTION 36)
        # ---------------------------------------------------------
        if intent == ConversationIntent.GREETING:
            greeting_msg = (
                "வணக்கம்! 👋 நான் சேஃப் சப்போர்ட் AI வாடிக்கையாளர் உதவியாளர். உங்களுக்கு இன்று எவ்வாறு உதவ முடியும்? "
                "ரீஃபண்ட், டெலிவரி, ரிட்டர்ன் அல்லது வாரண்டி குறித்து கேட்கலாம்."
                if language == "ta" else
                "Hi! 👋 I'm the SafeSupport AI customer assistant. How can I help you today? "
                "You can ask me about our refund policy, delivery timelines, return procedures, product warranty, or order cancellations."
            )
            suggestions = SuggestionsEngine.get_suggestions(ConversationIntent.GREETING, language=language)
            if session_id:
                ConversationMemory.update_session_context(session_id, last_intent="GREETING")

            return {
                "answer": greeting_msg,
                "status": GuardrailStatus.SUPPORTED,
                "confidence": ConfidenceLevel.HIGH,
                "sources": [],
                "evidence_status": "SUPPORTED",
                "requires_human": False,
                "verification_required": False,
                "verification_notice": None,
                "pii_warning": pii_warning,
                "action_confirmation": None,
                "intent": intent.value,
                "suggestions": suggestions,
                "rewritten_query": clean_query,
                "guardrail_flags": guardrail_flags + ["CONVERSATION_GREETING"]
            }

        # ---------------------------------------------------------
        # STEP 6C: CLARIFICATION GUARDRAIL (SECTION 37)
        # ---------------------------------------------------------
        is_ambiguous, clar_prompt, clar_suggestions = ClarificationEngine.evaluate(clean_query, active_topic=active_topic)
        if is_ambiguous and clar_prompt:
            audit_logger.log_event(
                guardrail_type=GuardrailType.CLARIFICATION,
                action=GuardrailAction.WARN,
                severity=GuardrailSeverity.INFO,
                reason="Ambiguous user input detected. Asking clarification without guessing.",
                request_id=request_id,
                session_id=session_id,
                user_id=user_id,
                details={"original_query": clean_query}
            )
            if session_id:
                ConversationMemory.update_session_context(session_id, last_intent="CLARIFICATION")

            return {
                "answer": clar_prompt,
                "status": GuardrailStatus.CLARIFICATION_REQUIRED,
                "confidence": ConfidenceLevel.UNABLE_TO_DETERMINE,
                "sources": [],
                "evidence_status": "CLARIFICATION_REQUIRED",
                "requires_human": False,
                "verification_required": False,
                "verification_notice": "⚠️ Please clarify your request so I can look up the exact verified policy.",
                "pii_warning": pii_warning,
                "action_confirmation": None,
                "intent": intent.value,
                "suggestions": clar_suggestions,
                "rewritten_query": clean_query,
                "guardrail_flags": guardrail_flags + ["CLARIFICATION_REQUIRED"]
            }

        # ---------------------------------------------------------
        # STEP 7: SMART RAG RETRIEVAL & QUERY REWRITING (SECTION 38)
        # ---------------------------------------------------------
        rewritten_query = ContextualQueryRewriter.rewrite(clean_query, recent_messages, active_topic=active_topic)
        candidate_chunks = self.vector_store.query(rewritten_query, top_k=settings.TOP_K_CHUNKS)

        # Sanitize retrieved chunks so document text cannot override system prompts
        for c in candidate_chunks:
            c["content_snippet"] = PromptInjectionGuardrail.sanitize_retrieved_chunk(c["content_snippet"])

        # ---------------------------------------------------------
        # STEP 8: OUTPUT GUARD - EVIDENCE-ONLY CHECK
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
            suggestions = SuggestionsEngine.get_suggestions(intent, requires_human=True, status="ABSTAINED", language=language)
            return {
                **abstention,
                "pii_warning": pii_warning,
                "action_confirmation": None,
                "intent": intent.value,
                "suggestions": suggestions,
                "rewritten_query": rewritten_query,
                "guardrail_flags": guardrail_flags + ["ABSTAINED_INSUFFICIENT_EVIDENCE"]
            }

        # ---------------------------------------------------------
        # STEP 9: LLM RESPONSE GENERATION
        # ---------------------------------------------------------
        top_chunk = candidate_chunks[0]
        raw_answer = await self.llm.generate_response(clean_query, candidate_chunks, "High", language)

        # ---------------------------------------------------------
        # STEP 10: OUTPUT GUARD - ANSWER-EVIDENCE CONSISTENCY CHECK
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
            suggestions = SuggestionsEngine.get_suggestions(intent, requires_human=True, status=consistency_status.value, language=language)
            return {
                **abstention,
                "status": consistency_status,
                "pii_warning": pii_warning,
                "action_confirmation": None,
                "intent": intent.value,
                "suggestions": suggestions,
                "rewritten_query": rewritten_query,
                "guardrail_flags": guardrail_flags + [f"CONSISTENCY_{consistency_status.value}"]
            }

        # ---------------------------------------------------------
        # STEP 11: CONFIDENCE, SOURCES & HUMAN ESCALATION
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
        suggestions = SuggestionsEngine.get_suggestions(
            intent, 
            requires_human=should_escalate, 
            status=consistency_status.value, 
            language=language
        )

        # ---------------------------------------------------------
        # STEP 12: MEMORY UPDATE & COMPACT SUMMARIZATION
        # ---------------------------------------------------------
        if session_id:
            new_topic = active_topic
            q_low = clean_query.lower()
            if "refund" in q_low or "return" in q_low:
                new_topic = "refund and return policy"
            elif "shipping" in q_low or "delivery" in q_low:
                new_topic = "shipping delivery timeline"
            elif "warranty" in q_low:
                new_topic = "hardware warranty"
            elif "cancel" in q_low:
                new_topic = "order cancellation"
            elif "novabook" in q_low or "spec" in q_low:
                new_topic = "novabook product specifications"

            ConversationMemory.update_session_context(
                session_id, 
                last_intent=intent.value, 
                active_topic=new_topic
            )
            ConversationMemory.generate_compact_summary(session_id)

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
            "intent": intent.value,
            "suggestions": suggestions,
            "rewritten_query": rewritten_query,
            "retrieval_score": top_score,
            "guardrail_flags": guardrail_flags + ["GUARDRAILS_PASSED"]
        }

guardrails_pipeline = SafeSupportGuardrails()
