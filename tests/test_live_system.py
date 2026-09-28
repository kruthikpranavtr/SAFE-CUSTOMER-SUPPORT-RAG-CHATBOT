import requests
import json
import time
import io

BASE_BACKEND = "http://127.0.0.1:8001"
BASE_FRONTEND_PROXY = "http://127.0.0.1:5173"

def run_tests():
    errors = []
    print("--- STARTING LIVE SYSTEM TESTING ---")

    # 1. Test Backend Health
    try:
        r = requests.get(f"{BASE_BACKEND}/api/health", timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        assert data["status"] == "healthy", f"Expected healthy status, got {data}"
        print("✓ Health Check Passed")
    except Exception as e:
        errors.append(f"Backend Health Check: {e}")

    # 2. Test Frontend Proxy
    try:
        r = requests.get(f"{BASE_FRONTEND_PROXY}/api/health", timeout=5)
        assert r.status_code == 200, f"Expected 200 via proxy, got {r.status_code}"
        print("✓ Frontend API Proxy Passed")
    except Exception as e:
        errors.append(f"Frontend Proxy Check: {e}")

    # 3. Test Chat - Supported Question
    session_id = None
    ai_msg_id = None
    try:
        payload = {"message": "How long do I have to request a refund?"}
        r = requests.post(f"{BASE_BACKEND}/api/chat", json=payload, timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["role"] == "assistant", "Role should be assistant"
        assert data["confidence"] in ["HIGH", "High", "Moderate"], f"Unexpected confidence: {data['confidence']}"
        assert len(data["sources"]) > 0, "Sources should not be empty"
        assert "7" in data["content"] or "calendar days" in data["content"], "Answer should cite 7 calendar days"
        session_id = data["session_id"]
        ai_msg_id = data["id"]
        print(f"✓ Chat Supported Question Passed (Confidence: {data['confidence']}, Sources: {len(data['sources'])})")
    except Exception as e:
        errors.append(f"Chat Supported Question: {e}")

    # 4. Test Chat - Unsupported Question (Out of domain / Hallucination prevention)
    try:
        payload = {"message": "What is the Martian cryptocurrency staking interest rate?"}
        r = requests.post(f"{BASE_BACKEND}/api/chat", json=payload, timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        assert data["confidence"] in ["UNABLE_TO_DETERMINE", "Unable to determine"], f"Expected 'UNABLE_TO_DETERMINE', got {data['confidence']}"
        assert len(data["sources"]) == 0, f"Expected 0 sources for unsupported question, got {len(data['sources'])}"
        assert "couldn't" in data["content"].lower() or "insufficient" in data["content"].lower() or "verify" in data["content"].lower(), "Expected safe refusal message"
        print("✓ Chat Unsupported Question Safe Refusal Passed")
    except Exception as e:
        errors.append(f"Chat Unsupported Question: {repr(e)}")

    # 5. Test Chat - Empty Message Validation
    try:
        payload = {"message": "   "}
        r = requests.post(f"{BASE_BACKEND}/api/chat", json=payload, timeout=5)
        assert r.status_code == 400, f"Expected 400 for empty message, got {r.status_code}"
        print("✓ Chat Empty Input Validation Passed (400 Bad Request)")
    except Exception as e:
        errors.append(f"Chat Empty Input Validation: {e}")

    # 6. Test Chat - Session Persistence & Retrieval
    if session_id:
        try:
            r = requests.get(f"{BASE_BACKEND}/api/chat/sessions/{session_id}", timeout=5)
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            sess = r.json()
            assert len(sess["messages"]) >= 2, f"Expected at least 2 messages in session, got {len(sess['messages'])}"
            print(f"✓ Chat Session Persistence Passed ({len(sess['messages'])} messages)")
        except Exception as e:
            errors.append(f"Chat Session Persistence: {e}")

    # 6b. Test Bulk Session Deletion (Checkbox Multi-Delete)
    try:
        r_temp1 = requests.post(f"{BASE_BACKEND}/api/chat", json={"message": "Temporary test query 1", "user_id": "live-test-user"}, timeout=10)
        r_temp2 = requests.post(f"{BASE_BACKEND}/api/chat", json={"message": "Temporary test query 2", "user_id": "live-test-user"}, timeout=10)
        t_id1 = r_temp1.json()["session_id"]
        t_id2 = r_temp2.json()["session_id"]
        
        r_bulk = requests.post(f"{BASE_BACKEND}/api/chat/sessions/bulk-delete", json={"session_ids": [t_id1, t_id2]}, timeout=5)
        assert r_bulk.status_code == 200, f"Expected 200 for bulk-delete, got {r_bulk.status_code}"
        assert r_bulk.json()["deleted_count"] == 2, f"Expected 2 deleted, got {r_bulk.json()}"
        print("✓ Chat Bulk Session Deletion (Checkbox Multi-Select) Passed")
    except Exception as e:
        errors.append(f"Chat Bulk Session Deletion: {e}")

    # 7. Test Sources Inspection
    try:
        # Get first document chunks to find a valid chunk id
        r_docs = requests.get(f"{BASE_BACKEND}/api/documents", timeout=5)
        docs = r_docs.json()
        assert len(docs) > 0, "No documents found"
        doc_id = docs[0]["id"]
        
        r_chunks = requests.get(f"{BASE_BACKEND}/api/documents/{doc_id}/chunks", timeout=5)
        chunks = r_chunks.json()["chunks"]
        assert len(chunks) > 0, "No chunks found in document"
        first_chunk_id = chunks[0]["chunk_id"]

        # Test valid chunk lookup
        r_source = requests.get(f"{BASE_BACKEND}/api/sources/{first_chunk_id}", timeout=5)
        assert r_source.status_code == 200, f"Expected 200 for valid chunk, got {r_source.status_code}"
        source_data = r_source.json()
        assert source_data["chunk_id"] == first_chunk_id, "Chunk id mismatch"
        print("✓ Valid Source Chunk Inspection Passed")

        # Test invalid chunk lookup
        r_inv = requests.get(f"{BASE_BACKEND}/api/sources/non_existent_chunk_12345", timeout=5)
        assert r_inv.status_code == 404, f"Expected 404 for invalid chunk, got {r_inv.status_code}"
        print("✓ Invalid Source Chunk 404 Handling Passed")
    except Exception as e:
        errors.append(f"Sources Inspection: {e}")

    # 8. Test Document Upload, Search, and Deletion
    uploaded_doc_id = None
    try:
        # Create a mock policy document
        test_content = (
            "[DEMO POLICY]\nDOCUMENT: Quantum Fleet Travel Policy\n"
            "SECTION 1: TRAVEL CREDITS (Page 1)\n"
            "Quantum hyperloop travelers are entitled to a 500-credit voucher if arrival is delayed by more than 15 minutes."
        )
        files = {"file": ("quantum_travel_policy.txt", io.BytesIO(test_content.encode("utf-8")), "text/plain")}
        r_up = requests.post(f"{BASE_BACKEND}/api/documents/upload", files=files, timeout=10)
        assert r_up.status_code == 200, f"Expected 200 on upload, got {r_up.status_code}: {r_up.text}"
        uploaded_doc = r_up.json()
        uploaded_doc_id = uploaded_doc["id"]
        assert uploaded_doc["chunk_count"] > 0, "Uploaded document should have generated chunks"
        print(f"✓ Document Upload Passed (Doc ID: {uploaded_doc_id}, Chunks: {uploaded_doc['chunk_count']})")

        # Now ask a question that specifically relies on this newly uploaded document
        r_chat_new = requests.post(f"{BASE_BACKEND}/api/chat", json={"message": "What is the compensation voucher for quantum hyperloop arrival delay?"}, timeout=10)
        assert r_chat_new.status_code == 200
        new_ans = r_chat_new.json()
        assert new_ans["confidence"] in ["HIGH", "High", "Moderate"]
        assert "500-credit voucher" in new_ans["content"] or "15 minutes" in new_ans["content"]
        print("✓ RAG Retrieval on Newly Uploaded Document Passed")

        # Now delete the document
        r_del = requests.delete(f"{BASE_BACKEND}/api/documents/{uploaded_doc_id}", timeout=5)
        assert r_del.status_code == 200, f"Expected 200 on delete, got {r_del.status_code}"
        print("✓ Document Deletion & Vector Cleanup Passed")

        # Test uploading invalid file extension
        bad_file = {"file": ("malicious_script.exe", io.BytesIO(b"binary"), "application/octet-stream")}
        r_bad = requests.post(f"{BASE_BACKEND}/api/documents/upload", files=bad_file, timeout=5)
        assert r_bad.status_code == 400, f"Expected 400 for unsupported extension, got {r_bad.status_code}"
        print("✓ Upload Invalid File Extension 400 Validation Passed")
    except Exception as e:
        import traceback
        traceback.print_exc()
        errors.append(f"Document Upload & Deletion: {repr(e)}")

    # 9. Test Feedback Submission
    if session_id and ai_msg_id:
        try:
            fb_payload = {
                "session_id": session_id,
                "message_id": ai_msg_id,
                "feedback_type": "helpful"
            }
            r_fb1 = requests.post(f"{BASE_BACKEND}/api/feedback", json=fb_payload, timeout=5)
            assert r_fb1.status_code == 200, f"Expected 200, got {r_fb1.status_code}"
            
            fb_unhelpful = {
                "session_id": session_id,
                "message_id": ai_msg_id,
                "feedback_type": "unhelpful",
                "reason": "unsupported_source",
                "comment": "Testing issue report flow"
            }
            r_fb2 = requests.post(f"{BASE_BACKEND}/api/feedback", json=fb_unhelpful, timeout=5)
            assert r_fb2.status_code == 200, f"Expected 200, got {r_fb2.status_code}"
            print("✓ Feedback Submission (Helpful & Unhelpful) Passed")
        except Exception as e:
            errors.append(f"Feedback Submission: {e}")

    # 10. Test User Study Workflow
    try:
        r_start = requests.post(f"{BASE_BACKEND}/api/study/start", json={"participant_name": "QA Robot"}, timeout=5)
        assert r_start.status_code == 200, f"Expected 200, got {r_start.status_code}"
        study_session = r_start.json()
        study_id = study_session["study_session_id"]
        scenarios = study_session["scenarios"]
        assert len(scenarios) >= 5, f"Expected at least 5 scenarios, got {len(scenarios)}"
        print(f"✓ User Study Start Passed ({len(scenarios)} scenarios)")

        # Submit answers for all scenarios
        for sc in scenarios:
            resp_payload = {
                "study_session_id": study_id,
                "scenario_id": sc["id"],
                "question": sc["customer_question"],
                "ai_answer": sc["ai_answer"],
                "has_injected_error": sc["has_injected_error"],
                "selected_answer": sc["expected_answer"],  # Choose expected answer
                "expected_answer": sc["expected_answer"],
                "response_time_ms": 2500,
                "source_viewed": True
            }
            r_resp = requests.post(f"{BASE_BACKEND}/api/study/response", json=resp_payload, timeout=5)
            assert r_resp.status_code == 200, f"Expected 200, got {r_resp.status_code}"
            assert r_resp.json()["is_correct"] is True, "Expected correct answer"

        # Check aggregate metrics
        r_metrics = requests.get(f"{BASE_BACKEND}/api/study/results", timeout=5)
        assert r_metrics.status_code == 200
        metrics = r_metrics.json()
        assert metrics["total_participants"] >= 1
        assert metrics["error_catch_rate_percent"] >= 80.0
        print(f"✓ User Study Metrics Calculation Passed (Error Catch Rate: {metrics['error_catch_rate_percent']}%)")
    except Exception as e:
        errors.append(f"User Study Workflow: {e}")

    # 11. Test Admin Dashboard Telemetry
    try:
        r_dash = requests.get(f"{BASE_BACKEND}/api/dashboard", timeout=5)
        assert r_dash.status_code == 200, f"Expected 200, got {r_dash.status_code}"
        dash = r_dash.json()
        assert dash["total_conversations"] > 0
        assert dash["total_questions"] > 0
        assert dash["total_documents"] >= 5
        assert "feedback_distribution" in dash
        assert "confidence_distribution" in dash
        assert "error_detection_breakdown" in dash
        print(f"✓ Dashboard Telemetry Passed ({dash['total_questions']} questions, {dash['total_documents']} documents)")
    except Exception as e:
        errors.append(f"Admin Dashboard Telemetry: {e}")

    # 12. Test Human Escalation Handoff
    try:
        esc_payload = {
            "session_id": session_id,
            "customer_name": "Kavitha Raman",
            "email": "kavitha@example.com",
            "question": "Can I get an extension on the warranty period due to hospital emergency?",
            "reason": "Need human assistance"
        }
        r_esc = requests.post(f"{BASE_BACKEND}/api/escalations", json=esc_payload, timeout=5)
        assert r_esc.status_code == 200, f"Expected 200, got {r_esc.status_code}"
        esc_data = r_esc.json()
        assert esc_data["status"] == "Pending"
        assert esc_data["conversation_summary"] is not None
        assert len(esc_data["conversation_summary"]) > 10

        r_esc_list = requests.get(f"{BASE_BACKEND}/api/escalations", timeout=5)
        assert r_esc_list.status_code == 200
        assert len(r_esc_list.json()) > 0
        print("✓ Human Escalation & Auto-Summary Passed")
    except Exception as e:
        errors.append(f"Human Escalation: {e}")

    # 13. Test Risk Register Matrix
    try:
        r_risk = requests.get(f"{BASE_BACKEND}/api/risk-register", timeout=5)
        assert r_risk.status_code == 200, f"Expected 200, got {r_risk.status_code}"
        risks = r_risk.json()
        assert len(risks) >= 4, f"Expected at least 4 risk items, got {len(risks)}"
        risk_names = [item["risk"] for item in risks]
        assert "Overreliance on AI" in risk_names
        assert "Automation Bias" in risk_names
        print(f"✓ Risk Register Matrix Passed ({len(risks)} monitored risks)")
    except Exception as e:
        errors.append(f"Risk Register Matrix: {e}")

    # 14. Test Tamil Multilingual Chat
    try:
        ta_payload = {
            "message": "பணம் திரும்பப் பெறுவதற்கான விதிமுறைகள் என்ன?",
            "language": "ta"
        }
        r_ta = requests.post(f"{BASE_BACKEND}/api/chat", json=ta_payload, timeout=10)
        assert r_ta.status_code == 200, f"Expected 200, got {r_ta.status_code}"
        ta_data = r_ta.json()
        assert ta_data["role"] == "assistant"
        assert ta_data["language"] == "ta"
        assert len(ta_data["content"]) > 10
        assert ta_data["status"] in ["SUPPORTED", "ABSTAINED"]
        print("✓ Multilingual Chat (Tamil தமிழ்) Passed")
    except Exception as e:
        errors.append(f"Multilingual Chat (Tamil): {repr(e)}")

    # 15. Test Guardrail API & Safety Lab Scenarios
    try:
        r_stats = requests.get(f"{BASE_BACKEND}/api/guardrails/stats", timeout=5)
        assert r_stats.status_code == 200, f"Expected 200, got {r_stats.status_code}"
        g_stats = r_stats.json()
        assert "total_events" in g_stats
        assert g_stats["total_events"] > 0

        r_events = requests.get(f"{BASE_BACKEND}/api/guardrails/events?limit=10", timeout=5)
        assert r_events.status_code == 200
        assert len(r_events.json()) > 0

        test_types = [
            "NORMAL_QUESTION",
            "MISSING_EVIDENCE",
            "PROMPT_INJECTION",
            "PII_INPUT",
            "OUT_OF_DOMAIN",
            "EVIDENCE_CONTRADICTION",
            "LOW_EVIDENCE",
            "ACTION_CONFIRMATION"
        ]
        for t in test_types:
            r_test = requests.post(f"{BASE_BACKEND}/api/guardrails/test", json={"test_type": t}, timeout=10)
            assert r_test.status_code == 200, f"Test {t} returned status {r_test.status_code}"
            t_data = r_test.json()
            assert t_data["passed"] is True, f"Guardrail test '{t}' failed: expected {t_data['expected_result']}, got {t_data['actual_result']}"

        print("✓ Guardrail Statistics, Audit Events & All 8 Safety Lab Scenarios Passed")
    except Exception as e:
        import traceback
        traceback.print_exc()
        errors.append(f"Guardrails & Safety Lab: {repr(e)}")

    print("\n--- TEST SUMMARY ---")
    if not errors:
        print("ALL TESTS PASSED! ZERO CRITICAL ERRORS FOUND.")
    else:
        print(f"FOUND {len(errors)} ERRORS:")
        for err in errors:
            print("  ❌", err)

if __name__ == "__main__":
    run_tests()

