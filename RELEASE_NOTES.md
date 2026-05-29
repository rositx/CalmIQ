# CalmIQ AI Guardrail Middleware — V1 Release Notes

This document provides formal release details, structural highlights, and feature specifications for the CalmIQ AI Guardrail Middleware integration.

---

## Major Features

### 1. Global Configuration and Unified Session Schema
- **Module:** `guardrail/config.py`, `guardrail/session/schema.py`
- **Capabilities:**
  - Consolidated single source of truth for weights, thresholds, model identifiers, and timing parameters.
  - Multi-stage Pydantic data schemas representing active session states and metadata (including LTV, turn counts, and complaint history).
  - Multilingual switch capability for code-switched deployments (Hinglish/Tamil-English) by environment flags.

### 2. Standardized Preprocessing and Cosine Similarity Utilities
- **Module:** `guardrail/utils/`
- **Capabilities:**
  - Capitalization shouting ratio computation and repeated punctuation pattern scanning.
  - Keyword and profanity trigger matching.
  - Pure-Python cosine similarity calculations over dense embedding arrays.
  - Resilient HuggingFace sentence transformer loading with a local deterministic hash fallback to guarantee offline utility.

### 3. Session State & Event Logging Adapters
- **Module:** `guardrail/session/state.py`, `guardrail/storage/`
- **Capabilities:**
  - High-performance serialization read/write wrappers mapping active session details to Redis.
  - Relational database schema models for permanent SQL storage.
  - Turn-by-turn chat history logging and peak irritation score tracking.
  - Automatic thread-safe in-memory fallback stores to allow standalone deployments without database dependencies.

### 4. Isolated Multi-Dimensional Scoring
- **Module:** `guardrail/scoring/`
- **Capabilities:**
  - S-Score (Sentiment): Evaluates neural angry probability, CAPS shout ratios, trigger keywords, profanities, and rapid shift velocities.
  - B-Score (Behavioral): Evaluates submit click frequencies, typing anomalies, and user input duplication.
  - C-Score (Context): Detects conversation loops on both AI and user turns, applying turn depth penalties.
  - Rebalanced re-weighting formulas automatically activated during telemetry outages (degraded mode).

### 5. Adaptive Threshold & Hysteresis Escalation System
- **Module:** `guardrail/escalation/`
- **Capabilities:**
  - Dynamically lowers thresholds for high-LTV customers and returning complainants, while extending patience for first-time clients.
  - Continuous breach tracking ensures transient spikes do not flap alerts.
  - Multi-stage circuit breaker severing sequence, gracefully silencing LLMs, evaluating queue capacities, pushing details to live agent dashboards, and writing log entries.

### 6. Anti-Gaming Retention coupon Gate
- **Module:** `guardrail/retention/coupon.py`
- **Capabilities:**
  - Three-stage fraud check gate ensuring store voucher payouts are only issued for genuine, sustained irritation events.
  - Restricts voucher redemption frequency by 30-day cooldown blocks and caps lifetime coupon counts.

### 7. REST & WebSocket Proxy Gateway API
- **Module:** `guardrail/middleware.py`, `guardrail/router.py`, `guardrail/api/`
- **Capabilities:**
  - Standardized ASGI proxy middleware class intercepting raw incoming requests.
  - REST POST routing `/api/v1/chat/message` executing full evaluation workflows.
  - WebSocket `/api/v1/telemetry/{session_id}` route capturing live click telemetry.
  - WebSocket `/api/v1/agent/dashboard` route registering active human support agents to receive real-time streams.

### 8. Full Pytest Diagnostics Suite
- **Module:** `tests/`
- **Capabilities:**
  - Independent unit and integration coverage for scoring, session persistence, thresholds, fraud rules, and storage logs.
  - Total test coverage: 18 passed tests.
