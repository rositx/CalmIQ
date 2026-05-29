# guardrail/scoring/matrix.py
# Core Irritation Score aggregator engine (Matrix calculation)

from typing import Optional
from guardrail.config import (
    SENTIMENT_WEIGHT,
    TELEMETRY_WEIGHT,
    CONTEXT_WEIGHT,
    SENTIMENT_WEIGHT_DEGRADED,
    CONTEXT_WEIGHT_DEGRADED,
)


def calculate_irritation_score(
    sentiment_score: float,
    telemetry_score: Optional[float],
    context_score: float,
) -> float:
    """Calculate aggregate Irritation Score (0-100) using active config weights."""
    if telemetry_score is None:
        # Degraded Mode: Re-weight S and C higher due to telemetry outage
        score = (sentiment_score * SENTIMENT_WEIGHT_DEGRADED) + (
            context_score * CONTEXT_WEIGHT_DEGRADED
        )
    else:
        # Standard Mode: Full matrix scoring with S, B, and C
        score = (
            (sentiment_score * SENTIMENT_WEIGHT)
            + (telemetry_score * TELEMETRY_WEIGHT)
            + (context_score * CONTEXT_WEIGHT)
        )
        
    return min(100.0, max(0.0, score))
