# guardrail/session/state.py
# Single repository for all Redis database reads, writes, and queue pushes

import json
from typing import Optional, List
from guardrail.config import REDIS_URL, SESSION_TTL_SECONDS
from guardrail.session.schema import SessionState

# Local process fallbacks for development and unit testing without infrastructure
_MEMORY_STORE = {}
_MEMORY_QUEUE = []
_REDIS_CLIENT = None


def _get_client():
    """Retrieve or initialize the Redis client with an in-memory fallback."""
    global _REDIS_CLIENT
    if _REDIS_CLIENT is not None:
        return _REDIS_CLIENT
        
    try:
        import redis
        # Set a short socket timeout to fail fast if Redis is down
        client = redis.from_url(REDIS_URL, socket_timeout=1.0, decode_responses=True)
        client.ping()
        _REDIS_CLIENT = client
    except Exception:
        # Fallback to None indicates we must use local process memory
        _REDIS_CLIENT = False
        
    return _REDIS_CLIENT


def get_session(session_id: str) -> Optional[SessionState]:
    """Retrieve session state from Redis or local memory fallback."""
    client = _get_client()
    if not client:
        data = _MEMORY_STORE.get(session_id)
        return SessionState.model_validate_json(data) if data else None
        
    try:
        data = client.get(f"session:{session_id}")
        return SessionState.model_validate_json(data) if data else None
    except Exception:
        data = _MEMORY_STORE.get(session_id)
        return SessionState.model_validate_json(data) if data else None


def save_session(session_id: str, state: SessionState) -> None:
    """Save session state to Redis with configured TTL or local memory fallback."""
    serialized = state.model_dump_json()
    client = _get_client()
    if not client:
        _MEMORY_STORE[session_id] = serialized
        return
        
    try:
        client.setex(f"session:{session_id}", SESSION_TTL_SECONDS, serialized)
    except Exception:
        _MEMORY_STORE[session_id] = serialized


def push_to_agent_queue(session_id: str, payload: dict) -> None:
    """Push an escalated session payload to the human agent queue."""
    serialized = json.dumps(payload)
    client = _get_client()
    if not client:
        _MEMORY_QUEUE.append(serialized)
        return
        
    try:
        client.rpush("agent_queue", serialized)
    except Exception:
        _MEMORY_QUEUE.append(serialized)


def get_agent_queue_depth() -> int:
    """Retrieve the current depth of the human agent queue."""
    client = _get_client()
    if not client:
        return len(_MEMORY_QUEUE)
        
    try:
        return client.llen("agent_queue")
    except Exception:
        return len(_MEMORY_QUEUE)


def clear_all_sessions_for_testing() -> None:
    """Clear memory stores to isolate tests."""
    global _REDIS_CLIENT
    _MEMORY_STORE.clear()
    _MEMORY_QUEUE.clear()
    _REDIS_CLIENT = None
