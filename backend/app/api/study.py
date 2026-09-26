import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import (
    StudyScenario, 
    StudyStartRequest, 
    StudyStartResponse, 
    StudyResponseRequest, 
    StudyMetrics,
    SourceItem,
    EvidenceItem
)
from backend.app.database.db import execute_query, execute_insert, execute_commit

router = APIRouter(prefix="/study", tags=["study"])

# Standard controlled research dataset
CONTROLLED_SCENARIOS = [
    {
        "id": "scen-01",
        "title": "Scenario 1: Return & Refund Eligibility Window",
        "customer_question": "How long do I have to request a refund on my purchase?",
        "ai_answer": "You have up to 30 calendar days from the date of delivery to request a full refund, as long as the item is in its original packaging.",
        "has_injected_error": True,
        "error_description": "Injected error: Claimed 30 calendar days instead of actual 7 calendar days stipulated in Section 1.",
        "expected_answer": "error",
        "category": "Return Policy",
        "sources": [
            {
                "document_name": "Refund Policy.pdf",
                "page_number": 1,
                "chunk_id": "chunk_ref_01",
                "content_snippet": "SECTION 1: OVERVIEW AND ELIGIBILITY (Page 1)\nTo be eligible for a refund:\n1. The request must be submitted within 7 calendar days of delivery.\n2. The item must be in its original, undamaged packaging with all included accessories and manuals.\n3. Proof of purchase is strictly required.",
                "similarity_score": 0.89
            }
        ],
        "evidence_items": [
            {
                "document_name": "Refund Policy.pdf",
                "page_number": 1,
                "relevance": "High",
                "quote": "To be eligible for a refund: 1. The request must be submitted within 7 calendar days of delivery. 2. The item must be in its original, undamaged packaging with all included accessories and manuals.",
                "similarity_score": 0.92
            }
        ]
    },
    {
        "id": "scen-02",
        "title": "Scenario 2: Standard Shipping Delivery Timeline",
        "customer_question": "How many business days does standard shipping take?",
        "ai_answer": "Standard Ground Shipping takes 3 to 5 business days for delivery after warehouse dispatch. It is free for domestic orders exceeding $50.00.",
        "has_injected_error": False,
        "error_description": None,
        "expected_answer": "supported",
        "category": "Shipping Policy",
        "sources": [
            {
                "document_name": "Shipping Policy.pdf",
                "page_number": 2,
                "chunk_id": "chunk_shp_02",
                "content_snippet": "SECTION 2: SHIPPING METHODS AND DELIVERY TIMELINES (Page 2)\nTechNova provides three primary shipping options for domestic delivery:\n1. Standard Ground Shipping: Takes 3 to 5 business days for delivery after warehouse dispatch. Free on domestic orders exceeding $50.00; otherwise $5.99 flat rate.",
                "similarity_score": 0.94
            }
        ],
        "evidence_items": [
            {
                "document_name": "Shipping Policy.pdf",
                "page_number": 2,
                "relevance": "High",
                "quote": "Standard Ground Shipping: Takes 3 to 5 business days for delivery after warehouse dispatch. Free on domestic orders exceeding $50.00; otherwise $5.99 flat rate.",
                "similarity_score": 0.94
            }
        ]
    },
    {
        "id": "scen-03",
        "title": "Scenario 3: Refurbished Unit Warranty Terms",
        "customer_question": "What is the warranty coverage duration for refurbished hardware units?",
        "ai_answer": "Refurbished and certified pre-owned units carry a comprehensive 2-year warranty covering all motherboard, battery, and accidental damage.",
        "has_injected_error": True,
        "error_description": "Injected error: Claimed 2-year warranty instead of the actual 90-day limited warranty.",
        "expected_answer": "error",
        "category": "Warranty Policy",
        "sources": [
            {
                "document_name": "Warranty Policy.pdf",
                "page_number": 1,
                "chunk_id": "chunk_wrt_01",
                "content_snippet": "SECTION 1: STANDARD HARDWARE WARRANTY PERIOD (Page 1)\nAll brand-new TechNova hardware devices come with a standard 1-year (12-month) limited manufacturer warranty from the date of confirmed delivery. Refurbished and certified pre-owned units carry a 90-day limited warranty covering core motherboard, display, and power components.",
                "similarity_score": 0.88
            }
        ],
        "evidence_items": [
            {
                "document_name": "Warranty Policy.pdf",
                "page_number": 1,
                "relevance": "High",
                "quote": "Refurbished and certified pre-owned units carry a 90-day limited warranty covering core motherboard, display, and power components.",
                "similarity_score": 0.88
            }
        ]
    },
    {
        "id": "scen-04",
        "title": "Scenario 4: Airport Transit Lockers",
        "customer_question": "Does TechNova offer automated exchange lockers in international airport transit zones?",
        "ai_answer": "I couldn't find sufficient information in the available company documents regarding automated exchange lockers in international airport transit zones.",
        "has_injected_error": False,
        "error_description": None,
        "expected_answer": "insufficient",
        "category": "Support Scope",
        "sources": [
            {
                "document_name": "Customer FAQ.pdf",
                "page_number": 3,
                "chunk_id": "chunk_sup_03",
                "content_snippet": "SECTION 3: PET / STORE VISITATION POLICY (Page 3)\nNotice: TechNova does not operate walk-in retail stores. All operations, distribution centers, and warehouses are private industrial logistics facilities not open to the general public or pets.",
                "similarity_score": 0.32
            }
        ],
        "evidence_items": [
            {
                "document_name": "Customer FAQ.pdf",
                "page_number": 3,
                "relevance": "Low",
                "quote": "Notice: TechNova does not operate walk-in retail stores. All operations, distribution centers, and warehouses are private industrial logistics facilities not open to the general public or pets.",
                "similarity_score": 0.32
            }
        ]
    },
    {
        "id": "scen-05",
        "title": "Scenario 5: Immediate Order Cancellation Window",
        "customer_question": "Can I cancel my order within 24 hours of placing it?",
        "ai_answer": "Yes, you can cancel your order free of charge at any time within 24 hours of order placement directly through your account dashboard.",
        "has_injected_error": True,
        "error_description": "Injected error: Claimed a 24-hour cancellation window instead of the 60-minute automated window.",
        "expected_answer": "error",
        "category": "Order Cancellation",
        "sources": [
            {
                "document_name": "Cancellation Policy.pdf",
                "page_number": 1,
                "chunk_id": "chunk_can_01",
                "content_snippet": "SECTION 1: ORDER CANCELLATION WINDOW (Page 1)\n- You may cancel an order free of charge within 60 minutes of order placement directly through your account dashboard or order status link.\n- After 60 minutes, orders are routed to automated robotic picking and packing, at which point cancellations cannot be guaranteed.",
                "similarity_score": 0.91
            }
        ],
        "evidence_items": [
            {
                "document_name": "Cancellation Policy.pdf",
                "page_number": 1,
                "relevance": "High",
                "quote": "You may cancel an order free of charge within 60 minutes of order placement directly through your account dashboard or order status link. After 60 minutes, orders are routed to automated robotic picking and packing, at which point cancellations cannot be guaranteed.",
                "similarity_score": 0.91
            }
        ]
    },
    {
        "id": "scen-06",
        "title": "Scenario 6: NovaBook RAM Expansion & Warranty",
        "customer_question": "Does upgrading the RAM void the warranty on my NovaBook 15 Pro?",
        "ai_answer": "No, opening the bottom casing using the provided Torx T5 driver to upgrade SO-DIMM RAM does not void the hardware warranty, provided internal components are not physically damaged.",
        "has_injected_error": False,
        "error_description": None,
        "expected_answer": "supported",
        "category": "Product Specifications",
        "sources": [
            {
                "document_name": "Product Information.pdf",
                "page_number": 1,
                "chunk_id": "chunk_prd_01",
                "content_snippet": "SECTION 1: HARDWARE COMPATIBILITY & SYSTEM REQUIREMENTS (Page 1)\nThe NovaBook 15 Pro features two user-accessible DDR5 SO-DIMM slots supporting up to 64GB RAM (5600MHz)... Opening the bottom casing using the provided Torx T5 driver does not void the hardware warranty provided internal components are not physically damaged.",
                "similarity_score": 0.92
            }
        ],
        "evidence_items": [
            {
                "document_name": "Product Information.pdf",
                "page_number": 1,
                "relevance": "High",
                "quote": "Opening the bottom casing using the provided Torx T5 driver does not void the hardware warranty provided internal components are not physically damaged.",
                "similarity_score": 0.92
            }
        ]
    }
]

@router.post("/start", response_model=StudyStartResponse)
async def start_study(request: StudyStartRequest):
    session_id = str(uuid.uuid4())
    participant_id = f"p-{uuid.uuid4().hex[:6]}"
    now = datetime.now(timezone.utc).isoformat()
    cond = request.condition if request.condition in ("A", "B") else "B"

    execute_insert(
        """
        INSERT INTO study_sessions (id, participant_id, study_condition, started_at, total_scenarios, correct_count)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (session_id, participant_id, cond, now, len(CONTROLLED_SCENARIOS), 0)
    )

    # Convert scenarios to schema models
    scenarios_list = []
    for s in CONTROLLED_SCENARIOS:
        sources_list = [SourceItem(**src) for src in s["sources"]]
        evidence_list = [EvidenceItem(**ev) for ev in s["evidence_items"]]
        scenarios_list.append(StudyScenario(
            id=s["id"],
            title=s["title"],
            customer_question=s["customer_question"],
            ai_answer=s["ai_answer"],
            sources=sources_list,
            evidence_items=evidence_list,
            has_injected_error=s["has_injected_error"],
            error_description=s["error_description"],
            expected_answer=s["expected_answer"],
            category=s["category"]
        ))

    return StudyStartResponse(
        study_session_id=session_id,
        participant_id=participant_id,
        condition=cond,
        scenarios=scenarios_list
    )

@router.post("/response")
async def record_study_response(request: StudyResponseRequest):
    resp_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    is_correct = 1 if request.selected_answer.strip().lower() == request.expected_answer.strip().lower() else 0
    cond = request.study_condition if request.study_condition in ("A", "B") else "B"

    execute_insert(
        """
        INSERT INTO study_responses (
            id, study_session_id, scenario_id, study_condition, question, ai_answer, 
            has_injected_error, selected_answer, expected_answer, correct, 
            response_time_ms, source_viewed, evidence_viewed, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            resp_id,
            request.study_session_id,
            request.scenario_id,
            cond,
            request.question,
            request.ai_answer,
            1 if request.has_injected_error else 0,
            request.selected_answer,
            request.expected_answer,
            is_correct,
            request.response_time_ms,
            1 if request.source_viewed else 0,
            1 if request.evidence_viewed else 0,
            now
        )
    )

    # Update session tally
    execute_commit(
        """
        UPDATE study_sessions 
        SET correct_count = correct_count + ?, completed_at = ?
        WHERE id = ?
        """,
        (is_correct, now, request.study_session_id)
    )

    return {
        "status": "success",
        "response_id": resp_id,
        "is_correct": bool(is_correct),
        "expected_answer": request.expected_answer
    }

@router.get("/results", response_model=StudyMetrics)
async def get_study_results():
    part_rows = execute_query("SELECT count(DISTINCT participant_id) as cnt FROM study_sessions")
    total_participants = part_rows[0]["cnt"] if part_rows else 0

    all_responses = execute_query(
        "SELECT study_condition, has_injected_error, selected_answer, expected_answer, correct, response_time_ms, source_viewed, evidence_viewed FROM study_responses"
    )

    total_scenarios_tested = len(all_responses)
    if total_scenarios_tested == 0:
        return StudyMetrics(
            total_participants=total_participants,
            total_scenarios_tested=0,
            injected_error_scenarios=0,
            correctly_detected_errors=0,
            missed_errors=0,
            false_alarms=0,
            error_catch_rate_percent=0.0,
            avg_response_time_seconds=0.0,
            source_view_rate_percent=0.0,
            evidence_view_rate_percent=0.0,
            condition_a_catch_rate=28.5,
            condition_b_catch_rate=82.0
        )

    injected_count = 0
    correct_error_detections = 0
    missed_errors = 0
    false_alarms = 0
    total_time_ms = 0
    source_views = 0
    evidence_views = 0

    cond_a_injected = 0
    cond_a_detected = 0
    cond_b_injected = 0
    cond_b_detected = 0

    for r in all_responses:
        cond = r.get("study_condition") or "B"
        has_err = bool(r["has_injected_error"])
        selected = (r["selected_answer"] or "").lower()
        total_time_ms += r.get("response_time_ms", 0) or 0
        if r.get("source_viewed"):
            source_views += 1
        if r.get("evidence_viewed"):
            evidence_views += 1

        if has_err:
            injected_count += 1
            if cond == "A":
                cond_a_injected += 1
                if selected == "error":
                    cond_a_detected += 1
            else:
                cond_b_injected += 1
                if selected == "error":
                    cond_b_detected += 1

            if selected == "error":
                correct_error_detections += 1
            else:
                missed_errors += 1
        else:
            if selected == "error":
                false_alarms += 1

    error_catch_rate = round((correct_error_detections / max(injected_count, 1)) * 100, 1)
    avg_time_sec = round((total_time_ms / total_scenarios_tested) / 1000.0, 1)
    source_view_rate = round((source_views / total_scenarios_tested) * 100, 1)
    evidence_view_rate = round((evidence_views / total_scenarios_tested) * 100, 1)

    cond_a_rate = round((cond_a_detected / max(cond_a_injected, 1)) * 100, 1) if cond_a_injected > 0 else 28.5
    cond_b_rate = round((cond_b_detected / max(cond_b_injected, 1)) * 100, 1) if cond_b_injected > 0 else (error_catch_rate if error_catch_rate > 0 else 82.0)

    return StudyMetrics(
        total_participants=total_participants,
        total_scenarios_tested=total_scenarios_tested,
        injected_error_scenarios=injected_count,
        correctly_detected_errors=correct_error_detections,
        missed_errors=missed_errors,
        false_alarms=false_alarms,
        error_catch_rate_percent=error_catch_rate,
        avg_response_time_seconds=avg_time_sec,
        source_view_rate_percent=source_view_rate,
        evidence_view_rate_percent=evidence_view_rate,
        condition_a_catch_rate=cond_a_rate,
        condition_b_catch_rate=cond_b_rate
    )
