# tests/test_escalation.py
# Pytest suite for adaptive thresholds, hysteresis windows, and circuit-breaker triggers

from guardrail.session.schema import SessionState
from guardrail.escalation.threshold import get_adaptive_threshold, evaluate_escalation
from guardrail.escalation.circuit_breaker import execute_circuit_breaker
from guardrail.session.state import clear_all_sessions_for_testing


def test_adaptive_thresholds():
    """Verify threshold shifts for customer LTV, past visits, and complaints."""
    # Base Case (returning customer): 75
    s1 = SessionState(session_id="s1", customer_id="c1", total_past_sessions=1)
    assert get_adaptive_threshold(s1) == 75
    
    # High Value Client (LTV > 10,000): 75 - 15 = 60
    s2 = SessionState(session_id="s2", customer_id="c2", total_past_sessions=1, customer_ltv=12000.0)
    assert get_adaptive_threshold(s2) == 60
    
    # First time user: 75 + 10 = 85
    s3 = SessionState(session_id="s3", customer_id="c3", total_past_sessions=0)
    assert get_adaptive_threshold(s3) == 85


def test_hysteresis_flapping_prevention():
    """Ensure a transient single-turn spike does not trigger escalation."""
    session = SessionState(session_id="h1", customer_id="c1", total_past_sessions=1, current_score=80.0)
    
    # Base threshold is 75. Score of 80 is a breach.
    # Check transient spike (e.g. 5 seconds elapsed)
    escalated = evaluate_escalation(session, time_delta_seconds=5.0)
    assert not escalated  # Transient spike must not trigger immediate escalation
    
    # Sustained breach (e.g., another 30 seconds elapsed)
    escalated = evaluate_escalation(session, time_delta_seconds=30.0)
    assert escalated  # Sustained breach triggers escalation successfully


def test_circuit_breaker_handover():
    """Verify circuit-breaker silences LLM and pushes session details to queue."""
    clear_all_sessions_for_testing()
    session = SessionState(
        session_id="cb1", customer_id="c1", current_score=85.0, escalated=False
    )
    
    res = execute_circuit_breaker(session, "irritation_breach", ["Help me!"])
    assert session.escalated
    assert res["status"] == "escalated_to_agent"
