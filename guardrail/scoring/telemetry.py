# guardrail/scoring/telemetry.py
# Behavioral telemetry scoring module (B component) - 0-100 normalized

from typing import Optional, Dict
from guardrail.session.schema import SessionState
from guardrail.utils.similarity import cosine_similarity


def _get_input_repetition_score(session: SessionState) -> float:
    """Calculate similarity of historical user message embeddings to flag repetition."""
    embeds = session.user_message_embeddings
    if len(embeds) < 2:
        return 0.0
        
    # Check similarity of the last input with the previous turn
    sim = cosine_similarity(embeds[-1], embeds[-2])
    if len(embeds) >= 3:
        # Check similarity with two turns ago and take the maximum overlap
        sim = max(sim, cosine_similarity(embeds[-1], embeds[-3]))
        
    # High similarity (>0.80) signals copy-pasting the same query
    if sim > 0.80:
        return (sim - 0.80) / 0.20 * 35.0
    return 0.0


def calculate_telemetry_score(
    telemetry_data: Optional[Dict], session: SessionState
) -> Optional[float]:
    """Compute behavioral telemetry B score or return None if telemetry is missing."""
    if not telemetry_data:
        return None
        
    score = 0.0
    
    # 1. Rage Clicking Check (button clicks in a 10s window)
    rage_clicks = float(telemetry_data.get("rage_clicks", 0))
    score += min(45.0, rage_clicks * 9.0)
    
    # 2. Input repetition checking (Backend calculations)
    score += _get_input_repetition_score(session)
    
    # 3. Typing speed anomalies (WPM spikes + abrupt pauses)
    wpm = float(telemetry_data.get("typing_speed_wpm", 0.0))
    pauses = int(telemetry_data.get("typing_pauses", 0))
    
    if wpm > 130.0 or pauses > 3:
        score += min(20.0, pauses * 5.0 + (wpm / 15.0))
        
    return min(100.0, max(0.0, score))
