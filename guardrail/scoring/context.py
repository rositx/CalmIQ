# guardrail/scoring/context.py
# Conversational context scoring module (C component) - 0-100 normalized

from guardrail.session.schema import SessionState
from guardrail.utils.similarity import cosine_similarity
from guardrail.config import (
    AI_LOOP_SIMILARITY_THRESHOLD,
    USER_LOOP_SIMILARITY_THRESHOLD,
    MAX_TURNS_WITHOUT_RESOLUTION,
)


def _check_vector_repetition(embeddings: list, threshold: float) -> float:
    """Compare recent vector embeddings to detect looping pattern above threshold."""
    if len(embeddings) < 2:
        return 0.0
        
    sim = cosine_similarity(embeddings[-1], embeddings[-2])
    if len(embeddings) >= 3:
        sim = max(sim, cosine_similarity(embeddings[-1], embeddings[-3]))
        
    # Scale score if similarity breaches the threshold
    if sim >= threshold:
        return 100.0
    elif sim > 0.65:
        # Scale similarity linearly for partial loop patterns
        return (sim - 0.65) / (threshold - 0.65) * 60.0
    return 0.0


def calculate_context_score(session: SessionState) -> float:
    """Compute C score evaluating conversational loop history and turn depth."""
    # 1. AI loop detection (0.4 weight)
    ai_loop = _check_vector_repetition(
        session.ai_response_embeddings, AI_LOOP_SIMILARITY_THRESHOLD
    )
    
    # 2. User loop detection (0.6 weight)
    user_loop = _check_vector_repetition(
        session.user_message_embeddings, USER_LOOP_SIMILARITY_THRESHOLD
    )
    
    # Combined loop subscore
    score = (user_loop * 0.6) + (ai_loop * 0.4)
    
    # 3. Turn count penalty for long unresolved sessions
    if session.turn_count > MAX_TURNS_WITHOUT_RESOLUTION:
        over_limit = session.turn_count - MAX_TURNS_WITHOUT_RESOLUTION
        score += min(30.0, over_limit * 5.0)
        
    # 4. Unresolved repeat visitor penalty
    if session.recent_complaint_count > 0:
        score += 25.0
    elif session.total_past_sessions > 1:
        score += 12.0
        
    return min(100.0, max(0.0, score))
