import pytest
import os
import json
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.db import init_db, execute_query
from backend.app.api.documents import initialize_sample_documents_if_empty

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()
    initialize_sample_documents_if_empty()
    yield

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "ChromaDB" in data["vector_db"]

def test_list_documents(client):
    response = client.get("/api/documents")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) >= 5
    filenames = [d["filename"] for d in docs]
    assert any("Refund" in f for f in filenames)
    assert any("Shipping" in f for f in filenames)

def test_chat_supported_question(client):
    payload = {
        "message": "How long do I have to request a refund?",
        "user_id": "test-user"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "assistant"
    assert data["confidence"] in ["High", "Moderate"]
    assert len(data["sources"]) > 0
    assert any("Refund" in s["document_name"] for s in data["sources"])
    assert data["verification_notice"] is not None

def test_chat_unsupported_question(client):
    payload = {
        "message": "What is the Martian cryptocurrency staking interest rate?",
        "user_id": "test-user"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] == "Unable to determine"
    assert len(data["sources"]) == 0
    assert "couldn't find sufficient information" in data["content"].lower()

def test_feedback_submission(client):
    # Ask a question to get a message id
    chat_resp = client.post("/api/chat", json={"message": "What is the warranty period for refurbished units?"})
    ai_msg = chat_resp.json()
    
    # Submit helpful feedback
    fb_payload = {
        "session_id": ai_msg["session_id"],
        "message_id": ai_msg["id"],
        "feedback_type": "helpful",
        "comment": "Accurately cited 90-day warranty"
    }
    fb_resp = client.post("/api/feedback", json=fb_payload)
    assert fb_resp.status_code == 200
    fb_data = fb_resp.json()
    assert fb_data["feedback_type"] == "helpful"
    
    # Submit detailed unhelpful feedback
    fb_unhelpful = {
        "session_id": ai_msg["session_id"],
        "message_id": ai_msg["id"],
        "feedback_type": "unhelpful",
        "reason": "incorrect_info",
        "comment": "Testing error report"
    }
    fb_resp2 = client.post("/api/feedback", json=fb_unhelpful)
    assert fb_resp2.status_code == 200
    assert fb_resp2.json()["reason"] == "incorrect_info"

def test_study_flow_and_metrics(client):
    # 1. Start study session
    start_resp = client.post("/api/study/start", json={"participant_name": "Test Evaluator"})
    assert start_resp.status_code == 200
    study_data = start_resp.json()
    session_id = study_data["study_session_id"]
    scenarios = study_data["scenarios"]
    assert len(scenarios) >= 5

    # 2. Answer scenarios
    for sc in scenarios:
        # Intentionally select correct answer
        resp_payload = {
            "study_session_id": session_id,
            "scenario_id": sc["id"],
            "question": sc["customer_question"],
            "ai_answer": sc["ai_answer"],
            "has_injected_error": sc["has_injected_error"],
            "selected_answer": sc["expected_answer"],
            "expected_answer": sc["expected_answer"],
            "response_time_ms": 3200,
            "source_viewed": True
        }
        r = client.post("/api/study/response", json=resp_payload)
        assert r.status_code == 200
        assert r.json()["is_correct"] is True

    # 3. Check metrics calculation
    metrics_resp = client.get("/api/study/results")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert metrics["total_participants"] >= 1
    assert metrics["error_catch_rate_percent"] >= 90.0

def test_dashboard_metrics(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total_conversations"] >= 1
    assert stats["total_questions"] >= 1
    assert stats["total_documents"] >= 5
    assert "feedback_distribution" in stats
    assert "confidence_distribution" in stats
    assert "condition_a_catch_rate" in stats
    assert "condition_b_catch_rate" in stats

def test_escalations_flow(client):
    payload = {
        "customer_name": "Jane Doe",
        "email": "jane@example.com",
        "question": "My order #1234 arrived damaged, what are my options?",
        "reason": "Need human assistance"
    }
    resp = client.post("/api/escalations", json=payload)
    assert resp.status_code == 200
    esc = resp.json()
    assert esc["customer_name"] == "Jane Doe"
    assert esc["status"] == "Pending"
    assert esc["conversation_summary"] is not None
    assert len(esc["conversation_summary"]) > 10

    list_resp = client.get("/api/escalations")
    assert list_resp.status_code == 200
    all_esc = list_resp.json()
    assert len(all_esc) >= 1
    assert any(e["email"] == "jane@example.com" for e in all_esc)

def test_risk_register(client):
    resp = client.get("/api/risk-register")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 4
    risks = [i["risk"] for i in items]
    categories = [i["category"] for i in items]
    assert "Automation Bias" in risks
    assert "Overreliance on AI" in risks
    assert "Safety" in categories

def test_tamil_chat_response(client):
    payload = {
        "message": "பணம் திரும்பப் பெறுவதற்கான நிபந்தனைகள் என்ன?",
        "language": "ta"
    }
    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "assistant"
    assert data["language"] == "ta"
    assert len(data["content"]) > 10

