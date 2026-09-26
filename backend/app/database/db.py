import sqlite3
import os
import json
from datetime import datetime
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
        verification_notice TEXT,
        retrieval_score REAL,
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

    # 5. feedback
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

    # 6. study_sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS study_sessions (
        id TEXT PRIMARY KEY,
        participant_id TEXT,
        started_at TEXT,
        completed_at TEXT,
        total_scenarios INTEGER DEFAULT 0,
        correct_count INTEGER DEFAULT 0
    );
    """)

    # 7. study_responses
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS study_responses (
        id TEXT PRIMARY KEY,
        study_session_id TEXT,
        scenario_id TEXT,
        question TEXT,
        ai_answer TEXT,
        has_injected_error INTEGER,
        selected_answer TEXT,
        expected_answer TEXT,
        correct INTEGER,
        response_time_ms INTEGER,
        source_viewed INTEGER,
        created_at TEXT,
        FOREIGN KEY (study_session_id) REFERENCES study_sessions(id) ON DELETE CASCADE
    );
    """)

    # Create default demo user if not exists
    cursor.execute("SELECT id FROM users WHERE id = 'demo-user'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (id, name, email, role, created_at) VALUES (?, ?, ?, ?, ?)",
            ("demo-user", "Demo Customer", "customer@example.com", "customer", datetime.utcnow().isoformat())
        )

    conn.commit()
    conn.close()

# Database Helper Functions
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
