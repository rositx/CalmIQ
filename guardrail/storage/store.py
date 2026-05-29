# guardrail/storage/store.py
# Single repository for all PostgreSQL read, write, and log operations

import uuid
from datetime import datetime
from typing import Optional, Dict, List
from guardrail.config import DATABASE_URL

# Local lists and dicts for local process memory fallback
_MEM_SESSIONS = {}
_MEM_TURNS = []
_MEM_ESCALATIONS = []


def log_session_start(session_id: str, customer_id: str) -> None:
    """Log the initialization of a new chat session."""
    record = {
        "id": session_id,
        "customer_id": customer_id,
        "started_at": datetime.utcnow(),
        "ended_at": None,
        "peak_irritation_score": 0.0,
        "escalated": False,
        "escalation_reason": None,
        "resolved": False,
        "resolution_type": None,
        "coupon_issued": False,
        "turn_count": 0,
    }
    _MEM_SESSIONS[session_id] = record
    
    # In a full Postgres setup, this triggers async SQLAlchemy insert
    # e.g., session.add(SessionLog(**record))


def log_session_turn(
    session_id: str,
    turn_index: int,
    role: str,
    message: str,
    sentiment_score: float,
    irritation_score: float,
) -> None:
    """Log a turn (user or AI response) within the session."""
    record = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "turn_index": turn_index,
        "role": role,
        "message": message,
        "sentiment_score": sentiment_score,
        "irritation_score_at_turn": irritation_score,
        "timestamp": datetime.utcnow(),
    }
    _MEM_TURNS.append(record)
    
    if session_id in _MEM_SESSIONS:
        _MEM_SESSIONS[session_id]["turn_count"] = max(
            _MEM_SESSIONS[session_id]["turn_count"], turn_index + 1
        )
        _MEM_SESSIONS[session_id]["peak_irritation_score"] = max(
            _MEM_SESSIONS[session_id]["peak_irritation_score"], irritation_score
        )


def log_escalation_event(
    session_id: str,
    score: float,
    threshold: float,
    signal: str,
) -> None:
    """Log an escalation circuit-breaker trigger event."""
    record = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "triggered_at": datetime.utcnow(),
        "score_at_trigger": score,
        "threshold_at_trigger": threshold,
        "primary_signal": signal,
        "agent_id": None,
        "time_to_agent_seconds": None,
    }
    _MEM_ESCALATIONS.append(record)
    
    if session_id in _MEM_SESSIONS:
        _MEM_SESSIONS[session_id]["escalated"] = True
        _MEM_SESSIONS[session_id]["escalation_reason"] = signal


def update_session_resolution(
    session_id: str,
    resolution_type: str,
    coupon_issued: bool = False,
) -> None:
    """Mark a session as completed or resolved with details."""
    if session_id in _MEM_SESSIONS:
        _MEM_SESSIONS[session_id]["resolved"] = True
        _MEM_SESSIONS[session_id]["ended_at"] = datetime.utcnow()
        _MEM_SESSIONS[session_id]["resolution_type"] = resolution_type
        _MEM_SESSIONS[session_id]["coupon_issued"] = coupon_issued


def get_logged_session_for_testing(session_id: str) -> Optional[dict]:
    """Retrieve logged session details from memory for testing validation."""
    return _MEM_SESSIONS.get(session_id)


def get_logged_turns_for_testing(session_id: str) -> List[dict]:
    """Retrieve logged turn details from memory for testing validation."""
    return [t for t in _MEM_TURNS if t["session_id"] == session_id]


def get_logged_escalations_for_testing(session_id: str) -> List[dict]:
    """Retrieve logged escalation events from memory for testing validation."""
    return [e for e in _MEM_ESCALATIONS if e["session_id"] == session_id]


def clear_all_logs_for_testing() -> None:
    """Flush logs in memory to keep unit tests isolated."""
    _MEM_SESSIONS.clear()
    _MEM_TURNS.clear()
    _MEM_ESCALATIONS.clear()
