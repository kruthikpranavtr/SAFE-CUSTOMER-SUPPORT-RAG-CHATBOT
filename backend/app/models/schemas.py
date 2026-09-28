from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SourceItem(BaseModel):
    document_name: str
    page_number: Optional[int] = 1
    chunk_id: str
    content_snippet: str
    similarity_score: float

class EvidenceItem(BaseModel):
    document_name: str
    page_number: int
    relevance: str  # "High", "Medium", "Low"
    quote: str
    similarity_score: float

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Customer question")
    session_id: Optional[str] = None
    user_id: Optional[str] = "demo-user"
    language: Optional[str] = "en"  # "en" or "ta" (Tamil)

class ChatMessage(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    confidence: Optional[str] = None
    sources: Optional[List[SourceItem]] = []
    evidence_items: Optional[List[EvidenceItem]] = []
    verification_notice: Optional[str] = None
    retrieval_score: Optional[float] = None
    language: Optional[str] = "en"
    created_at: str

class ChatSessionInfo(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    messages: Optional[List[ChatMessage]] = []

class BulkDeleteSessionsRequest(BaseModel):
    session_ids: List[str]

class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_type: str
    file_path: Optional[str] = None
    status: str
    chunk_count: int
    file_size: int
    uploaded_at: str

class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: Optional[int] = 1
    text: str

class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    feedback_type: str  # "helpful" or "unhelpful"
    reason: Optional[str] = None  # "incorrect_info", "unsupported_source", "unclear", "missing_info", "other"
    comment: Optional[str] = None

class FeedbackInfo(BaseModel):
    id: str
    session_id: str
    message_id: str
    feedback_type: str
    reason: Optional[str] = None
    comment: Optional[str] = None
    created_at: str

class EscalationRequest(BaseModel):
    session_id: Optional[str] = None
    customer_name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    question: str = Field(..., min_length=1)
    conversation_summary: Optional[str] = None
    reason: str  # "AI answer seems incorrect", "Information not available", "Need human assistance", "Billing issue", "Other"

class EscalationInfo(BaseModel):
    id: str
    session_id: Optional[str] = None
    customer_name: str
    email: str
    question: str
    conversation_summary: Optional[str] = None
    reason: str
    status: str
    created_at: str

# Study Models (with A/B testing support)
class StudyScenario(BaseModel):
    id: str
    title: str
    customer_question: str
    ai_answer: str
    sources: List[SourceItem]
    evidence_items: List[EvidenceItem]
    has_injected_error: bool
    error_description: Optional[str] = None
    expected_answer: str  # "supported", "error", "insufficient"
    category: str

class StudyStartRequest(BaseModel):
    participant_name: Optional[str] = "Anonymous Participant"
    condition: Optional[str] = "B"  # "A" (baseline) or "B" (safety-enhanced)

class StudyStartResponse(BaseModel):
    study_session_id: str
    participant_id: str
    condition: str
    scenarios: List[StudyScenario]

class StudyResponseRequest(BaseModel):
    study_session_id: str
    scenario_id: str
    study_condition: Optional[str] = "B"
    question: str
    ai_answer: str
    has_injected_error: bool
    selected_answer: str  # "supported", "error", "insufficient"
    expected_answer: str
    response_time_ms: int
    source_viewed: bool
    evidence_viewed: Optional[bool] = False

class StudyMetrics(BaseModel):
    total_participants: int
    total_scenarios_tested: int
    injected_error_scenarios: int
    correctly_detected_errors: int
    missed_errors: int
    false_alarms: int
    error_catch_rate_percent: float
    avg_response_time_seconds: float
    source_view_rate_percent: float
    evidence_view_rate_percent: float
    condition_a_catch_rate: float
    condition_b_catch_rate: float

class RiskItem(BaseModel):
    id: str
    risk: str
    category: str
    status: str
    mitigation: str
    test_coverage: str

class DashboardStats(BaseModel):
    total_conversations: int
    total_questions: int
    total_documents: int
    total_chunks: int
    total_feedback: int
    total_escalations: int
    helpful_responses: int
    reported_incorrect_responses: int
    user_study_participants: int
    error_catch_rate: float
    source_view_rate: float
    evidence_view_rate: float
    condition_a_catch_rate: float
    condition_b_catch_rate: float
    feedback_distribution: Dict[str, int]
    confidence_distribution: Dict[str, int]
    error_detection_breakdown: Dict[str, int]
