import os
import re
import chromadb
from typing import List, Dict, Any, Optional
from backend.app.utils.config import settings
from backend.app.rag.embeddings import get_embedding_function, STOP_WORDS

GENERIC_SEARCH_TERMS = STOP_WORDS | {
    "policy", "policies", "terms", "rules", "rule", "company", "information", "tell",
    "explain", "what", "where", "when", "which", "does", "have", "with", "support",
    "customer", "please", "can", "know", "how", "need", "want", "help", "technova"
}

class VectorStore:
    def __init__(self):
        os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        self.embedding_fn = get_embedding_function()
        self.collection = self.client.get_or_create_collection(
            name="technova_support_knowledgebase",
            embedding_function=self.embedding_fn,
            metadata={"description": "Company policy and support documentation chunks"}
        )

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        if not chunks:
            return 0
        
        ids = [c["chunk_id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [
            {
                "document_id": c["document_id"],
                "document_name": c["document_name"],
                "page": int(c.get("page", 1))
            }
            for c in chunks
        ]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        return len(chunks)

    def delete_document_chunks(self, document_id: str) -> None:
        try:
            self.collection.delete(where={"document_id": document_id})
        except Exception as e:
            print(f"Notice: Deletion for doc {document_id}: {e}")

    def query(self, query_text: str, top_k: int = 4) -> List[Dict[str, Any]]:
        count = self.collection.count()
        if count == 0:
            return []
        
        # Pull candidate chunks
        n_candidates = min(max(top_k * 4, 20), count)
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_candidates,
            include=["documents", "metadatas", "distances"]
        )

        if not results or "documents" not in results or not results["documents"]:
            return []

        docs = results["documents"][0]
        metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
        dists = results["distances"][0] if "distances" in results else [1.0] * len(docs)
        ids = results["ids"][0] if "ids" in results else [""] * len(docs)

        # Extract distinctive query keywords
        raw_words = re.findall(r'\b[a-zA-Z0-9_\-]{3,}\b', query_text.lower())
        key_terms = [w for w in raw_words if w not in GENERIC_SEARCH_TERMS]
        if not key_terms:
            key_terms = [w for w in raw_words if w not in STOP_WORDS]
        if not key_terms:
            key_terms = raw_words

        ranked_chunks = []
        for i in range(len(docs)):
            text = docs[i]
            meta = metas[i]
            dist = dists[i]
            doc_name = meta.get("document_name", "").lower()
            text_lower = text.lower()

            # Vector similarity in [0, 1]
            vector_sim = max(0.0, min(1.0, 1.0 / (1.0 + float(dist))))

            # Exact keyword matches
            matched_terms = [t for t in key_terms if t in text_lower]
            matched_title_terms = [t for t in key_terms if t in doc_name]

            term_coverage = len(matched_terms) / max(len(key_terms), 1)
            title_coverage = len(matched_title_terms) / max(len(key_terms), 1)

            # Frequency of key terms in this chunk
            total_occurrences = sum(text_lower.count(t) for t in key_terms)
            freq_score = min(1.0, total_occurrences / (len(key_terms) * 2 or 1))

            if not matched_terms and not matched_title_terms:
                hybrid_score = round(vector_sim * 0.05, 3)
            else:
                hybrid_score = round(
                    0.20 * vector_sim + 0.45 * term_coverage + 0.20 * title_coverage + 0.15 * freq_score, 
                    3
                )

            ranked_chunks.append({
                "chunk_id": ids[i],
                "document_id": meta.get("document_id", ""),
                "document_name": meta.get("document_name", "Unknown Document"),
                "page_number": int(meta.get("page", 1)),
                "content_snippet": text,
                "similarity_score": min(1.0, hybrid_score),
                "matched_terms_count": len(matched_terms)
            })

        # Sort by hybrid score descending
        ranked_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)
        return ranked_chunks[:top_k]

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        results = self.collection.get(ids=[chunk_id], include=["documents", "metadatas"])
        if results and results["documents"] and len(results["documents"]) > 0:
            doc = results["documents"][0]
            meta = results["metadatas"][0] if results["metadatas"] else {}
            return {
                "chunk_id": chunk_id,
                "document_id": meta.get("document_id", ""),
                "document_name": meta.get("document_name", "Unknown"),
                "page_number": int(meta.get("page", 1)),
                "text": doc
            }
        return None

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        results = self.collection.get(where={"document_id": document_id}, include=["documents", "metadatas"])
        chunks = []
        if results and results["documents"]:
            for i in range(len(results["documents"])):
                meta = results["metadatas"][i] if results["metadatas"] else {}
                chunks.append({
                    "chunk_id": results["ids"][i],
                    "document_id": document_id,
                    "document_name": meta.get("document_name", "Unknown"),
                    "page_number": int(meta.get("page", 1)),
                    "text": results["documents"][i]
                })
        return chunks

vector_store = VectorStore()
