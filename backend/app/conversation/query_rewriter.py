import re
from typing import Optional, List, Dict, Any

class ContextualQueryRewriter:
    """
    SECTION 38 — SMART RAG RETRIEVAL (Query Rewriting Engine)
    Rewrites ambiguous or follow-up user queries using prior conversation context
    into self-contained, high-precision search queries for vector retrieval.
    The rewritten query is strictly internal and never replaces the user's original message.
    """

    PRONOUNS_AND_ELLIPSES = [
        r'\b(?:it|this|that|they|them|these|those)\b',
        r'^\s*(?:and|what\s+about|how\s+about|what\s+if|what\s+of)\b',
        r'^\s*(?:and\s+)?(?:express|ground|overnight|damaged|refurbished|international|weekend)\b',
        r'\b(?:same\s+thing|apply\s+to\s+this|eligible\s+too)\b',
        r'\b(?:enna|epdi|mudiyuma|panrathu|eppo)\b'
    ]

    TANGLISH_MAP = {
        r'\b(?:enna|yanna)\b': "what is",
        r'\b(?:epdi|eppadi)\b': "how to",
        r'\b(?:mudiyuma)\b': "can I is it eligible",
        r'\b(?:eppo|eppozhudhu)\b': "when timeline",
        r'\b(?:thirumba|thirumbavum)\b': "return refund",
        r'\b(?:kedaikuma)\b': "available policy",
        r'\b(?:kattanam)\b': "fee cost",
        r'\b(?:varala)\b': "not received delivery delayed"
    }

    @classmethod
    def rewrite(
        cls, 
        current_query: str, 
        recent_messages: List[Dict[str, Any]], 
        active_topic: Optional[str] = None
    ) -> str:
        """
        Returns a context-enhanced query string for ChromaDB retrieval.
        """
        clean_q = current_query.strip()
        q_lower = clean_q.lower()

        # Handle Tanglish translation for retrieval
        tanglish_translated = q_lower
        for pattern, replacement in cls.TANGLISH_MAP.items():
            tanglish_translated = re.sub(pattern, replacement, tanglish_translated)

        # Check if query needs contextual enrichment
        is_context_dependent = False
        for p in cls.PRONOUNS_AND_ELLIPSES:
            if re.search(p, q_lower):
                is_context_dependent = True
                break

        # If length is very short (< 4 words) without specific domain keywords
        words = re.findall(r'\b\w+\b', q_lower)
        if len(words) <= 3 and not any(k in q_lower for k in ["refund", "warranty", "shipping", "cancellation", "password"]):
            is_context_dependent = True

        if not is_context_dependent:
            return tanglish_translated

        # Extract previous domain context from recent messages or active_topic
        topic_anchor = active_topic or ""
        if not topic_anchor and recent_messages:
            # Look backwards at recent user/assistant turns
            for msg in reversed(recent_messages):
                c = msg.get("content", "").lower()
                if "refund" in c:
                    topic_anchor = "refund return policy"
                    break
                elif "shipping" in c or "delivery" in c:
                    topic_anchor = "shipping delivery policy"
                    break
                elif "warranty" in c:
                    topic_anchor = "warranty policy coverage"
                    break
                elif "cancel" in c:
                    topic_anchor = "cancellation policy"
                    break
                elif "novabook" in c or "spec" in c or "ram" in c:
                    topic_anchor = "novabook product specifications"
                    break

        # Synthesize rewritten query
        if topic_anchor:
            # Remove leading conjunctions
            stripped_query = re.sub(r'^\s*(?:and|what\s+about|what\s+if|how\s+about)\s+', '', tanglish_translated).strip()
            rewritten = f"{topic_anchor} {stripped_query}"
            return rewritten

        return tanglish_translated
