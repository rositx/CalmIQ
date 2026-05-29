# guardrail/router.py
# Intercepts user requests, routes to scoring modules, and executes circuit breakers

import time
from datetime import datetime
from typing import Optional, Dict
from guardrail.session.schema import SessionState
from guardrail.session.state import get_session, save_session
from guardrail.utils.embedder import get_embedding
from guardrail.scoring.sentiment import calculate_sentiment_score
from guardrail.scoring.telemetry import calculate_telemetry_score
from guardrail.scoring.context import calculate_context_score
from guardrail.scoring.matrix import calculate_irritation_score
from guardrail.escalation.threshold import evaluate_escalation
from guardrail.escalation.circuit_breaker import execute_circuit_breaker
from guardrail.retention.coupon import issue_retention_coupon
from guardrail.storage.store import log_session_start, log_session_turn, update_session_resolution


def _init_or_load_session(
    session_id: str, customer_id: str, metadata: dict
) -> SessionState:
    """Retrieve session state or construct a new instance if none exists."""
    session = get_session(session_id)
    if not session:
        session = SessionState(
            session_id=session_id,
            customer_id=customer_id,
            customer_ltv=float(metadata.get("customer_ltv", 0.0)),
            total_past_sessions=int(metadata.get("total_past_sessions", 0)),
            recent_complaint_count=int(metadata.get("recent_complaint_count", 0)),
            lifetime_coupons_claimed=int(metadata.get("lifetime_coupons_claimed", 0)),
        )
        log_session_start(session_id, customer_id)
    return session


def _calculate_time_delta(last_updated_str: str) -> float:
    """Calculate the elapsed seconds since the last message update."""
    try:
        prev = datetime.fromisoformat(last_updated_str)
        delta = (datetime.utcnow() - prev).total_seconds()
        return max(1.0, delta)
    except Exception:
        return 5.0


def _update_embeddings(history: list, new_emb: list) -> None:
    """Manage rolling history length for embeddings list up to 3."""
    history.append(new_emb)
    if len(history) > 3:
        history.pop(0)


async def _handle_escalation_flow(session: SessionState, text: str) -> dict:
    """Execute the full agent transfer and coupon issuance escalation sequence."""
    breaker = execute_circuit_breaker(session, "irritation_breach", [text])
    
    # Check if eligibility rules authorize coupon discounts
    coupon_code = await issue_retention_coupon(session)
    if coupon_code:
        breaker["coupon_issued"] = True
        breaker["coupon_code"] = coupon_code
        breaker["message"] += f" Sent coupon: {coupon_code}"
        
    update_session_resolution(
        session.session_id,
        resolution_type="human_resolved",
        coupon_issued=bool(coupon_code),
    )
    return breaker


async def process_user_message(
    session_id: str,
    customer_id: str,
    text: str,
    telemetry_data: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
) -> dict:
    """Intercept chat message, calculate score, evaluate safety, and respond."""
    metadata = metadata or {}
    session = _init_or_load_session(session_id, customer_id, metadata)
    
    # 1. Update user input embeddings
    user_emb = get_embedding(text)
    _update_embeddings(session.user_message_embeddings, user_emb)
    
    # 2. Score individual dimensions
    s_score = calculate_sentiment_score(text, session)
    b_score = calculate_telemetry_score(telemetry_data, session)
    c_score = calculate_context_score(session)
    
    # 3. Calculate aggregate Irritation Score
    score = calculate_irritation_score(s_score, b_score, c_score)
    
    # 4. Mutate session parameters securely
    session.score_history.append(score)
    session.current_score = score
    session.turn_count += 1
    
    # 5. Check escalation threshold with hysteresis
    time_delta = _calculate_time_delta(session.last_updated)
    session.last_updated = datetime.utcnow().isoformat()
    
    is_escalated = evaluate_escalation(session, time_delta)
    log_session_turn(session_id, session.turn_count, "user", text, s_score, score)
    
    if is_escalated:
        return await _handle_escalation_flow(session, text)
        
    # Standard Flow: Return Mock Bot response and append AI embeddings
    mock_response = f"Thank you for your message. I am here to help you: {text}"
    ai_emb = get_embedding(mock_response)
    _update_embeddings(session.ai_response_embeddings, ai_emb)
    
    save_session(session_id, session)
    log_session_turn(session_id, session.turn_count, "ai", mock_response, 0.0, score)
    
    return {
        "status": "normal",
        "response": mock_response,
        "irritation_score": score,
    }
