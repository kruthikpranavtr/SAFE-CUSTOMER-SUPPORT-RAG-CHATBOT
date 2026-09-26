from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SourceItem(BaseModel):
    document_name: str
    page_number: Optional[int] = 1
    chunk_id: str
    content_snippet: str
    similarity_score: float

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Customer question")
    session_id: Optional[str] = None
    user_id: Optional[str] = "demo-user"

class ChatMessage(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    confidence: Optional[str] = None
    sources: Optional[List[SourceItem]] = []
    verification_notice: Optional[str] = None
    retrieval_score: Optional[float] = None
    created_at: str

class ChatSessionInfo(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    messages: Optional[List[ChatMessage]] = []

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

# Study Models
class StudyScenario(BaseModel):
    id: str
    title: str
    customer_question: str
    ai_answer: str
    sources: List[SourceItem]
    has_injected_error: bool
    error_description: Optional[str] = None
    expected_answer: str  # "supported", "error", "insufficient"
    category: str

class StudyStartRequest(BaseModel):
    participant_name: Optional[str] = "Anonymous Participant"

class StudyStartResponse(BaseModel):
    study_session_id: str
    participant_id: str
    scenarios: List[StudyScenario]

class StudyResponseRequest(BaseModel):
    study_session_id: str
    scenario_id: str
    question: str
    ai_answer: str
    has_injected_error: bool
    selected_answer: str  # "supported", "error", "insufficient"
    expected_answer: str
    response_time_ms: int
    source_viewed: bool

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

class DashboardStats(BaseModel):
    total_conversations: int
    total_questions: int
    total_documents: int
    total_feedback: int
    helpful_responses: int
    reported_incorrect_responses: int
    user_study_participants: int
    error_catch_rate: float
    source_view_rate: float
    feedback_distribution: Dict[str, int]
    confidence_distribution: Dict[str, int]
    error_detection_breakdown: Dict[str, int]
