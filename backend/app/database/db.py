import sqlite3
import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.app.utils.config import settings

def get_db_connection():
    os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT,
        email TEXT,
        role TEXT DEFAULT 'customer',
        created_at TEXT
    );
    """)

    # 2. chat_sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        title TEXT,
        created_at TEXT,
        updated_at TEXT
    );
    """)

    # 3. messages
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        session_id TEXT,
        role TEXT,
        content TEXT,
        confidence TEXT,
        sources TEXT,
        evidence_items TEXT,
        verification_notice TEXT,
        retrieval_score REAL,
        language TEXT DEFAULT 'en',
        created_at TEXT,
        FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
    );
    """)

    # 4. documents
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        filename TEXT,
        file_type TEXT,
        file_path TEXT,
        status TEXT,
        chunk_count INTEGER DEFAULT 0,
        file_size INTEGER DEFAULT 0,
        uploaded_at TEXT
    );
    """)

    # 5. document_chunks
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_chunks (
        id TEXT PRIMARY KEY,
        document_id TEXT,
        chunk_id TEXT,
        filename TEXT,
        page_number INTEGER,
        text TEXT,
        created_at TEXT,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    """)

    # 6. feedback
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id TEXT PRIMARY KEY,
        session_id TEXT,
        message_id TEXT,
        feedback_type TEXT,
        reason TEXT,
        comment TEXT,
        created_at TEXT,
        FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
    );
    """)

    # 7. escalations (Human Handoff)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS escalations (
        id TEXT PRIMARY KEY,
        session_id TEXT,
        customer_name TEXT,
        email TEXT,
        question TEXT,
        conversation_summary TEXT,
        reason TEXT,
        status TEXT DEFAULT 'Pending',
        created_at TEXT
    );
    """)

    # 8. study_sessions (A/B Testing Condition A / B)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS study_sessions (
        id TEXT PRIMARY KEY,
        participant_id TEXT,
        study_condition TEXT DEFAULT 'B',
        started_at TEXT,
        completed_at TEXT,
        total_scenarios INTEGER DEFAULT 0,
        correct_count INTEGER DEFAULT 0
    );
    """)

    # 9. study_scenarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS study_scenarios (
        id TEXT PRIMARY KEY,
        title TEXT,
        category TEXT,
        customer_question TEXT,
        ai_answer TEXT,
        expected_answer TEXT,
        has_injected_error INTEGER,
        error_description TEXT,
        sources_json TEXT
    );
    """)

    # 10. study_responses
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS study_responses (
        id TEXT PRIMARY KEY,
        study_session_id TEXT,
        scenario_id TEXT,
        study_condition TEXT,
        question TEXT,
        ai_answer TEXT,
        has_injected_error INTEGER,
        selected_answer TEXT,
        expected_answer TEXT,
        correct INTEGER,
        response_time_ms INTEGER,
        source_viewed INTEGER,
        evidence_viewed INTEGER DEFAULT 0,
        created_at TEXT,
        FOREIGN KEY (study_session_id) REFERENCES study_sessions(id) ON DELETE CASCADE
    );
    """)

    # 11. risk_register
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS risk_register (
        id TEXT PRIMARY KEY,
        risk TEXT,
        category TEXT,
        status TEXT,
        mitigation TEXT,
        test_coverage TEXT
    );
    """)

    # 12. guardrail_events (Safety Audit Logging)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guardrail_events (
        id TEXT PRIMARY KEY,
        request_id TEXT,
        session_id TEXT,
        user_id TEXT,
        guardrail_type TEXT,
        severity TEXT,
        action TEXT,
        reason TEXT,
        details TEXT,
        created_at TEXT
    );
    """)

    # 13. orders (Real Customer Support Orders)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        product_name TEXT,
        status TEXT,
        total_amount REAL,
        can_cancel INTEGER DEFAULT 1,
        created_at TEXT
    );
    """)

    # Schema migration helper for existing databases
    def _add_col_if_missing(table_name: str, col_name: str, col_def: str):
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing = [c[1] for c in cursor.fetchall()]
        if col_name not in existing:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}")

    _add_col_if_missing("chat_sessions", "summary", "TEXT")
    _add_col_if_missing("chat_sessions", "last_intent", "TEXT")
    _add_col_if_missing("chat_sessions", "active_topic", "TEXT")
    _add_col_if_missing("messages", "language", "TEXT DEFAULT 'en'")
    _add_col_if_missing("messages", "evidence_items", "TEXT")
    _add_col_if_missing("messages", "status", "TEXT DEFAULT 'SUPPORTED'")
    _add_col_if_missing("messages", "guardrail_flags", "TEXT")
    _add_col_if_missing("messages", "action_confirmation", "TEXT")
    _add_col_if_missing("messages", "pii_warning", "TEXT")
    _add_col_if_missing("messages", "intent", "TEXT")
    _add_col_if_missing("messages", "suggestions", "TEXT")
    _add_col_if_missing("messages", "rewritten_query", "TEXT")
    _add_col_if_missing("study_sessions", "study_condition", "TEXT DEFAULT 'B'")
    _add_col_if_missing("study_responses", "study_condition", "TEXT DEFAULT 'B'")
    _add_col_if_missing("study_responses", "evidence_viewed", "INTEGER DEFAULT 0")

    now = datetime.now(timezone.utc).isoformat()

    # Seed mock orders
    cursor.execute("SELECT count(*) as cnt FROM orders")
    if cursor.fetchone()["cnt"] == 0:
        orders_seed = [
            ("Nova-9876", "demo-user", "NovaBook Ultra 14 (32GB RAM / 1TB SSD)", "Processing", 1299.99, 1, now),
            ("Nova-1024", "demo-user", "NovaBook GaN 100W Fast Charger", "Shipped", 49.99, 0, now),
            ("Nova-5521", "demo-user", "NovaBook Premium Protective Sleeve", "Delivered", 29.99, 0, now)
        ]
        cursor.executemany(
            "INSERT INTO orders (id, user_id, product_name, status, total_amount, can_cancel, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            orders_seed
        )

    # Default demo user
    cursor.execute("SELECT id FROM users WHERE id = 'demo-user'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (id, name, email, role, created_at) VALUES (?, ?, ?, ?, ?)",
            ("demo-user", "Customer User", "customer@technova-support-demo.com", "customer", now)
        )

    # Seed Risk Register items
    cursor.execute("SELECT count(*) as cnt FROM risk_register")
    if cursor.fetchone()["cnt"] == 0:
        risks = [
            ("risk-1", "Overreliance on AI", "Safety", "Partially Mitigated", 
             "Direct citation of document snippets, required confirmation before critical action, and prominent verification guidance.", 
             "Covered by Safety Lab Scenario Testing and automated test suites."),
            ("risk-2", "Automation Bias", "Safety", "Partially Mitigated", 
             "Dynamic confidence communication (High, Moderate, Low, Unable to determine) and persistent verification notices.", 
             "Evaluated via A/B Safety Lab Error Catch Rate telemetry."),
            ("risk-3", "Anthropomorphization", "Safety", "Mitigated", 
             "Strictly labeled as 'AI Customer Support Assistant'. No human names, avatars, personal emotional statements, or false handling claims.", 
             "System prompt boundary tests and UI persona audits."),
            ("risk-4", "Hallucinated Company Policy", "Reliability", "Partially Mitigated", 
             "Strict evidence-first RAG. Safe refusal ('Insufficient Information') when documents do not corroborate query topic.", 
             "Verified with out-of-domain query tests in test_live_system.py."),
            ("risk-5", "Prompt Injection via User Query or Document", "Security", "Partially Mitigated", 
             "PromptGuard input sanitizer, unprivileged document content wrapping, and system prompt priority enforcement.", 
             "Covered by adversarial prompt injection unit tests.")
        ]
        cursor.executemany(
            "INSERT INTO risk_register (id, risk, category, status, mitigation, test_coverage) VALUES (?, ?, ?, ?, ?, ?)",
            risks
        )

    conn.commit()
    conn.close()

def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def execute_commit(query: str, params: tuple = ()) -> int:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()

def execute_insert(query: str, params: tuple = ()) -> None:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
    finally:
        conn.close()
