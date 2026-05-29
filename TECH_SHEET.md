# AI Guardrail Middleware — Technical Specification Sheet

## System Overview

A backend-heavy, asynchronous middleware service that intercepts messages between a customer chat frontend and a company's AI support bot. Computes a real-time Irritation Score per session and executes a circuit-breaker escalation protocol when the score exceeds a configured threshold.

The middleware is AI-agnostic and frontend-agnostic. It integrates via a proxy endpoint pattern — the client sends messages to the middleware instead of directly to the LLM, and the middleware forwards, monitors, and intercepts as needed.

---

## Architecture

### Request Flow

```
[ Customer Chat UI ]
        │
        ▼
POST /api/v1/chat/message  ←── All traffic enters here
        │
        ├──► [Telemetry Ingestion]     (optional behavioral signals)
        │
        ├──► [Message Router / Interceptor]
        │           │
        │           ├──► [NLP Sentiment Layer]   ──► S score (0–100)
        │           ├──► [Behavioral Telemetry]  ──► B score (0–100)
        │           └──► [Conversational Context]──► C score (0–100)
        │
        ├──► [Irritation Matrix Engine]
        │       Irritation Score = (S × 0.4) + (B × 0.3) + (C × 0.3)
        │       Session state stored in Redis
        │
        ├── Score < Threshold ──► Forward to LLM, return response
        │
        └── Score ≥ Threshold ──► Circuit Breaker
                    │
                    ├──► Sever LLM connection for session
                    ├──► Push to Human Agent WebSocket Queue
                    ├──► Fire Coupon Engine API (if fraud gate passes)
                    └──► Log escalation event to PostgreSQL
```

---

## Scoring Algorithm

### Master Formula

```
Irritation Score = (S × 0.4) + (B × 0.3) + (C × 0.3)
```

All component scores are normalized to 0–100 before being combined.

### Component 1: Linguistic Sentiment Score (S) — 40%

Computed by a local transformer-based classifier on each incoming message.

Signals that increase S:
- Negative sentiment classification (anger, frustration, disgust)
- Presence of trigger keywords: `cancel`, `refund`, `manager`, `human`, `representative`, `useless`, `broken`, `terrible`, profanity list
- ALL CAPS words (ratio of caps-lock words to total words)
- Repeated punctuation patterns: `!!!`, `???`, `....`
- Rapid sentiment shift from neutral/positive to strongly negative across the last 3 turns

Model: `cardiffnlp/twitter-roberta-base-sentiment-latest` as baseline.
Target upgrade: fine-tuned domain-specific classifier trained on labeled session data once 500+ labeled examples are available.
Runtime: ONNX-exported model via `onnxruntime` for low-latency inference.

### Component 2: Behavioral Telemetry Score (B) — 30%

Frontend streams interaction events via WebSocket alongside message payloads. B score is computed only when telemetry is available; if absent, the formula rebalances:

```python
# With telemetry
score = (S * 0.4) + (B * 0.3) + (C * 0.3)

# Without telemetry (graceful degradation)
score = (S * 0.55) + (C * 0.45)
```

Telemetry signals:
- **Rage clicking:** Submit/refresh button click frequency in a 10-second window
- **Repetitive inputs:** Cosine similarity between the last 3 user messages. High similarity = user is copy-pasting the same question
- **Typing velocity anomalies:** Bursts of fast typing followed by abrupt long pauses

Frontend integration: a drop-in JavaScript snippet (similar to Hotjar/Intercom pattern) that companies embed in their chat widget. One `<script>` tag. No SDK required.

### Component 3: Conversational Context Score (C) — 30%

Computed from session state stored in Redis.

Signals that increase C:
- **AI response loop:** Cosine similarity across the last 3 AI responses. If the AI is repeating itself, C rises sharply.
- **User message loop:** Cosine similarity across the last 3 user messages. User repetition is weighted higher than AI repetition (0.6 vs 0.4 in the C sub-score).
- **Turn count without resolution:** Sessions that exceed a configured turn limit without a `resolved` flag receive a C penalty.
- **Unresolved repeat visitor:** Customer has opened multiple sessions for the same issue without resolution.

---

## Adaptive Threshold System

Static threshold: `75` (defined in `config.py` as `BASE_ESCALATION_THRESHOLD`)

Adaptive modifier logic (computed per session at evaluation time):

```python
def get_adaptive_threshold(session) -> int:
    threshold = BASE_ESCALATION_THRESHOLD  # 75

    if session.customer_ltv > HIGH_VALUE_LTV_THRESHOLD:
        threshold -= 15  # escalate earlier for high-value customers

    if session.total_past_sessions == 0:
        threshold += 10  # more patience for first-time users

    if session.recent_complaint_count > 0:
        threshold -= 20  # escalate much earlier for returning complainants

    return max(40, min(90, threshold))  # hard floor/ceiling
```

All threshold constants live in `config.py`.

### Hysteresis

Prevents alert flapping for sessions hovering near the threshold.

- Alert fires when score crosses `ESCALATION_THRESHOLD` and stays above for at least `HYSTERESIS_WINDOW_SECONDS`
- Alert only clears when score drops below `ESCALATION_RESET_THRESHOLD` (default: 55) and holds for `HYSTERESIS_RESET_SECONDS`

---

## Circuit Breaker Protocol

When threshold is exceeded:

1. **AI Silencing:** The session's LLM connection is marked as severed in Redis. Any subsequent messages from this session ID are blocked from reaching the LLM until a human agent manually re-enables it or closes the session.

2. **Human Agent Handover:** Session is pushed to the Human Agent Queue via WebSocket. Payload includes: session ID, full conversation history, current irritation score, primary trigger reason, customer metadata.

3. **Queue Depth Check:** Before escalating, the system checks `AGENT_QUEUE_MAX_DEPTH` in Redis. If the queue is at capacity, the customer receives a fallback message with an honest wait-time estimate rather than a promise of instant connection.

4. **Compensation Trigger:** An API call is fired to the company's CRM/Promo engine if the fraud gate passes (see below).

---

## Coupon Fraud Gate

```python
def should_issue_coupon(session) -> bool:
    if session.last_coupon_issued_at > (now() - COUPON_COOLDOWN_DAYS):
        return False

    if session.irritation_duration_seconds < MIN_IRRITATION_DURATION_FOR_COUPON:
        return False  # spike too fast, likely gaming

    if session.lifetime_coupons_claimed >= MAX_LIFETIME_COUPONS:
        return False  # flag for human review instead

    return True
```

All constants (`COUPON_COOLDOWN_DAYS`, `MIN_IRRITATION_DURATION_FOR_COUPON`, `MAX_LIFETIME_COUPONS`) defined in `config.py`.

---

## Data Models

### Session State (Redis — TTL: 24 hours)

```json
{
  "session_id": "string",
  "customer_id": "string",
  "current_score": 0,
  "score_history": [float],
  "turn_count": 0,
  "ai_response_embeddings": [vector],
  "user_message_embeddings": [vector],
  "escalated": false,
  "escalation_reason": "string | null",
  "resolved": false,
  "last_updated": "timestamp"
}
```

### Session Log (PostgreSQL — permanent)

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    customer_id VARCHAR,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    peak_irritation_score FLOAT,
    escalated BOOLEAN,
    escalation_reason VARCHAR,
    resolved BOOLEAN,
    resolution_type VARCHAR,  -- 'ai_resolved' | 'human_resolved' | 'abandoned'
    coupon_issued BOOLEAN,
    turn_count INTEGER
);

CREATE TABLE session_turns (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    turn_index INTEGER,
    role VARCHAR,  -- 'user' | 'ai'
    message TEXT,
    sentiment_score FLOAT,
    irritation_score_at_turn FLOAT,
    timestamp TIMESTAMP
);

CREATE TABLE escalation_events (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    triggered_at TIMESTAMP,
    score_at_trigger FLOAT,
    threshold_at_trigger FLOAT,
    primary_signal VARCHAR,
    agent_id VARCHAR,
    time_to_agent_seconds INTEGER
);
```

---

## Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Backend framework | FastAPI (Python) | Async-native, WebSocket support, fast |
| In-memory state | Redis | Sub-millisecond session reads, TTL support |
| Persistent storage | PostgreSQL | Relational analytics, session logging |
| Sentiment model | `cardiffnlp/twitter-roberta-base-sentiment-latest` | Best out-of-box accuracy on informal conversational text |
| Model runtime | ONNX Runtime | 3–5× faster than full PyTorch for inference |
| Embeddings (cosine similarity) | `sentence-transformers/all-MiniLM-L6-v2` | Lightweight, fast, good semantic similarity on short texts |
| Real-time communication | FastAPI WebSockets | Streaming telemetry + agent queue push |
| Frontend telemetry | Vanilla JS drop-in snippet | Zero-dependency, single `<script>` tag integration |
| ORM | SQLAlchemy (async) | Native FastAPI compatibility |
| Task queue (async jobs) | Celery + Redis broker | Background logging, coupon API calls |
| Testing | pytest + httpx | Async-compatible test client |
| Containerisation | Docker + Docker Compose | Sidecar deployment or standalone service |

---

## Multilingual Support

Default models are English-biased. For deployments involving code-switched language (Hindi-English, Tamil-English, etc.):

- Replace `cardiffnlp/twitter-roberta-base-sentiment-latest` with `cardiffnlp/twitter-xlm-roberta-base-sentiment` (multilingual variant)
- Replace `all-MiniLM-L6-v2` with `paraphrase-multilingual-MiniLM-L12-v2` for cosine similarity calculations
- Both are drop-in replacements with the same interface. Switch is controlled by `MULTILINGUAL_MODE=true` in `config.py`

---

## Latency Budget

Target end-to-end overhead added by middleware (measured from message receipt to LLM forward): **< 80ms**

| Step | Target Latency |
|---|---|
| Redis session read | < 2ms |
| Keyword/regex check | < 1ms |
| ONNX sentiment inference | < 30ms |
| Cosine similarity (embeddings) | < 20ms |
| Redis session write | < 2ms |
| Threshold evaluation + routing | < 5ms |
| **Total middleware overhead** | **< 60ms** |

Coupon API calls and PostgreSQL logging run asynchronously via Celery and do not block the response path.

---

## Deployment

Designed for two deployment modes:

**Sidecar Container:** Runs alongside an existing LLM orchestration stack (e.g., CrewAI, LangChain) in the same Docker Compose or Kubernetes namespace. Communicates via localhost networking for minimal latency.

**Standalone Service:** Deployed independently. The company's chat frontend points to the middleware URL. The middleware forwards to the company's LLM endpoint. No changes required to the LLM setup.

Environment variables control all secrets, endpoints, and threshold overrides. No secrets in code.

---

## Fine-Tuning Pipeline (Post-MVP)

From day one, every sentiment classification is logged alongside its session outcome (`escalated_correctly` / `false_positive` / `missed_escalation`). Once 500+ labeled examples accumulate, a fine-tuning job runs on the domain-specific data. The improved model replaces the baseline. This loop runs monthly. Expected accuracy improvement: significant within 2–3 cycles.
