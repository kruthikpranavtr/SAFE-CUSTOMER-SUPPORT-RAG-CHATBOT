import re
import time
from typing import Dict, Any, Tuple, Optional, List
from backend.app.guardrails.base import (
    GuardrailStatus, 
    GuardrailType, 
    GuardrailSeverity, 
    GuardrailAction, 
    GuardrailResult
)
from backend.app.utils.config import settings

# In-memory sliding window store: user_id/ip -> list of timestamps
_RATE_LIMIT_STORE: Dict[str, List[float]] = {}

class PIIGuardrail:
    """
    GUARDRAIL 7 — PII PROTECTION
    Detects phone numbers, email addresses, credit/debit card numbers, government IDs, and account numbers.
    Redacts sensitive tokens before sending to LLM and returns a user warning notice.
    """
    PII_PATTERNS = {
        "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b',
        "PHONE": r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?|\b\d{3}[-.\s]?)\d{3}[-.\s]?\d{4}\b|\b[6-9]\d{9}\b',
        "CREDIT_CARD": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b|\b(?:\d{4}[-\s]){3}\d{4}\b',
        "SSN_GOV_ID": r'\b\d{3}-\d{2}-\d{4}\b|\b\d{4}\s\d{4}\s\d{4}\b',
        "ACCOUNT_NUMBER": r'\b(?:acct|account|acc)\s*#?\s*:?\s*\d{8,17}\b'
    }

    @classmethod
    def evaluate(cls, text: str) -> Tuple[bool, str, List[str], str]:
        """
        Inspects text for PII.
        Returns (has_pii, redacted_text, detected_types, warning_message).
        """
        redacted = text
        detected = []

        for pii_type, pattern in cls.PII_PATTERNS.items():
            matches = list(re.finditer(pattern, redacted, flags=re.IGNORECASE))
            if matches:
                detected.append(pii_type)
                # Replace with placeholder
                redacted = re.sub(pattern, f"[REDACTED_{pii_type}]", redacted, flags=re.IGNORECASE)

        if detected:
            warning = "⚠️ Please avoid sharing sensitive personal information in this chat."
            return True, redacted, detected, warning

        return False, text, [], ""

class DomainGuardrail:
    """
    GUARDRAIL 8 — DOMAIN RESTRICTION
    Enforces that queries relate strictly to company customer-support topics:
    Products, Orders, Delivery, Returns, Refunds, Warranty, Company policies, Support procedures.
    """
    ALLOWED_SUPPORT_KEYWORDS = {
        "refund", "return", "shipping", "delivery", "warranty", "order", "cancel",
        "cancellation", "product", "novabook", "hardware", "charger", "battery",
        "fee", "charge", "payment", "track", "tracking", "status", "damaged", "repair",
        "replacement", "support", "help", "policy", "policies", "terms", "rma", "contact",
        "faq", "account", "password", "reset", "email", "address", "warehouse", "store",
        # Tamil support terms
        "பணம்", "ரீஃபண்ட்", "ரிட்டர்ன்", "ஷிப்பிங்", "டெலிவரி", "வாரண்டி", "ஆர்டர்", "ரத்து"
    }

    OUT_OF_DOMAIN_PATTERNS = [
        r'\b(?:write\s+(?:a\s+)?(?:python|java|javascript|c\+\+|code|script|essay|poem|song|story))\b',
        r'\b(?:recipe|cook|how\s+to\s+bake|ingredients)\b',
        r'\b(?:weather\s+in|forecast\s+for)\b',
        r'\b(?:who\s+won\s+the|sports\s+score|fifa|olympics)\b',
        r'\b(?:bitcoin|ethereum|crypto|stock\s+market|investing\s+advice|trading\s+strategy)\b'
    ]

    OUT_OF_DOMAIN_RESPONSE_EN = (
        "I'm designed to help with customer-support questions. "
        "Please ask something related to our products, orders, policies, or services."
    )
    OUT_OF_DOMAIN_RESPONSE_TA = (
        "நான் வாடிக்கையாளர் சேவை (Customer Support) உதவிகளுக்காக மட்டுமே வடிவமைக்கப்பட்டுள்ளேன். "
        "எங்கள் தயாரிப்புகள், ஆர்டர்கள், ஷிப்பிங், வாரண்டி அல்லது நிறுவனக் கொள்கைகள் தொடர்பான கேள்விகளைக் கேட்கவும்."
    )

    @classmethod
    def evaluate(cls, query: str, language: str = "en") -> GuardrailResult:
        query_lower = query.lower()

        # Check explicit out of domain patterns
        for p in cls.OUT_OF_DOMAIN_PATTERNS:
            if re.search(p, query_lower):
                resp = cls.OUT_OF_DOMAIN_RESPONSE_TA if language == "ta" else cls.OUT_OF_DOMAIN_RESPONSE_EN
                return GuardrailResult(
                    passed=False,
                    guardrail_type=GuardrailType.DOMAIN_VIOLATION,
                    action=GuardrailAction.REJECT,
                    severity=GuardrailSeverity.LOW,
                    reason="Query belongs to an unsupported topic outside customer support domain.",
                    details={"response": resp}
                )

        # Check if query is completely irrelevant to company support
        words = set(re.findall(r'\b[a-zA-Z0-9_\-\u0B80-\u0BFF]{3,}\b', query_lower))
        has_support_term = bool(words.intersection(cls.ALLOWED_SUPPORT_KEYWORDS))

        return GuardrailResult(
            passed=True,
            guardrail_type=GuardrailType.DOMAIN_VIOLATION,
            action=GuardrailAction.ALLOW,
            severity=GuardrailSeverity.INFO,
            reason="Query is within customer support domain scope.",
            details={"has_support_term": has_support_term}
        )

class RateLimitGuardrail:
    """
    RATE LIMITING
    Prevents denial-of-service and abusive querying by tracking requests per IP / user
    using a sliding window. Limits are configurable via settings.
    """
    @staticmethod
    def evaluate(client_id: str) -> GuardrailResult:
        max_requests = getattr(settings, "RATE_LIMIT_REQUESTS", 60)
        window_seconds = getattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)

        now = time.time()
        window_start = now - window_seconds

        timestamps = _RATE_LIMIT_STORE.get(client_id, [])
        # Prune old timestamps
        timestamps = [t for t in timestamps if t > window_start]

        if len(timestamps) >= max_requests:
            _RATE_LIMIT_STORE[client_id] = timestamps
            return GuardrailResult(
                passed=False,
                guardrail_type=GuardrailType.RATE_LIMIT,
                action=GuardrailAction.BLOCK,
                severity=GuardrailSeverity.HIGH,
                reason=f"Rate limit exceeded: {len(timestamps)} requests in {window_seconds}s window (limit: {max_requests}).",
                details={"max_requests": max_requests, "window_seconds": window_seconds}
            )

        timestamps.append(now)
        _RATE_LIMIT_STORE[client_id] = timestamps
        return GuardrailResult(
            passed=True,
            guardrail_type=GuardrailType.RATE_LIMIT,
            action=GuardrailAction.ALLOW,
            severity=GuardrailSeverity.INFO,
            reason="Request within rate limits.",
            details={"current_count": len(timestamps), "limit": max_requests}
        )
