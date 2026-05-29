# tests/test_storage.py
# Pytest suite for database persistence logging functions (PostgreSQL mocks)

from guardrail.storage.store import (
    log_session_start,
    log_session_turn,
    log_escalation_event,
    update_session_resolution,
    get_logged_session_for_testing,
    get_logged_turns_for_testing,
    get_logged_escalations_for_testing,
    clear_all_logs_for_testing,
)


def test_session_logging_start_resolution():
    """Verify that starting and resolving a session updates logs successfully."""
    clear_all_logs_for_testing()
    
    log_session_start("db_s1", "customer_db")
    record = get_logged_session_for_testing("db_s1")
    assert record is not None
    assert record["customer_id"] == "customer_db"
    assert not record["resolved"]
    
    # Resolve session
    update_session_resolution("db_s1", resolution_type="ai_resolved", coupon_issued=False)
    updated = get_logged_session_for_testing("db_s1")
    assert updated["resolved"]
    assert updated["resolution_type"] == "ai_resolved"
    assert updated["ended_at"] is not None


def test_session_turn_logging():
    """Verify turn logging appends messages and registers peak scores."""
    clear_all_logs_for_testing()
    log_session_start("db_s2", "customer_db")
    
    # Log turn 1
    log_session_turn(
        session_id="db_s2",
        turn_index=0,
        role="user",
        message="Cancel it!",
        sentiment_score=85.0,
        irritation_score=40.0,
    )
    
    # Log turn 2
    log_session_turn(
        session_id="db_s2",
        turn_index=1,
        role="ai",
        message="Okay",
        sentiment_score=0.0,
        irritation_score=50.0,
    )
    
    turns = get_logged_turns_for_testing("db_s2")
    assert len(turns) == 2
    assert turns[0]["role"] == "user"
    assert turns[1]["role"] == "ai"
    
    session = get_logged_session_for_testing("db_s2")
    assert session["turn_count"] == 2
    assert session["peak_irritation_score"] == 50.0


def test_escalation_event_logging():
    """Verify that escalation events are tracked with appropriate triggers."""
    clear_all_logs_for_testing()
    log_session_start("db_s3", "customer_db")
    
    log_escalation_event(
        session_id="db_s3",
        score=82.0,
        threshold=75.0,
        signal="irritation_breach",
    )
    
    events = get_logged_escalations_for_testing("db_s3")
    assert len(events) == 1
    assert events[0]["score_at_trigger"] == 82.0
    assert events[0]["primary_signal"] == "irritation_breach"
    
    session = get_logged_session_for_testing("db_s3")
    assert session["escalated"]
    assert session["escalation_reason"] == "irritation_breach"
