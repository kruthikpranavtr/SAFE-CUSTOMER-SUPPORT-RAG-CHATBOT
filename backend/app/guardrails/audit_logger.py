import uuid
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.app.database.db import execute_insert, execute_query
from backend.app.guardrails.base import GuardrailType, GuardrailSeverity, GuardrailAction

class AuditLogger:
    @staticmethod
    def log_event(
        guardrail_type: GuardrailType,
        action: GuardrailAction,
        reason: str,
        severity: GuardrailSeverity = GuardrailSeverity.INFO,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = "demo-user",
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Records a safety audit event to the SQLite database without storing raw sensitive user PII.
        """
        event_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        req_id = request_id or str(uuid.uuid4())
        
        # Ensure details do not store raw credit cards, passwords, or full sensitive payload
        clean_details = {}
        if details:
            for k, v in details.items():
                if "pii" in k.lower() or "secret" in k.lower() or "card" in k.lower():
                    clean_details[k] = "[REDACTED]"
                else:
                    clean_details[k] = v

        try:
            execute_insert(
                """
                INSERT INTO guardrail_events (id, request_id, session_id, user_id, guardrail_type, severity, action, reason, details, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    req_id,
                    session_id,
                    user_id or "anonymous",
                    guardrail_type.value if hasattr(guardrail_type, "value") else str(guardrail_type),
                    severity.value if hasattr(severity, "value") else str(severity),
                    action.value if hasattr(action, "value") else str(action),
                    reason,
                    json.dumps(clean_details),
                    now
                )
            )
        except Exception as e:
            # Fallback print if db schema not yet migrated
            print(f"[AUDIT LOG ERROR] Failed to record event {guardrail_type}: {e}")

        return event_id

    @staticmethod
    def get_events(limit: int = 100, guardrail_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves recent audit log events.
        """
        query = "SELECT id, request_id, session_id, user_id, guardrail_type, severity, action, reason, details, created_at FROM guardrail_events"
        params = []
        if guardrail_type:
            query += " WHERE guardrail_type = ?"
            params.append(guardrail_type)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        try:
            rows = execute_query(query, tuple(params))
            for r in rows:
                if r.get("details"):
                    try:
                        r["details"] = json.loads(r["details"])
                    except Exception:
                        pass
            return rows
        except Exception:
            return []

    @staticmethod
    def get_guardrail_stats() -> Dict[str, Any]:
        """
        Computes real telemetry on guardrail activity for the admin dashboard.
        """
        try:
            total_events = execute_query("SELECT count(*) as cnt FROM guardrail_events")
            cnt = total_events[0]["cnt"] if total_events else 0

            type_counts = execute_query(
                "SELECT guardrail_type, count(*) as cnt FROM guardrail_events GROUP BY guardrail_type"
            )
            by_type = {r["guardrail_type"]: r["cnt"] for r in type_counts}

            severity_counts = execute_query(
                "SELECT severity, count(*) as cnt FROM guardrail_events GROUP BY severity"
            )
            by_severity = {r["severity"]: r["cnt"] for r in severity_counts}

            return {
                "total_events": cnt,
                "by_type": by_type,
                "by_severity": by_severity,
                "prompt_injections_blocked": by_type.get("PROMPT_INJECTION", 0),
                "pii_detected": by_type.get("PII", 0),
                "abstentions": by_type.get("ABSTENTION", 0),
                "evidence_failures": by_type.get("EVIDENCE_ONLY", 0) + by_type.get("EVIDENCE_CONSISTENCY", 0),
                "human_escalations": by_type.get("HUMAN_ESCALATION", 0),
                "domain_violations": by_type.get("DOMAIN_VIOLATION", 0)
            }
        except Exception:
            return {
                "total_events": 0,
                "by_type": {},
                "by_severity": {},
                "prompt_injections_blocked": 0,
                "pii_detected": 0,
                "abstentions": 0,
                "evidence_failures": 0,
                "human_escalations": 0,
                "domain_violations": 0
            }

audit_logger = AuditLogger()
