# guardrail/escalation/circuit_breaker.py
# Silences LLMs, handles agent queue checking, and logs escalations

from guardrail.session.schema import SessionState
from guardrail.session.state import save_session, push_to_agent_queue, get_agent_queue_depth
from guardrail.storage.store import log_escalation_event
from guardrail.config import AGENT_QUEUE_MAX_DEPTH


def execute_circuit_breaker(
    session: SessionState,
    primary_signal: str,
    history_transcript: list,
) -> dict:
    """Execute the escalation circuit breaker sequence for a breached session."""
    # 1. AI Silencing: Mark session as escalated in memory
    session.escalated = True
    session.escalation_reason = primary_signal
    
    # 2. Queue Depth check before pushing
    current_depth = get_agent_queue_depth()
    if current_depth >= AGENT_QUEUE_MAX_DEPTH:
        save_session(session.session_id, session)
        return {
            "status": "queue_capacity_breached",
            "message": "Human agent queue is currently at capacity. Please hold.",
            "coupon_issued": False,
        }
        
    # 3. Assemble handover payload
    payload = {
        "session_id": session.session_id,
        "customer_id": session.customer_id,
        "irritation_score": session.current_score,
        "reason": primary_signal,
        "history": history_transcript,
        "customer_ltv": session.customer_ltv,
    }
    
    # 4. Push to WebSocket Queue via Redis and save session
    push_to_agent_queue(session.session_id, payload)
    save_session(session.session_id, session)
    
    # 5. Log escalation incident permanently to DB
    log_escalation_event(
        session_id=session.session_id,
        score=session.current_score,
        threshold=session.current_score,  # Trigger score is active threshold
        signal=primary_signal,
    )
    
    return {
        "status": "escalated_to_agent",
        "message": "Chat has been transferred to a human agent.",
        "coupon_issued": False,  # Managed by retention module subsequently
    }
