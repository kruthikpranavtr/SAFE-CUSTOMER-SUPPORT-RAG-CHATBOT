import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import EscalationRequest, EscalationInfo
from backend.app.database.db import execute_query, execute_insert
from backend.app.rag.llm import llm_service

router = APIRouter(prefix="/escalations", tags=["escalations"])

@router.post("", response_model=EscalationInfo)
async def create_escalation(request: EscalationRequest):
    escalation_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    summary = request.conversation_summary
    if not summary:
        summary = llm_service.generate_conversation_summary(
            user_question=request.question,
            ai_answer="Automated AI answer provided.",
            confidence="Moderate"
        )

    execute_insert(
        """
        INSERT INTO escalations (id, session_id, customer_name, email, question, conversation_summary, reason, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            escalation_id,
            request.session_id,
            request.customer_name,
            request.email,
            request.question,
            summary,
            request.reason,
            "Pending",
            now
        )
    )

    return EscalationInfo(
        id=escalation_id,
        session_id=request.session_id,
        customer_name=request.customer_name,
        email=request.email,
        question=request.question,
        conversation_summary=summary,
        reason=request.reason,
        status="Pending",
        created_at=now
    )

@router.get("", response_model=List[EscalationInfo])
async def list_escalations():
    rows = execute_query(
        "SELECT id, session_id, customer_name, email, question, conversation_summary, reason, status, created_at FROM escalations ORDER BY created_at DESC"
    )
    return [EscalationInfo(**r) for r in rows]
