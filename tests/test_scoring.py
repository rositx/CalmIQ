# tests/test_scoring.py
# Pytest suite for sentiment, telemetry, context, and matrix engines

import pytest
from guardrail.session.schema import SessionState
from guardrail.scoring.sentiment import calculate_sentiment_score
from guardrail.scoring.telemetry import calculate_telemetry_score
from guardrail.scoring.context import calculate_context_score
from guardrail.scoring.matrix import calculate_irritation_score


def test_sentiment_scoring():
    """Verify that S scores scale with keywords, CAPS shouting, and profanities."""
    session = SessionState(session_id="test_s", customer_id="c_1")
    
    # Check baseline positive string
    pos_score = calculate_sentiment_score("Hello, I need some simple help please.", session)
    assert pos_score >= 0.0
    
    # Check angry caps and trigger word escalation
    angry_text = "I WANT TO CANCEL MY UNHELPFUL SUBSCRIPTION RIGHT NOW!!! THIS IS USELESS."
    neg_score = calculate_sentiment_score(angry_text, session)
    assert neg_score > pos_score
    assert neg_score > 50.0


def test_telemetry_scoring():
    """Verify that B scores scale with clicks and fall back to None correctly."""
    session = SessionState(session_id="test_b", customer_id="c_1")
    
    # Normal telemetry behavior
    tel_data = {"rage_clicks": 5, "typing_speed_wpm": 140.0, "typing_pauses": 2}
    telemetry_val = calculate_telemetry_score(tel_data, session)
    assert telemetry_val > 30.0
    
    # Degraded mode validation: Missing telemetry yields None
    assert calculate_telemetry_score(None, session) is None


def test_context_scoring():
    """Verify that C scores flag repeating loop similarities and turn counts."""
    session = SessionState(session_id="test_c", customer_id="c_1", turn_count=15)
    
    # Turn limit penalty verification
    long_session_score = calculate_context_score(session)
    assert long_session_score >= 15.0  # Turn count limit penalty applied
    
    # Sub-loop similarity check
    dummy_emb = [0.1] * 384
    session.ai_response_embeddings = [dummy_emb, dummy_emb, dummy_emb]
    loop_score = calculate_context_score(session)
    assert loop_score > long_session_score


def test_matrix_rebalancing():
    """Verify standard rebalancing and degraded rebalancing matrices."""
    # Standard weighting: (80 * 0.4) + (50 * 0.3) + (60 * 0.3) = 32 + 15 + 18 = 65
    std = calculate_irritation_score(80.0, 50.0, 60.0)
    assert std == pytest.approx(65.0)
    
    # Degraded weighting: (80 * 0.55) + (60 * 0.45) = 44 + 27 = 71
    deg = calculate_irritation_score(80.0, None, 60.0)
    assert deg == pytest.approx(71.0)
