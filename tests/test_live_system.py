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
        assert data["confidence"] in ["High", "Moderate"], f"Unexpected confidence: {data['confidence']}"
        assert len(data["sources"]) > 0, "Sources should not be empty"
        assert "7" in data["content"] or "calendar days" in data["content"], "Answer should cite 7 calendar days"
        session_id = data["session_id"]
        ai_msg_id = data["id"]
        print(f"✓ Chat Supported Question Passed (Confidence: {data['confidence']}, Sources: {len(data['sources'])})")
    except Exception as e:
        errors.append(f"Chat Supported Question: {e}")

    # 4. Test Chat - Unsupported Question (Out of domain / Hallucination prevention)
    try:
        payload = {"message": "What is the cryptocurrency payment policy?"}
        r = requests.post(f"{BASE_BACKEND}/api/chat", json=payload, timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        assert data["confidence"] == "Unable to determine", f"Expected 'Unable to determine', got {data['confidence']}"
        assert len(data["sources"]) == 0, f"Expected 0 sources for unsupported question, got {len(data['sources'])}"
        assert "couldn't find sufficient information" in data["content"].lower(), "Expected safe refusal message"
        print("✓ Chat Unsupported Question Safe Refusal Passed")
    except Exception as e:
        errors.append(f"Chat Unsupported Question: {e}")

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
        assert new_ans["confidence"] in ["High", "Moderate"]
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

    print("\n--- TEST SUMMARY ---")
    if not errors:
        print("ALL TESTS PASSED! ZERO CRITICAL ERRORS FOUND.")
    else:
        print(f"FOUND {len(errors)} ERRORS:")
        for err in errors:
            print("  ❌", err)

if __name__ == "__main__":
    run_tests()
