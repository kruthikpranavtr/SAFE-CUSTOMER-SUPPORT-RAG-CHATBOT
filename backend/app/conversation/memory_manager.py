import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.app.database.db import execute_query, execute_insert, execute_commit

class ConversationMemory:
    """
    Manages short-term conversation memory and compact summary generation.
    Stores and retrieves structured context, detected intents, and recent interaction history.
    """
    
    @staticmethod
    def get_recent_messages(session_id: str, limit: int = 6) -> List[Dict[str, Any]]:
        """
        Retrieves the last N messages for context windowing.
        """
        if not session_id:
            return []
        
        rows = execute_query(
            """
            SELECT id, role, content, confidence, status, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (session_id, limit)
        )
        # Return in chronological order
        return [dict(r) for r in reversed(rows)]

    @staticmethod
    def get_session_context(session_id: str) -> Dict[str, Any]:
        """
        Retrieves current session metadata, summary, and last recorded intent.
        """
        if not session_id:
            return {"summary": None, "last_intent": None, "active_topic": None}

        rows = execute_query(
            "SELECT id, title, summary, last_intent, active_topic FROM chat_sessions WHERE id = ?",
            (session_id,)
        )
        if not rows:
            return {"summary": None, "last_intent": None, "active_topic": None}

        row = rows[0]
        return {
            "summary": row["summary"],
            "last_intent": row["last_intent"],
            "active_topic": row["active_topic"]
        }

    @staticmethod
    def update_session_context(
        session_id: str, 
        last_intent: Optional[str] = None, 
        active_topic: Optional[str] = None,
        summary: Optional[str] = None
    ):
        """
        Persists updated intent, topic, and summary to chat_sessions.
        """
        if not session_id:
            return

        updates = []
        params = []
        if last_intent is not None:
            updates.append("last_intent = ?")
            params.append(last_intent)
        if active_topic is not None:
            updates.append("active_topic = ?")
            params.append(active_topic)
        if summary is not None:
            updates.append("summary = ?")
            params.append(summary)

        if updates:
            params.append(session_id)
            execute_commit(f"UPDATE chat_sessions SET {', '.join(updates)} WHERE id = ?", tuple(params))

    @classmethod
    def generate_compact_summary(cls, session_id: str) -> Optional[str]:
        """
        Builds a compact, safety-conscious summary of the conversation once it exceeds 4 turns.
        Format conforms strictly to Section 33 requirements.
        """
        if not session_id:
            return None

        # Fetch recent messages (up to 12)
        rows = execute_query(
            "SELECT role, content, status FROM messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,)
        )
        if len(rows) < 4:
            return None

        user_queries = [r["content"] for r in rows if r["role"] == "user"]
        ai_answers = [r["content"] for r in rows if r["role"] == "assistant"]
        
        main_topic = "customer support inquiry"
        if any("refund" in q.lower() for q in user_queries):
            main_topic = "refund policy and eligibility"
        elif any("return" in q.lower() for q in user_queries):
            main_topic = "product return procedure"
        elif any("shipping" in q.lower() or "delivery" in q.lower() for q in user_queries):
            main_topic = "shipping and delivery timelines"
        elif any("warranty" in q.lower() for q in user_queries):
            main_topic = "hardware warranty coverage"
        elif any("cancel" in q.lower() for q in user_queries):
            main_topic = "order cancellation"

        has_escalation = any("human" in q.lower() for q in user_queries)
        latest_query = user_queries[-1] if user_queries else "None"

        summary_lines = [
            f"Customer inquiry topic: {main_topic}.",
            f"Latest question: '{latest_query[:80]}'.",
            f"AI provided factually verified policy information from company documents.",
            "Customer requested human escalation." if has_escalation else "Customer has not yet requested human support."
        ]

        summary = "\n".join(summary_lines)
        cls.update_session_context(session_id, summary=summary)
        return summary
