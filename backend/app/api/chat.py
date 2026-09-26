import uuid
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from backend.app.models.schemas import ChatRequest, ChatMessage, ChatSessionInfo, SourceItem
from backend.app.database.db import execute_query, execute_insert, execute_commit
from backend.app.rag.rag_pipeline import rag_pipeline

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatMessage)
async def send_chat_message(request: ChatRequest):
    user_query = request.message.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    now = datetime.now(timezone.utc).isoformat()
    session_id = request.session_id

    # 1. Manage session
    if not session_id:
        session_id = str(uuid.uuid4())
        session_title = user_query[:40] + ("..." if len(user_query) > 40 else "")
        execute_insert(
            "INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, request.user_id or "demo-user", session_title, now, now)
        )
    else:
        existing = execute_query("SELECT id FROM chat_sessions WHERE id = ?", (session_id,))
        if not existing:
            session_title = user_query[:40] + ("..." if len(user_query) > 40 else "")
            execute_insert(
                "INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, request.user_id or "demo-user", session_title, now, now)
            )
        else:
            execute_commit("UPDATE chat_sessions SET updated_at = ? WHERE id = ?", (now, session_id))

    # 2. Save User Message
    user_msg_id = str(uuid.uuid4())
    execute_insert(
        """
        INSERT INTO messages (id, session_id, role, content, confidence, sources, verification_notice, retrieval_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_msg_id, session_id, "user", user_query, None, json.dumps([]), None, 0.0, now)
    )

    # 3. Execute RAG Pipeline
    rag_result = await rag_pipeline.execute_rag(user_query)
    
    # 4. Save AI Message
    ai_msg_id = str(uuid.uuid4())
    sources_json = json.dumps([s.model_dump() for s in rag_result["sources"]])
    execute_insert(
        """
        INSERT INTO messages (id, session_id, role, content, confidence, sources, verification_notice, retrieval_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ai_msg_id,
            session_id,
            "assistant",
            rag_result["answer"],
            rag_result["confidence"],
            sources_json,
            rag_result["verification_notice"],
            rag_result["retrieval_score"],
            now
        )
    )

    return ChatMessage(
        id=ai_msg_id,
        session_id=session_id,
        role="assistant",
        content=rag_result["answer"],
        confidence=rag_result["confidence"],
        sources=rag_result["sources"],
        verification_notice=rag_result["verification_notice"],
        retrieval_score=rag_result["retrieval_score"],
        created_at=now
    )

@router.get("/sessions", response_model=List[ChatSessionInfo])
async def list_chat_sessions(user_id: Optional[str] = "demo-user"):
    rows = execute_query(
        "SELECT id, user_id, title, created_at, updated_at FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,)
    )
    return [ChatSessionInfo(**r) for r in rows]

@router.get("/sessions/{session_id}", response_model=ChatSessionInfo)
async def get_chat_session(session_id: str):
    sess_rows = execute_query("SELECT id, user_id, title, created_at, updated_at FROM chat_sessions WHERE id = ?", (session_id,))
    if not sess_rows:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    sess = sess_rows[0]
    msg_rows = execute_query(
        """
        SELECT id, session_id, role, content, confidence, sources, verification_notice, retrieval_score, created_at
        FROM messages WHERE session_id = ? ORDER BY created_at ASC
        """,
        (session_id,)
    )
    
    messages = []
    for m in msg_rows:
        sources_list = []
        if m["sources"]:
            try:
                raw_sources = json.loads(m["sources"])
                sources_list = [SourceItem(**s) for s in raw_sources]
            except Exception:
                sources_list = []
        
        messages.append(ChatMessage(
            id=m["id"],
            session_id=m["session_id"],
            role=m["role"],
            content=m["content"],
            confidence=m["confidence"],
            sources=sources_list,
            verification_notice=m["verification_notice"],
            retrieval_score=m["retrieval_score"],
            created_at=m["created_at"]
        ))

    return ChatSessionInfo(
        id=sess["id"],
        user_id=sess["user_id"],
        title=sess["title"],
        created_at=sess["created_at"],
        updated_at=sess["updated_at"],
        messages=messages
    )

@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    execute_commit("DELETE FROM messages WHERE session_id = ?", (session_id,))
    execute_commit("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    return {"status": "success", "message": f"Session {session_id} deleted"}
