# tests/test_retention.py
# Pytest suite for coupon fraud gates, cooldowns, and payout eligibility checks

import time
import pytest
from guardrail.session.schema import SessionState
from guardrail.retention.coupon import should_issue_coupon, issue_retention_coupon


def test_coupon_fraud_gate_first_time():
    """Verify first-time claimant passes fraud gate if irritation is sustained."""
    session = SessionState(
        session_id="ret_1",
        customer_id="c_1",
        irritation_duration_seconds=70.0,  # Exceeds MIN_IRRITATION_DURATION (60s)
        lifetime_coupons_claimed=0,
        last_coupon_issued_at=None,
    )
    assert should_issue_coupon(session)


def test_coupon_fraud_gate_cooldown_boundary():
    """Verify cooldown rules block repeat payouts inside 30-day window."""
    now = time.time()
    
    # Repeat claim inside 30-day window (e.g. 15 days ago)
    session_recent = SessionState(
        session_id="ret_2",
        customer_id="c_2",
        irritation_duration_seconds=70.0,
        lifetime_coupons_claimed=1,
        last_coupon_issued_at=now - (15 * 86400.0),
    )
    assert not should_issue_coupon(session_recent)
    
    # Repeat claim outside 30-day window (e.g. 35 days ago)
    session_old = SessionState(
        session_id="ret_3",
        customer_id="c_3",
        irritation_duration_seconds=70.0,
        lifetime_coupons_claimed=1,
        last_coupon_issued_at=now - (35 * 86400.0),
    )
    assert should_issue_coupon(session_old)


def test_coupon_fraud_gate_duration_gaming():
    """Verify rapid score spikes without sustained irritation fail the gate."""
    session = SessionState(
        session_id="ret_4",
        customer_id="c_4",
        irritation_duration_seconds=10.0,  # Below 60s minimum threshold
        lifetime_coupons_claimed=0,
        last_coupon_issued_at=None,
    )
    assert not should_issue_coupon(session)


def test_coupon_fraud_gate_lifetime_cap():
    """Verify lifetime coupon limits block payouts after 3 claims."""
    session = SessionState(
        session_id="ret_5",
        customer_id="c_5",
        irritation_duration_seconds=70.0,
        lifetime_coupons_claimed=3,  # Max lifetime coupons limit reached
        last_coupon_issued_at=None,
    )
    assert not should_issue_coupon(session)


@pytest.mark.asyncio
async def test_coupon_issuance_execution():
    """Verify that eligible sessions yield coupon codes and update stats."""
    session = SessionState(
        session_id="ret_6",
        customer_id="c_6",
        irritation_duration_seconds=80.0,
        lifetime_coupons_claimed=1,
        last_coupon_issued_at=None,
    )
    
    code = await issue_retention_coupon(session)
    assert code is not None
    assert code.startswith("CALM-RETAIN-")
    assert session.lifetime_coupons_claimed == 2
    assert session.last_coupon_issued_at is not None
