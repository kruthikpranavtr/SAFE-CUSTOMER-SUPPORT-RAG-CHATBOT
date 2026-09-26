import re
import httpx
from typing import List, Dict, Any, Optional
from backend.app.utils.config import settings

SYSTEM_INSTRUCTION = """You are the AI Customer Support Assistant for TechNova.
YOUR STRICT OBJECTIVE:
Answer the customer's question using ONLY the provided company documentation context.

SAFETY AND FACTUAL INTEGRITY RULES:
1. NON-FABRICATION: If the question cannot be answered using the provided context, you must clearly state:
   "Sorry, I couldn't find sufficient information about that in the available company documents."
2. NO ANTHROPOMORPHISM: Never refer to yourself as a human employee, do not claim personal feelings or personal life experiences. Always speak neutrally as an AI Customer Support Assistant.
3. CITATION: Explicitly refer to the relevant policy or section mentioned in the context.
4. UNCERTAINTY: If the retrieved information only partially addresses the question, explicitly communicate that and advise the user to verify with cited sources.
5. CONCISENESS: Provide direct, helpful, and polite answers without unnecessary filler.
"""

class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.openai_key = settings.OPENAI_API_KEY
        self.gemini_key = settings.GEMINI_API_KEY

    async def generate_response(
        self, 
        query: str, 
        context_chunks: List[Dict[str, Any]],
        confidence_level: str
    ) -> str:
        """
        Generates response using configured provider. Falls back cleanly to Local Grounded Synthesizer.
        """
        # If confidence is Unable to determine or context is empty
        if confidence_level == "Unable to determine" or not context_chunks:
            return f"Sorry, I couldn't find sufficient information regarding \"{query}\" in the available company documents. Please verify with official company support or check if the relevant policy document has been uploaded."

        # If Gemini is configured
        if self.gemini_key and (self.provider == "gemini" or not self.openai_key):
            try:
                return await self._call_gemini(query, context_chunks)
            except Exception as e:
                print(f"Gemini API error (falling back): {e}")

        # If OpenAI is configured
        if self.openai_key and self.provider == "openai":
            try:
                return await self._call_openai(query, context_chunks)
            except Exception as e:
                print(f"OpenAI API error (falling back): {e}")

        # Local Grounded Synthesizer (Reliable, fast, zero-external-dependency fallback)
        return self._local_grounded_synthesis(query, context_chunks, confidence_level)

    async def _call_gemini(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        formatted_context = "\n\n".join([
            f"[Source: {c['document_name']} | Page {c['page_number']}]\n{c['content_snippet']}"
            for c in context_chunks
        ])
        
        prompt = f"{SYSTEM_INSTRUCTION}\n\nCONTEXT:\n{formatted_context}\n\nCUSTOMER QUESTION:\n{query}\n\nANSWER:"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600}
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            raise Exception(f"Gemini returned status {resp.status_code}: {resp.text}")

    async def _call_openai(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        formatted_context = "\n\n".join([
            f"[Source: {c['document_name']} | Page {c['page_number']}]\n{c['content_snippet']}"
            for c in context_chunks
        ])

        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": f"CONTEXT:\n{formatted_context}\n\nCUSTOMER QUESTION: {query}"}
        ]
        
        payload = {
            "model": settings.LLM_MODEL,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 500
        }
        
        headers = {"Authorization": f"Bearer {self.openai_key}"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            raise Exception(f"OpenAI returned status {resp.status_code}: {resp.text}")

    def _local_grounded_synthesis(
        self, 
        query: str, 
        context_chunks: List[Dict[str, Any]], 
        confidence_level: str
    ) -> str:
        """
        Extractive, grounded local answering engine.
        Extracts relevant factual sentences from the top retrieved chunks,
        avoids hallucinations, and directly cites retrieved company documentation.
        """
        query_words = set(re.findall(r'\b\w{3,}\b', query.lower()))
        # Filter stop words
        stop_words = {"what", "when", "where", "which", "does", "have", "with", "from", "about", "your", "their", "this", "that"}
        key_terms = query_words - stop_words

        extracted_sentences = []
        seen = set()

        for chunk in context_chunks:
            text = chunk.get("content_snippet", "")
            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', text)
            for s in sentences:
                s_clean = s.strip()
                if len(s_clean) < 15 or s_clean in seen:
                    continue
                # Score sentence by keyword overlap
                s_words = set(re.findall(r'\b\w{3,}\b', s_clean.lower()))
                match_count = len(key_terms.intersection(s_words))
                if match_count > 0:
                    seen.add(s_clean)
                    extracted_sentences.append((match_count, chunk["document_name"], chunk["page_number"], s_clean))

        if not extracted_sentences:
            # Fall back to first 2 sentences of top chunk if available
            top_chunk = context_chunks[0]
            top_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', top_chunk["content_snippet"]) if len(s.strip()) > 15]
            if top_sentences:
                return f"Based on the {top_chunk['document_name']} (Page {top_chunk['page_number']}):\n\n" + " ".join(top_sentences[:2])
            return "Sorry, I couldn't find sufficient information about that in the available company documents."

        # Sort by relevance match count
        extracted_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = extracted_sentences[:3]
        
        primary_doc = top_sentences[0][1]
        primary_page = top_sentences[0][2]

        body = " ".join([item[3] for item in top_sentences])
        
        prefix = f"Based on {primary_doc} (Page {primary_page}):\n\n"
        if confidence_level == "Low":
            return prefix + body + "\n\n(Note: This provides only partial coverage of your query. Please verify against the full cited policy.)"
        
        return prefix + body

llm_service = LLMService()
