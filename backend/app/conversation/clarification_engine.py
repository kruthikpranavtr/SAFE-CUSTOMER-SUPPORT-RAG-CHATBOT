import re
from typing import Tuple, Optional, Dict, Any, List

class ClarificationEngine:
    """
    SECTION 37 — CLARIFICATION GUARDRAIL
    Detects underspecified or ambiguous customer requests and generates
    polite clarification questions without guessing or hallucinating missing parameters.
    """

    AMBIGUOUS_PATTERNS = [
        (
            r'^\s*(?:i\s+want\s+to\s+cancel\s+it|cancel\s+it|please\s+cancel\s+it)\s*$',
            "I can certainly help you cancel an eligible order! Could you please provide your order reference number (e.g. #Nova-9876) so I can verify its status?",
            ["Check cancellation policy window", "Cancel order #Nova-9876", "Speak with human support"]
        ),
        (
            r'^\s*(?:i\s+want\s+to\s+return\s+something|i\s+want\s+to\s+return\s+it|help\s+me\s+return\s+this|return\s+it)\s*$',
            "I'd be glad to guide you through the return process. Could you tell me which product or order you're inquiring about, and whether the item is still unopened?",
            ["What is the return time window?", "Can I return a damaged product?", "How to get an RMA number"]
        ),
        (
            r'^\s*(?:where\s+is\s+it|track\s+it|check\s+status)\s*$',
            "I can help you check shipment status! Please provide your tracking number or order ID.",
            ["How long does standard delivery take?", "Track shipment #Nova-9876", "Contact human representative"]
        ),
        (
            r'^\s*(?:it\s+is\s+broken|it\s+doesnt\s+work|damaged)\s*$',
            "I'm sorry to hear that. To provide the exact policy options, is this item newly delivered or covered under our 1-year warranty?",
            ["Damaged delivery return policy", "Hardware warranty coverage", "File an RMA replacement claim"]
        )
    ]

    @classmethod
    def evaluate(cls, query: str, active_topic: Optional[str] = None) -> Tuple[bool, Optional[str], List[str]]:
        """
        Returns (is_ambiguous, clarification_prompt, suggestions).
        """
        clean_q = query.strip().lower()

        # Check explicit ambiguous patterns
        for pattern, prompt, suggestions in cls.AMBIGUOUS_PATTERNS:
            if re.search(pattern, clean_q):
                return True, prompt, suggestions

        # Generic ambiguity check: statement has intent to act on an unknown pronoun without order id
        if re.search(r'\b(?:cancel|return|change|delete|track)\s+(?:it|this|that|something)\b', clean_q):
            if not re.search(r'#?[a-zA-Z0-9_\-]{4,}', clean_q):
                prompt = (
                    "I'd be happy to assist with that! Could you clarify the specific product or order ID "
                    "you're referring to so I can provide accurate policy information?"
                )
                suggestions = ["Check Return Policy", "Check Cancellation Policy", "Contact Human Support"]
                return True, prompt, suggestions

        return False, None, []
