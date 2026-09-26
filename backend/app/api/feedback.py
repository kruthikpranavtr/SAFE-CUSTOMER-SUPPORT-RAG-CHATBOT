import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import FeedbackRequest, FeedbackInfo
from backend.app.database.db import execute_query, execute_insert

router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.post("", response_model=FeedbackInfo)
async def submit_feedback(request: FeedbackRequest):
    if request.feedback_type not in ["helpful", "unhelpful"]:
        raise HTTPException(status_code=400, detail="feedback_type must be 'helpful' or 'unhelpful'")

    feedback_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    execute_insert(
        """
        INSERT INTO feedback (id, session_id, message_id, feedback_type, reason, comment, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            feedback_id,
            request.session_id,
            request.message_id,
            request.feedback_type,
            request.reason,
            request.comment or "",
            now
        )
    )

    return FeedbackInfo(
        id=feedback_id,
        session_id=request.session_id,
        message_id=request.message_id,
        feedback_type=request.feedback_type,
        reason=request.reason,
        comment=request.comment,
        created_at=now
    )

@router.get("", response_model=List[FeedbackInfo])
async def list_feedback():
    rows = execute_query("SELECT id, session_id, message_id, feedback_type, reason, comment, created_at FROM feedback ORDER BY created_at DESC")
    return [FeedbackInfo(**r) for r in rows]
