import re
from typing import List, Dict, Any, Tuple, Optional
from backend.app.utils.config import settings
from backend.app.rag.vector_store import vector_store
from backend.app.rag.llm import llm_service
from backend.app.rag.embeddings import STOP_WORDS
from backend.app.models.schemas import SourceItem, EvidenceItem

GENERIC_WORDS = STOP_WORDS | {
    "policy", "policies", "terms", "rules", "rule", "company", "information", "tell",
    "explain", "what", "where", "when", "which", "does", "have", "with", "support",
    "customer", "please", "can", "know", "how", "need", "want", "help", "technova",
    "give", "much", "many", "take", "long", "short", "days", "about", "your", "this",
    "எத்தனை", "நாட்கள்", "என்ன", "எப்படி", "கேட்கலாம்"
}

TAMIL_TO_ENGLISH_KEYWORDS = {
    "பணம் திரும்ப": "refund",
    "திரும்பப் பெற": "refund return",
    "ரீஃபண்ட்": "refund",
    "ஷிப்பிங்": "shipping delivery",
    "டெலிவரி": "delivery shipping",
    "அனுப்பு": "shipping delivery dispatch",
    "வாரண்டி": "warranty replacement",
    "உத்தரவாதம்": "warranty guarantee",
    "ரத்து": "cancel cancellation",
    "ரிட்டர்ன்": "return exchange",
    "திரும்புதல்": "return exchange",
    "ஆர்டர்": "order purchase",
    "கட்டணம்": "fee cost payment",
    "விதிமுறைகள்": "policy rules terms",
    "நிபந்தனைகள்": "policy terms conditions",
    "நாட்கள்": "days calendar timeline",
    "உடை": "damaged defect",
    "பழுது": "defect damage warranty repair",
    "தயாரிப்பு": "product hardware novabook"
}

class RAGPipeline:
    def __init__(self):
        self.vector_store = vector_store
        self.llm = llm_service

    def determine_confidence(self, query: str, chunks: List[Dict[str, Any]]) -> Tuple[str, Optional[str], float]:
        """
        Calculates confidence level based on semantic similarity, keyword overlap, and chunk density.
        Returns (confidence_level, verification_notice, top_score).
        """
        if not chunks:
            return (
                "Unable to determine",
                "I couldn't find sufficient information in the available company documents.",
                0.0
            )

        # Extract distinctive query keywords
        raw_words = re.findall(r'\b[a-zA-Z0-9_\-\u0B80-\u0BFF]{3,}\b', query.lower())
        key_words = [w for w in raw_words if w not in STOP_WORDS]
        # For distinct keywords against English doc vocabulary, keep Latin tokens
        distinct_keywords = [w for w in raw_words if w not in GENERIC_WORDS and re.match(r'^[a-z0-9_\-]+$', w)]

        # Check for unknown domain terms across the entire database
        all_db_text = ""
        try:
            cached_docs = self.vector_store.collection.get(include=["documents"])
            if cached_docs and cached_docs.get("documents"):
                all_db_text = " ".join(cached_docs["documents"]).lower()
        except Exception:
            pass

        all_db_tokens = set(re.findall(r'\b[a-zA-Z0-9_\-\u0B80-\u0BFF]{3,}\b', all_db_text)) if all_db_text else set()

        unknown_in_db = []
        if all_db_tokens and key_words:
            for w in key_words:
                if re.match(r'^[a-z0-9_\-]+$', w) and len(w) >= 4 and w not in all_db_tokens:
                    # Prefix stem check
                    prefix_match = any(tok.startswith(w[:min(len(w), 5)]) or w.startswith(tok) for tok in all_db_tokens if len(tok) >= 4)
                    if not prefix_match:
                        unknown_in_db.append(w)

        # Top chunk analysis
        top_chunk = chunks[0]
        top_score = top_chunk["similarity_score"]

        # If top retrieved chunk similarity is very low, refuse immediately
        if top_score < 0.25:
            return (
                "Unable to determine",
                "I couldn't find sufficient information in the available company documents regarding the requested topic.",
                top_score
            )

        # Check context coverage
        all_context = " ".join([c["content_snippet"].lower() for c in chunks[:3]])
        context_tokens = set(re.findall(r'\b[a-zA-Z0-9_\-\u0B80-\u0BFF]{3,}\b', all_context))

        matched_distinct = []
        if distinct_keywords:
            for w in distinct_keywords:
                if w in context_tokens or any(tok.startswith(w[:min(len(w), 5)]) or w.startswith(tok) for tok in context_tokens if len(tok) >= 4):
                    matched_distinct.append(w)
            distinct_coverage = len(matched_distinct) / max(len(distinct_keywords), 1)
        else:
            distinct_coverage = 0.0 if top_score < 0.40 else 0.5

        # If key terms are unknown in DB AND context coverage is insufficient or < 2 key terms matched
        if unknown_in_db and (distinct_coverage < 0.65 or len(matched_distinct) < 2):
            return (
                "Unable to determine",
                "I couldn't find sufficient information in the available company documents regarding the requested topic.",
                0.05
            )

        # Score calculation
        effective_score = round(0.55 * top_score + 0.45 * distinct_coverage, 3)

        if effective_score >= 0.50 and distinct_coverage >= 0.60:
            confidence = "High"
            notice = "AI-generated response. Please verify important information using the cited sources before taking action."
        elif effective_score >= 0.35 and distinct_coverage >= 0.40:
            confidence = "Moderate"
            notice = "AI-generated response. Information is moderately supported by company documents. Please verify cited sections."
        elif effective_score >= 0.20:
            confidence = "Low"
            notice = "Limited supporting information was found. Please verify this information against official company policy."
        else:
            confidence = "Unable to determine"
            notice = "I couldn't find sufficient supporting information in the available company documents."

        return confidence, notice, effective_score

    async def execute_rag(self, query: str, language: str = "en") -> Dict[str, Any]:
        # Cross-lingual expansion if query contains Tamil or language is 'ta'
        search_query = query
        has_tamil = bool(re.search(r'[\u0B80-\u0BFF]', query))
        if language == "ta" or has_tamil:
            expansions = []
            for tam_phrase, eng_words in TAMIL_TO_ENGLISH_KEYWORDS.items():
                if tam_phrase in query:
                    expansions.append(eng_words)
            if expansions:
                search_query = f"{query} {' '.join(expansions)}"

        # 1. Retrieve candidate chunks from ChromaDB
        candidate_chunks = self.vector_store.query(search_query, top_k=settings.TOP_K_CHUNKS)

        # 2. Determine confidence and verification warning
        confidence, verification_notice, score = self.determine_confidence(
            search_query if (language == "ta" or has_tamil) else query, 
            candidate_chunks
        )

        # 3. If confidence is "Unable to determine", do not show misleading sources
        active_chunks = candidate_chunks if confidence != "Unable to determine" else []

        # 4. Generate answer through LLM or grounded synthesizer
        answer = await self.llm.generate_response(query, active_chunks, confidence, language)

        # 5. Format sources & Evidence Items
        sources = []
        evidence_items = []
        seen_chunks = set()

        for c in active_chunks:
            if c["chunk_id"] not in seen_chunks:
                seen_chunks.add(c["chunk_id"])
                
                # Assign qualitative relevance
                sim = c["similarity_score"]
                relevance = "High" if sim >= 0.55 else ("Medium" if sim >= 0.35 else "Low")
                
                # Format clean quote snippet
                snippet = c["content_snippet"].strip()
                quote = snippet[:220] + ("..." if len(snippet) > 220 else "")

                sources.append(SourceItem(
                    document_name=c["document_name"],
                    page_number=c.get("page_number", 1),
                    chunk_id=c["chunk_id"],
                    content_snippet=snippet[:300] + ("..." if len(snippet) > 300 else ""),
                    similarity_score=sim
                ))

                evidence_items.append(EvidenceItem(
                    document_name=c["document_name"],
                    page_number=c.get("page_number", 1),
                    relevance=relevance,
                    quote=quote,
                    similarity_score=sim
                ))

        return {
            "answer": answer,
            "confidence": confidence,
            "verification_notice": verification_notice,
            "sources": sources,
            "evidence_items": evidence_items,
            "retrieval_score": score
        }

rag_pipeline = RAGPipeline()
