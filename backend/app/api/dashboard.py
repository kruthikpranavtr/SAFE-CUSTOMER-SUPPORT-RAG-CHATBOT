from fastapi import APIRouter
from backend.app.models.schemas import DashboardStats
from backend.app.database.db import execute_query

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("", response_model=DashboardStats)
async def get_dashboard_metrics():
    # 1. Conversations
    c_res = execute_query("SELECT count(*) as cnt FROM chat_sessions")
    total_conversations = c_res[0]["cnt"] if c_res else 0

    # 2. Questions (user messages)
    q_res = execute_query("SELECT count(*) as cnt FROM messages WHERE role = 'user'")
    total_questions = q_res[0]["cnt"] if q_res else 0

    # 3. Documents
    d_res = execute_query("SELECT count(*) as cnt FROM documents")
    total_documents = d_res[0]["cnt"] if d_res else 0

    # 4. Feedback metrics
    fb_all = execute_query("SELECT feedback_type, reason FROM feedback")
    total_feedback = len(fb_all)
    helpful_count = sum(1 for f in fb_all if f["feedback_type"] == "helpful")
    incorrect_count = sum(1 for f in fb_all if f.get("reason") == "incorrect_info")

    fb_dist = {
        "Helpful": helpful_count,
        "Incorrect Info": incorrect_count,
        "Unsupported Source": sum(1 for f in fb_all if f.get("reason") == "unsupported_source"),
        "Unclear": sum(1 for f in fb_all if f.get("reason") == "unclear"),
        "Missing Info": sum(1 for f in fb_all if f.get("reason") == "missing_info"),
        "Other": sum(1 for f in fb_all if f["feedback_type"] == "unhelpful" and f.get("reason") == "other")
    }

    # 5. Confidence Distribution from AI messages
    ai_msgs = execute_query("SELECT confidence FROM messages WHERE role = 'assistant'")
    conf_dist = {
        "High": 0,
        "Moderate": 0,
        "Low": 0,
        "Unable to determine": 0
    }
    for m in ai_msgs:
        conf = m.get("confidence") or "Moderate"
        if conf in conf_dist:
            conf_dist[conf] += 1
        else:
            conf_dist["Moderate"] += 1

    # 6. Study Metrics
    part_res = execute_query("SELECT count(DISTINCT participant_id) as cnt FROM study_sessions")
    user_study_participants = part_res[0]["cnt"] if part_res else 0

    study_res = execute_query("SELECT has_injected_error, selected_answer, source_viewed FROM study_responses")
    total_study_scenarios = len(study_res)
    
    injected_count = 0
    detected_errors = 0
    missed_errors = 0
    false_alarms = 0
    sources_viewed = 0

    for s in study_res:
        has_err = bool(s["has_injected_error"])
        ans = (s.get("selected_answer") or "").lower()
        if s.get("source_viewed"):
            sources_viewed += 1

        if has_err:
            injected_count += 1
            if ans == "error":
                detected_errors += 1
            else:
                missed_errors += 1
        else:
            if ans == "error":
                false_alarms += 1

    error_catch_rate = round((detected_errors / max(injected_count, 1)) * 100, 1)
    source_view_rate = round((sources_viewed / max(total_study_scenarios, 1)) * 100, 1)

    error_detection_breakdown = {
        "Detected Injected Errors": detected_errors,
        "Missed Injected Errors": missed_errors,
        "False Alarms": false_alarms,
        "Correctly Verified Supported": total_study_scenarios - (injected_count + false_alarms)
    }

    return DashboardStats(
        total_conversations=total_conversations,
        total_questions=total_questions,
        total_documents=total_documents,
        total_feedback=total_feedback,
        helpful_responses=helpful_count,
        reported_incorrect_responses=incorrect_count,
        user_study_participants=user_study_participants,
        error_catch_rate=error_catch_rate,
        source_view_rate=source_view_rate,
        feedback_distribution=fb_dist,
        confidence_distribution=conf_dist,
        error_detection_breakdown=error_detection_breakdown
    )
