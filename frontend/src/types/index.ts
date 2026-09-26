export interface SourceItem {
  document_name: string;
  page_number: number;
  chunk_id: string;
  content_snippet: string;
  similarity_score: number;
}

export interface EvidenceItem {
  document_name: string;
  page_number: number;
  relevance: 'High' | 'Medium' | 'Low';
  quote: string;
  similarity_score: number;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  confidence?: 'High' | 'Moderate' | 'Low' | 'Unable to determine' | null;
  sources?: SourceItem[];
  evidence_items?: EvidenceItem[];
  verification_notice?: string | null;
  retrieval_score?: number | null;
  language?: string;
  created_at: string;
}

export interface ChatSessionInfo {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: ChatMessage[];
}

export interface DocumentInfo {
  id: string;
  filename: string;
  file_type: string;
  file_path?: string;
  status: 'Ready' | 'Processing' | 'Error';
  chunk_count: number;
  file_size: number;
  uploaded_at: string;
}

export interface DocumentChunk {
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_number: number;
  text: string;
}

export interface FeedbackRequest {
  session_id: string;
  message_id: string;
  feedback_type: 'helpful' | 'unhelpful';
  reason?: string;
  comment?: string;
}

export interface FeedbackInfo {
  id: string;
  session_id: string;
  message_id: string;
  feedback_type: string;
  reason?: string;
  comment?: string;
  created_at: string;
}

export interface EscalationRequest {
  session_id?: string;
  customer_name: string;
  email: string;
  question: string;
  conversation_summary?: string;
  reason: string;
}

export interface EscalationInfo {
  id: string;
  session_id?: string;
  customer_name: string;
  email: string;
  question: string;
  conversation_summary?: string;
  reason: string;
  status: string;
  created_at: string;
}

export interface RiskItem {
  id: string;
  risk: string;
  category: string;
  status: string;
  mitigation: string;
  test_coverage: string;
}

export interface StudyScenario {
  id: string;
  title: string;
  customer_question: string;
  ai_answer: string;
  sources: SourceItem[];
  evidence_items: EvidenceItem[];
  has_injected_error: boolean;
  error_description?: string | null;
  expected_answer: 'supported' | 'error' | 'insufficient';
  category: string;
}

export interface StudyStartResponse {
  study_session_id: string;
  participant_id: string;
  condition: 'A' | 'B';
  scenarios: StudyScenario[];
}

export interface StudyResponseResult {
  status: string;
  response_id: string;
  is_correct: boolean;
  expected_answer: string;
}

export interface StudyMetrics {
  total_participants: number;
  total_scenarios_tested: number;
  injected_error_scenarios: number;
  correctly_detected_errors: number;
  missed_errors: number;
  false_alarms: number;
  error_catch_rate_percent: number;
  avg_response_time_seconds: number;
  source_view_rate_percent: number;
  evidence_view_rate_percent: number;
  condition_a_catch_rate: number;
  condition_b_catch_rate: number;
}

export interface DashboardStats {
  total_conversations: number;
  total_questions: number;
  total_documents: number;
  total_chunks: number;
  total_feedback: number;
  total_escalations: number;
  helpful_responses: number;
  reported_incorrect_responses: number;
  user_study_participants: number;
  error_catch_rate: number;
  source_view_rate: number;
  evidence_view_rate: number;
  condition_a_catch_rate: number;
  condition_b_catch_rate: number;
  feedback_distribution: Record<string, number>;
  confidence_distribution: Record<string, number>;
  error_detection_breakdown: Record<string, number>;
}
