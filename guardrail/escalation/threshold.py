# guardrail/escalation/threshold.py
# Adaptive threshold calculations and hysteresis validation logic

from guardrail.session.schema import SessionState
from guardrail.config import (
    BASE_ESCALATION_THRESHOLD,
    ESCALATION_RESET_THRESHOLD,
    HIGH_VALUE_LTV_THRESHOLD,
    HYSTERESIS_WINDOW_SECONDS,
    HYSTERESIS_RESET_SECONDS,
)


def get_adaptive_threshold(session: SessionState) -> int:
    """Calculate session-specific irritation threshold with bounds [40, 90]."""
    threshold = BASE_ESCALATION_THRESHOLD
    
    # Escalate earlier for high-value customers
    if session.customer_ltv > HIGH_VALUE_LTV_THRESHOLD:
        threshold -= 15
        
    # Grant first-time users slightly more patience
    if session.total_past_sessions == 0:
        threshold += 10
        
    # Escalate much earlier for returning complainants
    if session.recent_complaint_count > 0:
        threshold -= 20
        
    return max(40, min(90, threshold))


def evaluate_escalation(session: SessionState, time_delta_seconds: float) -> bool:
    """Enforce hysteresis rules to evaluate if escalation should trigger or reset."""
    threshold = get_adaptive_threshold(session)
    
    if session.current_score >= threshold:
        # Increment continuous irritation duration
        session.irritation_duration_seconds += time_delta_seconds
        
        # Trigger escalation only if irritation is sustained past window
        if not session.escalated and session.irritation_duration_seconds >= HYSTERESIS_WINDOW_SECONDS:
            return True
    else:
        # If score drops below the reset threshold, hold for cooldown reset
        if session.current_score < ESCALATION_RESET_THRESHOLD:
            # We decrease or check if the duration of low score exceeds reset hold
            if session.escalated:
                # Deduct irritation duration to track calm period
                session.irritation_duration_seconds = max(
                    0.0, session.irritation_duration_seconds - time_delta_seconds
                )
                if session.irritation_duration_seconds == 0.0:
                    return False  # Reset escalation status
            else:
                session.irritation_duration_seconds = 0.0
        else:
            # Score is in middle region, keep current state but stop duration growth
            pass
            
    return session.escalated
