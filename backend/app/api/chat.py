import uuid
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.models.schemas import (
    ChatRequest, 
    ChatMessage, 
    ChatSessionInfo, 
    SourceItem, 
    EvidenceItem,
    BulkDeleteSessionsRequest,
    RenameSessionRequest
)
from backend.app.database.db import execute_query, execute_insert, execute_commit
from backend.app.guardrails.pipeline import guardrails_pipeline

router = APIRouter(prefix="/chat", tags=["chat"])

class RegenerateRequest(BaseModel):
    session_id: str
    language: Optional[str] = "en"

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

    # 3. Execute Guardrails Pipeline (Input Guard -> Prompt Guard -> RAG -> Output Guard -> Audit Logger)
    res = await guardrails_pipeline.process_chat(
        query=user_query,
        session_id=session_id,
        user_id=request.user_id,
        language=lang
    )
    
    # 4. Map structured sources to SourceItem & EvidenceItem
    sources_list = []
    evidence_list = []
    if res.get("sources"):
        for s in res["sources"]:
            sources_list.append(SourceItem(
                document_name=s.document_name,
                page_number=s.page_number,
                chunk_id=s.source_id,
                content_snippet=s.snippet,
                similarity_score=s.similarity_score
            ))
            relevance = "High" if s.similarity_score >= 0.55 else ("Medium" if s.similarity_score >= 0.35 else "Low")
            evidence_list.append(EvidenceItem(
                document_name=s.document_name,
                page_number=s.page_number,
                relevance=relevance,
                quote=s.snippet[:200],
                similarity_score=s.similarity_score
            ))

    # 5. Save AI Message
    ai_msg_id = str(uuid.uuid4())
    sources_json = json.dumps([s.model_dump() for s in sources_list])
    evidence_json = json.dumps([e.model_dump() for e in evidence_list])
    conf_str = res["confidence"].value if hasattr(res["confidence"], "value") else str(res["confidence"])
    status_str = res["status"].value if hasattr(res["status"], "value") else str(res["status"])
    guardrail_flags_json = json.dumps(res.get("guardrail_flags", []))
    action_conf_json = json.dumps(res.get("action_confirmation")) if res.get("action_confirmation") else None
    suggestions_json = json.dumps(res.get("suggestions", []))

    execute_insert(
        """
        INSERT INTO messages (
            id, session_id, role, content, confidence, status, guardrail_flags,
            action_confirmation, pii_warning, intent, suggestions, rewritten_query,
            sources, evidence_items, verification_notice, retrieval_score, language, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ai_msg_id,
            session_id,
            "assistant",
            res["answer"],
            conf_str,
            status_str,
            guardrail_flags_json,
            action_conf_json,
            res.get("pii_warning"),
            res.get("intent"),
            suggestions_json,
            res.get("rewritten_query"),
            sources_json,
            evidence_json,
            res.get("verification_notice"),
            res.get("retrieval_score", 0.0),
            lang,
            now
        )
    )

    return ChatMessage(
        id=ai_msg_id,
        session_id=session_id,
        role="assistant",
        content=res["answer"],
        confidence=conf_str,
        status=status_str,
        evidence_status=res.get("evidence_status", "SUPPORTED"),
        requires_human=res.get("requires_human", False),
        verification_required=res.get("verification_required", True),
        pii_warning=res.get("pii_warning"),
        action_confirmation=res.get("action_confirmation"),
        guardrail_flags=res.get("guardrail_flags", []),
        sources=sources_list,
        evidence_items=evidence_list,
        verification_notice=res.get("verification_notice"),
        retrieval_score=res.get("retrieval_score", 0.0),
        language=lang,
        intent=res.get("intent"),
        suggestions=res.get("suggestions", []),
        rewritten_query=res.get("rewritten_query"),
        created_at=now
    )

@router.post("/regenerate", response_model=ChatMessage)
async def regenerate_last_response(req: RegenerateRequest):
    """
    SECTION 42 — Regnerates AI answer for the last user message, re-evaluating all safety guardrails.
    """
    user_msgs = execute_query(
        "SELECT content FROM messages WHERE session_id = ? AND role = 'user' ORDER BY created_at DESC LIMIT 1",
        (req.session_id,)
    )
    if not user_msgs:
        raise HTTPException(status_code=400, detail="No prior user inquiry found to regenerate.")

    last_query = user_msgs[0]["content"]
    return await send_chat_message(ChatRequest(
        message=last_query,
        session_id=req.session_id,
        language=req.language or "en"
    ))

@router.get("/sessions", response_model=List[ChatSessionInfo])
async def list_chat_sessions(user_id: Optional[str] = "demo-user"):
    rows = execute_query(
        "SELECT id, user_id, title, summary, created_at, updated_at FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,)
    )
    return [ChatSessionInfo(**r) for r in rows]

@router.get("/history", response_model=List[ChatSessionInfo])
async def get_chat_history(user_id: Optional[str] = "demo-user"):
    return await list_chat_sessions(user_id)

@router.put("/sessions/{session_id}/rename", response_model=ChatSessionInfo)
async def rename_chat_session(session_id: str, req: RenameSessionRequest):
    """
    SECTION 44 — Renames a chat conversation.
    """
    sess_rows = execute_query("SELECT id FROM chat_sessions WHERE id = ?", (session_id,))
    if not sess_rows:
        raise HTTPException(status_code=404, detail="Session not found.")

    now = datetime.now(timezone.utc).isoformat()
    new_title = req.title.strip()
    execute_commit("UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?", (new_title, now, session_id))
    return await get_chat_session(session_id)

@router.get("/sessions/{session_id}", response_model=ChatSessionInfo)
async def get_chat_session(session_id: str):
    sess_rows = execute_query("SELECT id, user_id, title, summary, created_at, updated_at FROM chat_sessions WHERE id = ?", (session_id,))
    if not sess_rows:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    sess = sess_rows[0]
    msg_rows = execute_query(
        """
        SELECT id, session_id, role, content, confidence, status, guardrail_flags,
               action_confirmation, pii_warning, intent, suggestions, rewritten_query,
               sources, evidence_items, verification_notice, retrieval_score, language, created_at
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
        
        action_conf = None
        if m.get("action_confirmation"):
            try:
                action_conf = json.loads(m["action_confirmation"])
            except Exception:
                pass

        flags = []
        if m.get("guardrail_flags"):
            try:
                flags = json.loads(m["guardrail_flags"])
            except Exception:
                pass

        suggestions = []
        if m.get("suggestions"):
            try:
                suggestions = json.loads(m["suggestions"])
            except Exception:
                pass

        messages.append(ChatMessage(
            id=m["id"],
            session_id=m["session_id"],
            role=m["role"],
            content=m["content"],
            confidence=m["confidence"],
            status=m.get("status") or "SUPPORTED",
            evidence_status=m.get("status") or "SUPPORTED",
            requires_human=m.get("status") in ["ABSTAINED", "ESCALATED", "UNSUPPORTED"],
            verification_required=True,
            pii_warning=m.get("pii_warning"),
            action_confirmation=action_conf,
            guardrail_flags=flags,
            intent=m.get("intent"),
            suggestions=suggestions,
            rewritten_query=m.get("rewritten_query"),
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
        summary=sess["summary"],
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
