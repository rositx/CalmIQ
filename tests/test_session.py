# tests/test_session.py
# Pytest suite for session state schema serialization and storage CRUD

from guardrail.session.schema import SessionState
from guardrail.session.state import (
    save_session,
    get_session,
    push_to_agent_queue,
    get_agent_queue_depth,
    clear_all_sessions_for_testing,
)


def test_session_serialization():
    """Verify session serialization schema matches Pydantic constraints."""
    session = SessionState(
        session_id="test_schema",
        customer_id="c_100",
        customer_ltv=500.0,
        recent_complaint_count=1,
    )
    dumped = session.model_dump()
    assert dumped["session_id"] == "test_schema"
    assert dumped["customer_id"] == "c_100"
    assert dumped["customer_ltv"] == 500.0
    assert not dumped["escalated"]


def test_session_state_crud():
    """Verify session state storage write and read routines."""
    clear_all_sessions_for_testing()
    session = SessionState(
        session_id="session_crud_1",
        customer_id="c_5",
        current_score=40.0,
    )
    save_session("session_crud_1", session)
    
    fetched = get_session("session_crud_1")
    assert fetched is not None
    assert fetched.session_id == "session_crud_1"
    assert fetched.current_score == 40.0


def test_queue_push_depth():
    """Verify agent queue pushes and depth calculations."""
    clear_all_sessions_for_testing()
    assert get_agent_queue_depth() == 0
    
    payload = {"session_id": "s_1", "reason": "irritation"}
    push_to_agent_queue("s_1", payload)
    
    assert get_agent_queue_depth() == 1
