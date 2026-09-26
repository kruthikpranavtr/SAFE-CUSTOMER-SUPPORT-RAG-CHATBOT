import {
  ChatMessage,
  ChatSessionInfo,
  DocumentInfo,
  DocumentChunk,
  FeedbackRequest,
  FeedbackInfo,
  StudyStartResponse,
  StudyResponseResult,
  StudyMetrics,
  DashboardStats
} from '../types';

const API_BASE = '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = 'Network response was not ok';
    try {
      const errorJson = await res.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      errorDetail = res.statusText || errorDetail;
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Chat
  async sendMessage(message: string, sessionId?: string): Promise<ChatMessage> {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId })
    });
    return handleResponse<ChatMessage>(res);
  },

  async getSessions(): Promise<ChatSessionInfo[]> {
    const res = await fetch(`${API_BASE}/chat/sessions`);
    return handleResponse<ChatSessionInfo[]>(res);
  },

  async getSession(sessionId: string): Promise<ChatSessionInfo> {
    const res = await fetch(`${API_BASE}/chat/sessions/${sessionId}`);
    return handleResponse<ChatSessionInfo>(res);
  },

  async deleteSession(sessionId: string): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
      method: 'DELETE'
    });
    return handleResponse<{ status: string }>(res);
  },

  // Documents
  async getDocuments(): Promise<DocumentInfo[]> {
    const res = await fetch(`${API_BASE}/documents`);
    return handleResponse<DocumentInfo[]>(res);
  },

  async uploadDocument(file: File): Promise<DocumentInfo> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData
    });
    return handleResponse<DocumentInfo>(res);
  },

  async deleteDocument(id: string): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE}/documents/${id}`, {
      method: 'DELETE'
    });
    return handleResponse<{ status: string }>(res);
  },

  async reindexDocuments(): Promise<{ status: string; documents_reindexed: number; total_chunks: number }> {
    const res = await fetch(`${API_BASE}/documents/reindex`, {
      method: 'POST'
    });
    return handleResponse<{ status: string; documents_reindexed: number; total_chunks: number }>(res);
  },

  async getDocumentChunks(id: string): Promise<{ document_id: string; chunk_count: number; chunks: DocumentChunk[] }> {
    const res = await fetch(`${API_BASE}/documents/${id}/chunks`);
    return handleResponse<{ document_id: string; chunk_count: number; chunks: DocumentChunk[] }>(res);
  },

  async getSourceChunk(chunkId: string): Promise<DocumentChunk> {
    const res = await fetch(`${API_BASE}/sources/${chunkId}`);
    return handleResponse<DocumentChunk>(res);
  },

  // Feedback
  async submitFeedback(data: FeedbackRequest): Promise<FeedbackInfo> {
    const res = await fetch(`${API_BASE}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return handleResponse<FeedbackInfo>(res);
  },

  // User Study
  async startStudy(name: string = 'Participant'): Promise<StudyStartResponse> {
    const res = await fetch(`${API_BASE}/study/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ participant_name: name })
    });
    return handleResponse<StudyStartResponse>(res);
  },

  async submitStudyResponse(payload: {
    study_session_id: string;
    scenario_id: string;
    question: string;
    ai_answer: string;
    has_injected_error: boolean;
    selected_answer: string;
    expected_answer: string;
    response_time_ms: number;
    source_viewed: boolean;
  }): Promise<StudyResponseResult> {
    const res = await fetch(`${API_BASE}/study/response`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse<StudyResponseResult>(res);
  },

  async getStudyMetrics(): Promise<StudyMetrics> {
    const res = await fetch(`${API_BASE}/study/results`);
    return handleResponse<StudyMetrics>(res);
  },

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    const res = await fetch(`${API_BASE}/dashboard`);
    return handleResponse<DashboardStats>(res);
  },

  // Health
  async getHealth(): Promise<{ status: string; app: string; llm_provider: string; vector_db: string }> {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse<{ status: string; app: string; llm_provider: string; vector_db: string }>(res);
  }
};
