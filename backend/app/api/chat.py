import uuid
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import (
    ChatRequest, 
    ChatMessage, 
    ChatSessionInfo, 
    SourceItem, 
    EvidenceItem,
    BulkDeleteSessionsRequest
)
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
    lang = request.language or "en"

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
        INSERT INTO messages (id, session_id, role, content, confidence, sources, evidence_items, verification_notice, retrieval_score, language, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_msg_id, session_id, "user", user_query, None, json.dumps([]), json.dumps([]), None, 0.0, lang, now)
    )

    # 3. Execute RAG Pipeline with Language option
    rag_result = await rag_pipeline.execute_rag(user_query, language=lang)
    
    # 4. Save AI Message
    ai_msg_id = str(uuid.uuid4())
    sources_json = json.dumps([s.model_dump() for s in rag_result["sources"]])
    evidence_json = json.dumps([e.model_dump() for e in rag_result["evidence_items"]])
    
    execute_insert(
        """
        INSERT INTO messages (id, session_id, role, content, confidence, sources, evidence_items, verification_notice, retrieval_score, language, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ai_msg_id,
            session_id,
            "assistant",
            rag_result["answer"],
            rag_result["confidence"],
            sources_json,
            evidence_json,
            rag_result["verification_notice"],
            rag_result["retrieval_score"],
            lang,
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
        evidence_items=rag_result["evidence_items"],
        verification_notice=rag_result["verification_notice"],
        retrieval_score=rag_result["retrieval_score"],
        language=lang,
        created_at=now
    )

@router.get("/sessions", response_model=List[ChatSessionInfo])
async def list_chat_sessions(user_id: Optional[str] = "demo-user"):
    rows = execute_query(
        "SELECT id, user_id, title, created_at, updated_at FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,)
    )
    return [ChatSessionInfo(**r) for r in rows]

@router.get("/history", response_model=List[ChatSessionInfo])
async def get_chat_history(user_id: Optional[str] = "demo-user"):
    return await list_chat_sessions(user_id)

@router.get("/sessions/{session_id}", response_model=ChatSessionInfo)
async def get_chat_session(session_id: str):
    sess_rows = execute_query("SELECT id, user_id, title, created_at, updated_at FROM chat_sessions WHERE id = ?", (session_id,))
    if not sess_rows:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    sess = sess_rows[0]
    msg_rows = execute_query(
        """
        SELECT id, session_id, role, content, confidence, sources, evidence_items, verification_notice, retrieval_score, language, created_at
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

        evidence_list = []
        if m.get("evidence_items"):
            try:
                raw_evidence = json.loads(m["evidence_items"])
                evidence_list = [EvidenceItem(**e) for e in raw_evidence]
            except Exception:
                evidence_list = []
        
        messages.append(ChatMessage(
            id=m["id"],
            session_id=m["session_id"],
            role=m["role"],
            content=m["content"],
            confidence=m["confidence"],
            sources=sources_list,
            evidence_items=evidence_list,
            verification_notice=m["verification_notice"],
            retrieval_score=m["retrieval_score"],
            language=m.get("language") or "en",
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

@router.post("/sessions/bulk-delete")
async def bulk_delete_chat_sessions(req: BulkDeleteSessionsRequest):
    if not req.session_ids:
        return {"status": "success", "deleted_count": 0}
    placeholders = ",".join(["?"] * len(req.session_ids))
    execute_commit(f"DELETE FROM messages WHERE session_id IN ({placeholders})", tuple(req.session_ids))
    execute_commit(f"DELETE FROM chat_sessions WHERE id IN ({placeholders})", tuple(req.session_ids))
    return {"status": "success", "deleted_count": len(req.session_ids)}

@router.delete("/sessions/clear-all")
async def clear_all_chat_sessions(user_id: Optional[str] = "demo-user"):
    if user_id:
        sess_rows = execute_query("SELECT id FROM chat_sessions WHERE user_id = ?", (user_id,))
        if sess_rows:
            s_ids = [r["id"] for r in sess_rows]
            placeholders = ",".join(["?"] * len(s_ids))
            execute_commit(f"DELETE FROM messages WHERE session_id IN ({placeholders})", tuple(s_ids))
            execute_commit("DELETE FROM chat_sessions WHERE user_id = ?", (user_id,))
            return {"status": "success", "deleted_count": len(s_ids)}
        return {"status": "success", "deleted_count": 0}
    else:
        execute_commit("DELETE FROM messages")
        execute_commit("DELETE FROM chat_sessions")
        return {"status": "success", "deleted_count": "all"}

@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    execute_commit("DELETE FROM messages WHERE session_id = ?", (session_id,))
    execute_commit("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    return {"status": "success", "message": f"Session {session_id} deleted"}
