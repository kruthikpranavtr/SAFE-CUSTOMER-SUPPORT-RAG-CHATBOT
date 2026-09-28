# Safe Customer Support RAG Chatbot

An AI-powered, evidence-based customer support web application designed to reduce **overreliance on AI**, **automation bias**, **anthropomorphization**, and **unsupported/hallucinated answers** using Retrieval-Augmented Generation (RAG) and behavioral testing.

---

## 1. Project Title & Overview
**Application Name:** Safe Customer Support RAG Chatbot  
**Identity:** AI Customer Support Assistant  
**Primary Mission:** Answering customer questions strictly from verified company documentation, communicating explicit confidence levels, citing supporting document excerpts, providing user verification warnings, and running controlled behavioral user studies to measure error detection rates.

---

## 2. Problem Statement
When modern customer support chatbots provide confident-sounding responses, users are prone to:
1. **Overreliance on AI:** Assuming automated outputs are always accurate and neglecting manual verification.
2. **Automation Bias:** Blindly accepting algorithmic outputs even in the presence of contradictory evidence.
3. **Anthropomorphization:** Trusting the chatbot as if it were a human employee with personal knowledge and accountability.
4. **Hallucination & Fabrication:** Generating plausible-sounding but completely fabricated company policies (e.g., claiming a 30-day return policy when the actual company policy strictly enforces 7 days).

---

## 3. Objectives
- Provide accurate, factually grounded answers to customer questions using an enterprise RAG pipeline.
- Implement explicit **Source Attribution** with page numbers and text snippets viewable in real-time.
- Calibrate and communicate **Uncertainty** across 4 levels: *High*, *Moderate*, *Low*, and *Unable to determine*.
- Prevent policy fabrication by safely refusing queries unsupported by company documents.
- Clearly present the assistant as non-human (*"AI Customer Support Assistant"*).
- Include an integrated **User Study Module** with injected errors to measure user error detection rates.
- Present real-time telemetry through an interactive **Admin Dashboard**.

---

## 4. Technologies Used

### Frontend
- **React 18** (TypeScript)
- **Vite 5** (Fast development server and bundling)
- **Tailwind CSS 3** (Responsive, professional SaaS layout)
- **Lucide React** (Consistent iconography)

### Backend
- **Python 3.12**
- **FastAPI** (High-performance asynchronous REST API)
- **Uvicorn** (ASGI server)
- **Pydantic v2 & Pydantic-Settings** (Data validation & schemas)

### RAG & Vector Database
- **ChromaDB** (Local persistent vector database)
- **Modular Embedding System** (Hybrid TF-IDF subword vectorizer with zero external network dependencies, plus support for OpenAI/Sentence-Transformers)
- **Multi-format Document Parsers** (`pypdf`, `python-docx`, plain text)
- **Modular LLM Integration** (Local grounded synthesizer with zero external dependencies, plus plug-and-play support for Google Gemini and OpenAI)

### Database
- **SQLite** (`data/app.db`) for chat sessions, messages, documents, feedback, and user study results.

---

## 5. System Architecture & RAG Pipeline

```
                                  +-----------------------------+
                                  |   Customer / Evaluator UI   |
                                  | (React + Vite + TypeScript) |
                                  +--------------+--------------+
                                                 |
                                     HTTP REST / JSON
                                                 |
                                  +--------------v--------------+
                                  |     FastAPI Backend API     |
                                  +--------------+--------------+
                                                 |
             +-----------------------------------+-----------------------------------+
             |                                   |                                   |
+------------v------------+         +------------v------------+         +------------v------------+
|  Document Preprocessor  |         |   Hybrid Vector Store   |         |      Relational DB      |
|  - Text Extraction      |         |   - ChromaDB Collection |         |      - SQLite           |
|  - Sliding-Window Chunk |         |   - Subword Embeddings  |         |      - Sessions & Logs  |
|  - Page Metadata        |         |   - BM25 Re-Ranking     |         |      - User Study Data  |
+-------------------------+         +------------+------------+         +-------------------------+
                                                 |
                                    +------------v------------+
                                    |   Confidence Evaluator  |
                                    |   - Lexical & Semantic  |
                                    |   - Domain Verification |
                                    +------------+------------+
                                                 |
                                    +------------v------------+
                                    |   Grounded Synthesizer  |
                                    |   - Local / Gemini / OAI|
                                    |   - Citation Formatting |
                                    +-------------------------+
```

### RAG Execution Steps:
1. **Document Ingestion:** Admin uploads PDF, TXT, or DOCX documents to `data/documents/`.
2. **Chunking & Metadata:** Documents are split into 800-character overlapping chunks, preserving document name, chunk ID, and page number.
3. **ChromaDB Indexing:** Text chunks are vectorized and indexed into the ChromaDB collection `technova_support_knowledgebase`.
4. **Retrieval & Re-ranking:** Customer questions query ChromaDB with hybrid cosine similarity and keyword coverage re-ranking.
5. **Confidence & Domain Check:**
   - If key distinctive terms are absent from the entire documentation corpus, confidence is set to **"Unable to determine"** and safe refusal is triggered.
   - If evidence is strongly corroborated, confidence is set to **High** or **Moderate**.
6. **Answer Synthesis:** Formulates factual answers with exact citations and displays verification alerts.

---

## 6. Database Schema (SQLite)

- **`users`**: User identity and customer role.
- **`chat_sessions`**: Conversation threads, titles, and timestamps.
- **`messages`**: Chat history, message role (`user`/`assistant`), content, confidence, serialized sources, and retrieval scores.
- **`documents`**: Tracked knowledge base files, upload dates, chunk counts, and indexing status.
- **`feedback`**: User feedback ratings (`helpful`, `unhelpful`), category reasons (`incorrect_info`, `unsupported_source`, `unclear`, `missing_info`), and user comments.
- **`study_sessions`**: User-study evaluation sessions and completion progress.
- **`study_responses`**: Participant decisions on injected-error scenarios, tracking correctness, response time in milliseconds, and whether sources were viewed.

---

## 7. Safety Mechanisms & Bias Mitigation

| Mechanism | Implementation | Purpose |
| :--- | :--- | :--- |
| **Automation Bias Warning** | Persistent amber banner and per-message notice: *"AI answers may contain errors. Check cited sources before making important decisions."* | Encourages manual verification rather than passive acceptance. |
| **De-anthropomorphization** | Strictly labeled as **"AI Customer Support Assistant"** with bot avatars. Forbids human names, human portraits, and personal emotions. | Mitigates emotional trust and synthetic human bonding. |
| **Source Citation & Inspection** | Every AI response renders clickable document badges (`[View Source]`) opening the raw chunk excerpt with similarity score. | Allows instant verification against source text. |
| **Non-Fabrication Policy** | Queries lacking sufficient documentation return: *"Sorry, I couldn't find sufficient information about that in the available company documents."* | Prevents hallucinating fictional policies. |
| **Uncertainty Calibration** | Dynamic confidence badges: *High* (Emerald), *Moderate* (Amber), *Low* (Orange), *Unable to determine* (Rose). | Clearly bounds the certainty of each generated response. |

---

## 8. User Study Methodology & Metrics

The built-in **User Study Module** (`/study`) tests whether users can catch errors in AI customer support answers:
1. Participants review controlled customer support scenarios.
2. Scenarios include:
   - **Supported Answers:** Answers that accurately match company policy.
   - **Injected Errors:** Plausible-sounding answers that deliberately contradict company policy (e.g. claiming a 30-day refund window when policy mandates 7 days).
   - **Insufficient Information:** Answers acknowledging lack of policy coverage.
3. Participants choose between:
   - *1. Answer is supported*
   - *2. Answer contains an error*
   - *3. Not enough information*
4. Telemetry records:
   - **Error Catch Rate (%):** `(Correctly detected injected errors / Total injected-error scenarios) × 100`
   - **Response Time (ms):** Time taken by user to evaluate the scenario.
   - **Source View Rate (%):** Frequency with which participants opened the supporting document before submitting their decision.
   - **False Alarm Rate:** Number of times a supported response was incorrectly marked as an error.

---

## 9. Installation & Running Instructions

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Node.js 18+ & npm

### Backend Setup
1. Open a terminal in the project directory:
   ```bash
   cd "/home/techpark-4/project2/SAFE CUSTOMER SUPPORT RAG CHATBOT"
   ```
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Install backend dependencies (already installed in venv):
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI backend server:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   The backend API will run at: `http://localhost:8000`  
   Interactive API docs (Swagger UI): `http://localhost:8000/docs`

### Frontend Setup
1. In a second terminal, navigate to the frontend:
   ```bash
   cd "/home/techpark-4/project2/SAFE CUSTOMER SUPPORT RAG CHATBOT/frontend"
   ```
2. Install frontend dependencies (if not already installed):
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The web application will run at: `http://localhost:5173`

---

## 10. Environment Configuration (`.env`)

Configure the backend via `.env` or system environment variables:

```ini
# Storage paths
DATABASE_PATH="./data/app.db"
VECTOR_DB_PATH="./data/vectorstore"
DOCUMENTS_DIR="./data/documents"

# LLM Provider: "local" (default offline synthesizer), "gemini", or "openai"
LLM_PROVIDER="local"

# Optional External API Keys:
GEMINI_API_KEY=""
OPENAI_API_KEY=""
LLM_MODEL="gpt-4o-mini"

# Safety & Retrieval Settings
TOP_K_CHUNKS=4
SIMILARITY_THRESHOLD_HIGH=0.60
SIMILARITY_THRESHOLD_MODERATE=0.40
SIMILARITY_THRESHOLD_LOW=0.20
```

---

## 11. API Documentation Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/chat` | Submit question, run RAG, calculate confidence, return answer & sources |
| `GET` | `/api/chat/sessions` | List customer chat sessions |
| `GET` | `/api/chat/sessions/{id}` | Retrieve messages and sources for a session |
| `DELETE` | `/api/chat/sessions/{id}` | Delete a chat session |
| `GET` | `/api/documents` | List uploaded documents with status and chunk counts |
| `POST` | `/api/documents/upload` | Upload PDF/TXT/DOCX, extract text, chunk and index in ChromaDB |
| `DELETE` | `/api/documents/{id}` | Delete document and remove chunk vectors from ChromaDB |
| `POST` | `/api/documents/reindex` | Re-index all documents in knowledge base |
| `GET` | `/api/documents/{id}/chunks`| Inspect text chunks of a specific document |
| `GET` | `/api/sources/{id}` | Inspect raw chunk text and metadata by chunk ID |
| `POST` | `/api/feedback` | Submit helpful/unhelpful rating and detailed error reasons |
| `POST` | `/api/study/start` | Initialize a controlled user-study session |
| `POST` | `/api/study/response` | Record participant decision, time, and source view status |
| `GET` | `/api/study/results` | Compute aggregate study metrics (Error Catch Rate, etc.) |
| `GET` | `/api/dashboard` | Retrieve overall telemetry for Admin Dashboard |
| `GET` | `/api/health` | Service health status |

---

## 12. Automated Testing
Run the complete test suite:
```bash
source venv/bin/activate
pytest tests/test_backend.py -v
```

All 7 test suites verify:
- Health check & ChromaDB connectivity
- Sample document indexing & retrieval
- Accurate source citation for supported questions
- Hallucination refusal for unsupported queries
- Detailed feedback submissions
- User study response tracking & Error Catch Rate calculations
- Admin dashboard telemetry aggregations

---

## 13. Preloaded Sample Company Documents
The system automatically includes, parses, and indexes 7 multi-page PDF company documents:
1. `Refund Policy.pdf` (Return eligibility, 7-day window, restocking fees, condition guidelines)
2. `Shipping Policy.pdf` (Ground, express, overnight timelines, $50 free shipping threshold, international delivery)
3. `Product Information.pdf` (NovaBook specifications, Torx T5 RAM upgrades, battery GaN charger, display specs)
4. `Warranty Policy.pdf` (1-year manufacturer warranty, 90-day refurbished warranty, exclusions)
5. `Cancellation Policy.pdf` (60-minute cancellation window, in-transit cancellation rules, fees)
6. `Customer FAQ.pdf` (Support channels, password reset, warehouse visitation notice, account management)
7. `Return Policy.pdf` (RMA authorization, inspection procedures, return packaging instructions)

---

## 14. Phased Implementation Progress & Verification Tracker

| Phase | Description | Key Deliverables & Implemented Features | Status |
| :--- | :--- | :--- | :---: |
| **Phase 0** | **Project Inspection & Planning** | Architecture audit, project directory inspection, dependency validation (`requirements.txt`, `package.json`), environment template (`.env.example`), and development roadmap. | `VERIFIED` |
| **Phase 1** | **Basic Full-Stack Application** | FastAPI application setup, SQLite database initialization (`data/app.db`), health check endpoint (`/api/health`), React 18 TypeScript frontend with responsive SaaS layout and navigation. | `VERIFIED` |
| **Phase 2** | **Document Management & RAG Knowledge Base** | Multi-format parser (PDF, DOCX, TXT, MD), sliding-window text chunker with page attribution, ChromaDB vector store with hybrid subword vectorizer and BM25-style keyword re-ranking, document upload/deletion/reindexing endpoints. | `VERIFIED` |
| **Phase 3** | **Modular LLM Integration & Grounded Synthesis** | Multi-provider architecture (Local Grounded Synthesizer with zero external dependencies, Google Gemini 1.5 Flash, and OpenAI GPT-4o-mini), context-grounded extractive response synthesis, safe refusal on unindexed queries. | `VERIFIED` |
| **Phase 4** | **AI Safety, Uncertainty & Transparency** | Calibrated 4-tier confidence engine (*High*, *Moderate*, *Low*, *Unable to determine*), persistent automation-bias warnings, non-human AI identity safeguards, interactive `SourceModal` with similarity scores. | `VERIFIED` |
| **Phase 5** | **Feedback, Verification & Human Escalation** | Granular user feedback ratings with category tags (`incorrect_info`, `unsupported_source`, etc.), user verification tracking, one-click human escalation with automated conversation summary. | `VERIFIED` |
| **Phase 6** | **Safety Lab / Controlled Testing Module** | Dedicated evaluation suite with 6 controlled scenarios (accurate policies, injected error edge cases, insufficient information), response time telemetry, and automated Error Catch Rate calculation. | `VERIFIED` |
| **Phase 7** | **A/B Testing Framework for Safety UI** | Split-testing engine comparing Condition A (standard chatbot baseline) vs. Condition B (safety-enhanced UI with prominent confidence badges and mandatory source reminders), comparative catch rate metrics. | `VERIFIED` |
| **Phase 8** | **Analytics Dashboard & Risk Register** | Executive telemetry dashboard (session statistics, question counts, satisfaction ratings, A/B performance) and formal AI Safety Risk Matrix monitoring 5 critical failure modes with mitigation tracking. | `VERIFIED` |
| **Phase 9** | **Advanced Security & Multilingual Support** | `PromptGuard` defense against prompt injections, system prompt leaks, and delimiter breakouts; cross-lingual RAG expansion for Tamil (தமிழ்) with domain-specific keyword translation and synthesized Tamil responses. | `VERIFIED` |
| **Phase 10** | **End-to-End Verification & Presentation Prep** | Full test suite execution: 10/10 pytest unit tests passing, 18/18 live system integration tests passing with 0 errors, Vite production build verified (`0 errors`), and clean GitHub synchronization. | `VERIFIED` |
| **Phase 11** | **Production-Style Custom Guardrails System** | Multi-layer custom guardrail architecture (`InputGuard`, `PromptGuard`, `OutputGuard`, `SafetyGuard`, `Pipeline`, `AuditLogger`), SQLite audit log stream (`guardrail_events`), 8-scenario interactive AI Safety Testing Lab, and full 12/12 automated guardrail test cases passing. | `VERIFIED` |

---

## 15. SafeSupport AI Custom Guardrail System Architecture

SafeSupport AI implements a defense-in-depth **custom guardrails architecture** designed to eliminate overreliance, automation bias, anthropomorphization, hallucinated customer-support answers, and prompt injection attacks.

```
       [ Incoming User Request ]
                  │
                  ▼
       ┌──────────────────────┐
       │   1. INPUT GUARD     │ ──> PII Guard (redacts phone/email/cards/SSN)
       │                      │ ──> Domain Guard (blocks coding, creative writing, homework)
       │                      │ ──> Rate Limit Guard (sliding-window per IP/client)
       └──────────┬───────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │   2. PROMPT GUARD    │ ──> Prompt Injection Guard (blocks jailbreaks, prompt leaks)
       │                      │ ──> Context Boundary Guard (wraps untrusted company docs)
       └──────────┬───────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │   3. RETRIEVAL &     │ ──> Evidence-Only Guard (minimum 0.30 relevance threshold)
       │      EVIDENCE GUARD  │ ──> Abstention Guard (deterministic safe refusal if missing)
       └──────────┬───────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │   4. OUTPUT GUARD    │ ──> Evidence Consistency Guard (extracts & cross-checks numbers/terms)
       │                      │ ──> Contradiction Detection (abstains if answer conflicts with policy)
       │                      │ ──> Confidence Guard (calibrated HIGH / MEDIUM / LOW / UNABLE)
       │                      │ ──> Source Attribution Guard (validated document & page metadata)
       └──────────┬───────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │   5. HUMAN SAFETY    │ ──> Human Escalation Guard (handoff on dispute, low confidence, or request)
       │      & ESCALATION    │ ──> Action Confirmation Guard (INFORM -> CONFIRM -> ACT for orders/deletion)
       │                      │ ──> AI Identity Disclosure ("I am an AI assistant...")
       └──────────┬───────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │   6. AUDIT & LAB     │ ──> Real-time SQLite Audit Logger (`guardrail_events` table)
       │                      │ ──> AI Safety Testing Lab (8 interactive scenario tests)
       │                      │ ──> Automation Bias User Study (A/B research evaluation)
       └──────────────────────┘
```

### Supported Guardrail Scenarios (AI Safety Testing Lab)
1. **Normal Supported Question:** Verifies legitimate refund/shipping questions retrieve sources with HIGH confidence.
2. **Missing Evidence (Abstention):** Refuses to hallucinate on missing policies (e.g., Martian crypto) and safely abstains.
3. **Prompt Injection Defense:** Blocks jailbreak attempts, delimiter breakouts, and prompt extraction.
4. **Sensitive PII Input:** Redacts phone numbers, emails, credit cards, and SSNs with user-facing safety warnings.
5. **Out-of-Domain Scope Enforcement:** Rejects queries unrelated to customer support (coding, essays, etc.).
6. **Evidence Contradiction Detection:** Detects fabricated numbers (e.g., claiming 30 days when policy states 7 days) and triggers abstention.
7. **Low Evidence & Human Escalation:** Offers one-click escalation to human representatives when evidence is weak or requested.
8. **High-Impact Action Confirmation:** Enforces `INFORM → CONFIRM → ACT` on sensitive operations like order cancellation or account deletion.

