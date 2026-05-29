# guardrail/session/schema.py
# Pydantic data schemas representing the current active session state

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SessionState(BaseModel):
    """Pydantic model representing active user session details in Redis."""

    session_id: str
    customer_id: str
    current_score: float = 0.0
    score_history: List[float] = Field(default_factory=list)
    turn_count: int = 0
    
    # Store historical message embeddings to compute looping similarity
    ai_response_embeddings: List[List[float]] = Field(default_factory=list)
    user_message_embeddings: List[List[float]] = Field(default_factory=list)
    
    # Escalation tracking
    escalated: bool = False
    escalation_reason: Optional[str] = None
    resolved: bool = False
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    # Customer metadata for adaptive thresholds
    customer_ltv: float = 0.0
    total_past_sessions: int = 0
    recent_complaint_count: int = 0
    
    # Coupon and retention metrics
    last_coupon_issued_at: Optional[float] = None
    irritation_duration_seconds: float = 0.0
    lifetime_coupons_claimed: int = 0
