# guardrail/retention/coupon.py
# Customer retention coupon anti-gaming rules and distribution triggers

import time
from typing import Optional
from guardrail.session.schema import SessionState
from guardrail.config import (
    COUPON_COOLDOWN_DAYS,
    MIN_IRRITATION_DURATION_FOR_COUPON,
    MAX_LIFETIME_COUPONS,
)


def should_issue_coupon(session: SessionState) -> bool:
    """Enforce three-stage fraud gate logic before allocating store promo codes."""
    now = time.time()
    
    # 1. Cooldown restriction: standard 30-day boundary check
    if session.last_coupon_issued_at is not None:
        cooldown_seconds = COUPON_COOLDOWN_DAYS * 86400.0
        if now - session.last_coupon_issued_at < cooldown_seconds:
            return False
            
    # 2. Duration restriction: irritation must be sustained (prevents instant gamification)
    if session.irritation_duration_seconds < MIN_IRRITATION_DURATION_FOR_COUPON:
        return False
        
    # 3. Lifetime cap restriction: maximum limits per customer ID
    if session.lifetime_coupons_claimed >= MAX_LIFETIME_COUPONS:
        return False
        
    return True


async def issue_retention_coupon(session: SessionState) -> Optional[str]:
    """Verify eligibility and execute promo coupon payout via mocked external API."""
    if not should_issue_coupon(session):
        return None
        
    # Standardised promo code format
    coupon_code = f"CALM-RETAIN-{int(time.time()) % 100000}"
    
    # Mutate session stats securely for tracking
    session.last_coupon_issued_at = time.time()
    session.lifetime_coupons_claimed += 1
    
    # Under real deployments, this issues HTTP POST to /api/promos
    return coupon_code
