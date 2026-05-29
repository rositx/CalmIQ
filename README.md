# CalmIQ AI Guardrail Middleware

CalmIQ is a smart, real-time monitoring and safety layer that intercepts conversational exchanges between customer frontends and AI support chatbots. It continuously calculates a multi-dimensional **Irritation Score** (S, B, and C components) and triggers a circuit-breaker handover protocol to route frustrated users to human support agents before abandonment.

---

## Folder Architecture

The codebase follows the strict folder mapping layout specified by `RULES.md`:

```
guardrail/
├── config.py                  # All weights, thresholds, limits, and configurations
├── router.py                  # Intercepts requests, computes scores, coordinates handovers
├── scoring/
│   ├── sentiment.py           # S-Component: RoBERTa neural sentiment & lexical keywords
│   ├── telemetry.py           # B-Component: Rage clicks, typing speed, and repeat copy-pastes
│   ├── context.py             # C-Component: AI repetition loops and turn penalties
│   └── matrix.py              # Score aggregator re-weighting normal/degraded modes
├── session/
│   ├── schema.py              # Active Redis state Pydantic structures
│   └── state.py               # Redis read/write connectors with local fallbacks
├── escalation/
│   ├── threshold.py           # Customer-specific adaptive thresholds and hysteresis holds
│   ├── circuit_breaker.py     # AI silencer, queue checker, and PostgreSQL event logger
│   └── queue.py               # Active WebSocket dashboard broadcasting for agents
├── retention/
│   └── coupon.py              # Anti-fraud cooldowns and minimum duration coupon triggers
├── storage/
│   ├── schema.py              # PostgreSQL database SQLAlchemy declaratives
│   └── store.py               # Asynchronous session turn and escalation loggers
├── utils/
│   ├── text.py                # Text normalization, word counting, and caps ratio checks
│   ├── embedder.py            # SentenceTransformer embeddings loader and fallback hashes
│   └── similarity.py          # Vector cosine similarity algorithms
└── middleware.py              # Public entry gateway class (IrritationMiddleware)

tests/                         # Diagnostic testing suite mapping each module
```

---

## Getting Started

### 1. Requirements Installation
CalmIQ utilizes standard async frameworks. To install dependencies:
```bash
pip install fastapi uvicorn pydantic sqlalchemy redis sentence-transformers transformers torch websockets
```

To run unit tests, ensure `pytest` and `pytest-asyncio` are installed:
```bash
pip install pytest pytest-asyncio
```

### 2. Running Diagnostic Tests
We provide a comprehensive unit and integration test suite covering scoring rebalancing, hysteresis periods, state isolation, database logs, and anti-gaming fraud rules:
```bash
python -m pytest
```

---

## Running Sample Conversation Demonstrations

We have provided a turnkey simulation script, `demo_conversation.py`, to test and witness the middleware in action. 

The script simulates a customer who:
1. Starts with a standard request (Low Irritation).
2. Experiences delay, expressing mild frustration (Medium Irritation).
3. Becomes highly irritated, shouting in ALL CAPS, using trigger keywords, and executing rage clicks (High Irritation breaching the gate).

Since the customer is marked as a **High-Value Client** with **past complaints**, the middleware automatically adjusts the adaptive threshold down to **40.0** to escalate quicker.

### Run the Simulation
Execute the demonstration from the root directory:
```bash
python demo_conversation.py
```

### Expected Output
```text
=== CalmIQ AI Guardrail Middleware Simulation ===

Customer Value: $15000.0
Past Complaints: 1
Standard Threshold: 75 -> Adjusted Adaptive Threshold: 40

--- Turn 1 ---
Customer: Hello, I need to check the status of my refund.
Aggregate Irritation Score: 0.0/100
AI Bot Response: Thank you for your message. I am here to help you: Hello, I need to check the status of my refund.

--- Turn 2 ---
Customer: It has been three weeks! This delay is extremely slow.
Aggregate Irritation Score: 7.9/100
AI Bot Response: Thank you for your message. I am here to help you: It has been three weeks! This delay is extremely slow.

--- Turn 3 ---
Customer: THIS IS USELESS. REFUND MY MONEY AND LET ME SPEAK TO A MANAGER RIGHT NOW!!!
Status: CIRCUIT BREAKER TRIGGERED (escalated_to_agent)
Primary Trigger Reason: irritation_breach
Retention Promo Code Issued: CALM-RETAIN-XXXX
Middleware Action: Chat has been transferred to a human agent. Sent coupon: CALM-RETAIN-XXXX
```
