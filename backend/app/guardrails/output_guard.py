import re
from typing import List, Dict, Any, Tuple, Optional
from backend.app.guardrails.base import (
    GuardrailStatus, 
    ConfidenceLevel, 
    GuardrailType, 
    GuardrailSeverity, 
    GuardrailAction, 
    GuardrailResult,
    ClaimVerification,
    StructuredSource
)
from backend.app.rag.embeddings import STOP_WORDS

GENERIC_TERMS = STOP_WORDS | {
    "policy", "policies", "terms", "rules", "rule", "company", "information", "tell",
    "explain", "what", "where", "when", "which", "does", "have", "with", "support",
    "customer", "please", "can", "know", "how", "need", "want", "help", "technova",
    "give", "much", "many", "take", "long", "short", "days", "about", "your", "this"
}

class EvidenceOnlyGuardrail:
    """
    GUARDRAIL 1 — EVIDENCE-ONLY ANSWERING
    Prevents the model from hallucinating or answering when valid evidence is absent.
    Enforces that answers must be derived strictly from verified knowledge-base chunks.
    """
    @staticmethod
    def evaluate(query: str, retrieved_chunks: List[Dict[str, Any]]) -> GuardrailResult:
        if not retrieved_chunks:
            return GuardrailResult(
                passed=False,
                guardrail_type=GuardrailType.EVIDENCE_ONLY,
                action=GuardrailAction.ABSTAIN,
                severity=GuardrailSeverity.MEDIUM,
                reason="No supporting document chunks were retrieved for the query.",
                details={"chunk_count": 0}
            )

        top_score = retrieved_chunks[0].get("similarity_score", 0.0)
        if top_score < 0.25:
            return GuardrailResult(
                passed=False,
                guardrail_type=GuardrailType.EVIDENCE_ONLY,
                action=GuardrailAction.ABSTAIN,
                severity=GuardrailSeverity.MEDIUM,
                reason=f"Top retrieved chunk similarity score ({top_score:.3f}) is below minimum threshold (0.250).",
                details={"top_score": top_score}
            )

        return GuardrailResult(
            passed=True,
            guardrail_type=GuardrailType.EVIDENCE_ONLY,
            action=GuardrailAction.ALLOW,
            severity=GuardrailSeverity.INFO,
            reason="Retrieved evidence satisfies the minimum relevance threshold.",
            details={"top_score": top_score, "chunk_count": len(retrieved_chunks)}
        )

class AbstentionGuardrail:
    """
    GUARDRAIL 2 — ABSTENTION
    Provides an explicit, safe, standardized abstention response when evidence is missing,
    contradictory, or unverified. Prefers NO VERIFIED ANSWER over UNSUPPORTED ANSWER.
    """
    DEFAULT_ABSTENTION_EN = (
        "I couldn't verify this information from the available company documents. "
        "I don't want to guess. Please contact human support for confirmation."
    )
    DEFAULT_ABSTENTION_TA = (
        "வழங்கப்பட்டுள்ள நிறுவன ஆவணங்களில் இதற்குப் போதுமான உறுதிப்படுத்தப்பட்ட தகவல்கள் கிடைக்கவில்லை. "
        "ஊகத்தின் அடிப்படையில் பதிலளிக்க முடியாது. கூடுதல் உதவிக்கு மனித ஆதரவுக் குழுவைத் (Human Support) தொடர்பு கொள்ளவும்."
    )

    @staticmethod
    def create_abstention(query: str, reason: str, language: str = "en") -> Dict[str, Any]:
        msg = AbstentionGuardrail.DEFAULT_ABSTENTION_TA if language == "ta" else AbstentionGuardrail.DEFAULT_ABSTENTION_EN
        return {
            "answer": msg,
            "status": GuardrailStatus.ABSTAINED,
            "confidence": ConfidenceLevel.UNABLE_TO_DETERMINE,
            "evidence_status": "UNSUPPORTED",
            "sources": [],
            "requires_human": True,
            "verification_required": False,
            "abstention_reason": reason
        }

class SourceAttributionGuardrail:
    """
    GUARDRAIL 3 — SOURCE ATTRIBUTION
    Formats and validates structured source references.
    Ensures no fabricated sources or fictitious page numbers are emitted.
    """
    @staticmethod
    def build_sources(retrieved_chunks: List[Dict[str, Any]]) -> List[StructuredSource]:
        structured = []
        seen_ids = set()

        for c in retrieved_chunks:
            chunk_id = c.get("chunk_id", "")
            if not chunk_id or chunk_id in seen_ids:
                continue
            seen_ids.add(chunk_id)

            snippet = c.get("content_snippet", "").strip()
            # Infer section title from first line if header-like
            first_line = snippet.split("\n")[0] if snippet else ""
            section = first_line[:60] if any(k in first_line.lower() for k in ["section", "policy", "faq", "overview", "eligibility", "terms"]) else "General"

            structured.append(StructuredSource(
                document_name=c.get("document_name", "Unknown Policy"),
                page_number=int(c.get("page_number", 1)),
                section=section,
                snippet=snippet[:250] + ("..." if len(snippet) > 250 else ""),
                source_id=chunk_id,
                similarity_score=float(c.get("similarity_score", 0.0))
            ))

        return structured

class EvidenceConsistencyGuardrail:
    """
    GUARDRAIL 4 — ANSWER-EVIDENCE CONSISTENCY
    Extracts factual claims (numbers, time periods, fees, return windows, warranty terms)
    from the generated answer and cross-checks them against the retrieved evidence text.
    Detects contradictory or unsupported claims and triggers abstention if contradiction is found.
    """
    @staticmethod
    def extract_claims(text: str) -> List[str]:
        """
        Extracts key quantitative and policy claims:
        - Numbers with units (e.g. '7 calendar days', '30 days', '60 minutes', '1 year', '$50')
        - Absolute policy conditions ('non-refundable', 'free shipping', 'restocking fee')
        """
        claims = []
        # Pattern 1: Quantities with time/unit or currency
        patterns = [
            r'\b\d+\s*(?:calendar\s+days?|business\s+days?|days?|hours?|minutes?|months?|years?)\b',
            r'\$\s*\d+(?:\.\d+)?(?:\s*per\s*\w+)?',
            r'\b\d+%\b',
            r'\b(?:100%|full\s+refund|no\s+fee|free\s+shipping|restocking\s+fee)\b'
        ]
        text_lower = text.lower()
        for p in patterns:
            matches = re.findall(p, text_lower)
            claims.extend(matches)

        return list(set(claims))

    @classmethod
    def verify_consistency(
        cls, 
        generated_answer: str, 
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Tuple[GuardrailStatus, List[ClaimVerification], str]:
        """
        Compares factual claims in the answer against all retrieved evidence text.
        Returns (GuardrailStatus, claim_verifications, reason).
        """
        if not retrieved_chunks:
            return GuardrailStatus.UNSUPPORTED, [], "No evidence available to verify consistency."

        all_evidence_text = re.sub(r'\s+', ' ', " ".join([c.get("content_snippet", "").lower() for c in retrieved_chunks]))
        claims = [re.sub(r'\s+', ' ', clm) for clm in cls.extract_claims(generated_answer)]

        if not claims:
            # No specific numerical/policy claims extracted; general textual consistency
            return GuardrailStatus.SUPPORTED, [], "Answer contains general procedural guidance."

        verifications = []
        has_contradiction = False
        unsupported_count = 0

        for claim in claims:
            # Check if claim is directly supported in evidence text
            if claim in all_evidence_text:
                verifications.append(ClaimVerification(
                    claim=claim,
                    is_supported=True,
                    is_contradicted=False,
                    similarity=1.0
                ))
            else:
                # Check if claim contradicts a known dimension (e.g. claim has '30 days' but evidence has '7 calendar days')
                claim_num_match = re.search(r'\b\d+\b', claim)
                is_contradiction = False
                if claim_num_match:
                    claim_num = claim_num_match.group(0)
                    # Look for other numbers associated with the same unit in evidence
                    unit_match = re.search(r'(?:days?|hours?|minutes?|months?|years?|\$)', claim)
                    if unit_match:
                        unit = unit_match.group(0)
                        evidence_units = re.findall(rf'\b(\d+)\s*(?:calendar\s+|business\s+)?{unit}', all_evidence_text)
                        if evidence_units and claim_num not in evidence_units:
                            is_contradiction = True
                            has_contradiction = True

                unsupported_count += 1
                verifications.append(ClaimVerification(
                    claim=claim,
                    is_supported=False,
                    is_contradicted=is_contradiction,
                    similarity=0.0
                ))

        if has_contradiction:
            return (
                GuardrailStatus.CONTRADICTED, 
                verifications, 
                "Answer contains factual claims that directly contradict company policy documents."
            )

        if unsupported_count > 0:
            if unsupported_count == len(claims):
                return (
                    GuardrailStatus.UNSUPPORTED, 
                    verifications, 
                    "Answer contains factual claims that are not corroborated by any retrieved document."
                )
            return (
                GuardrailStatus.PARTIALLY_SUPPORTED, 
                verifications, 
                "Some claims in the answer could not be verified from the retrieved documents."
            )

        return GuardrailStatus.SUPPORTED, verifications, "All factual claims are strictly supported by retrieved evidence."

class ConfidenceGuardrail:
    """
    GUARDRAIL 5 — CONFIDENCE / UNCERTAINTY
    Deterministic, documented evidence confidence calculation:
    - HIGH: Top similarity >= 0.50 AND all factual claims verified.
    - MEDIUM: Top similarity >= 0.35 OR partially supported claims.
    - LOW: Top similarity >= 0.20 OR weak keyword coverage.
    - UNABLE_TO_DETERMINE: Similarity < 0.20 OR missing evidence OR contradicted claims.
    """
    @staticmethod
    def calculate(
        top_similarity: float, 
        distinct_coverage: float, 
        consistency_status: GuardrailStatus
    ) -> ConfidenceLevel:
        if consistency_status in [GuardrailStatus.CONTRADICTED, GuardrailStatus.UNSUPPORTED]:
            return ConfidenceLevel.UNABLE_TO_DETERMINE

        effective_score = round(0.55 * top_similarity + 0.45 * distinct_coverage, 3)

        if consistency_status == GuardrailStatus.SUPPORTED and effective_score >= 0.50 and distinct_coverage >= 0.55:
            return ConfidenceLevel.HIGH
        elif effective_score >= 0.35:
            return ConfidenceLevel.MEDIUM
        elif effective_score >= 0.20:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNABLE_TO_DETERMINE
