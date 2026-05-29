# AI Guardrail Middleware — Non-Negotiable Development Rules

> This file governs all code generation for the AI Guardrail Middleware project.
> Every rule here is mandatory. No exceptions without explicit developer approval.

---

## 1. No Repetitive Code — Ever

- Before writing any new function, search the codebase for existing functions that do the same or similar thing
- If a similar function exists — extend or refactor it, never duplicate it
- If two functions share more than 5 lines of logic — extract the shared logic into a utility function
- Helper functions live in `utils/` — if you find yourself writing the same transformation twice anywhere, it belongs there
- DRY is not a preference here — it is a hard rule

**Before creating any new function ask:**
> "Does something like this already exist in the codebase?"
> If yes — use it, extend it, or refactor it. Never write a parallel version.

---

## 2. Clean Code Standards

- **One responsibility per function** — if a function does two things, split it
- **One responsibility per file** — if a file handles two concerns, split it
- **Max function length: 40 lines** — if it's longer, it should be broken down
- **Max file length: 200 lines** — if it's longer, split it by responsibility
- No commented-out dead code — delete it
- No unused imports — remove them immediately
- No hardcoded magic numbers or strings — use constants from `config.py`
- All thresholds, limits, model names, score weights, and time windows live in `config.py` only

---

## 3. File Structure — Follow This Exactly

```
guardrail/
├── config.py                  # All constants, thresholds, weights, model names — nothing else
├── router.py                  # Intercepts requests, routes to scoring, forwards to LLM or circuit breaker
├── scoring/
│   ├── __init__.py
│   ├── sentiment.py           # Linguistic sentiment scoring (S component) only
│   ├── telemetry.py           # Behavioral telemetry scoring (B component) only
│   ├── context.py             # Conversational context scoring (C component) only
│   └── matrix.py              # Combines S, B, C into final Irritation Score
├── session/
│   ├── __init__.py
│   ├── state.py               # Redis read/write for session state only
│   └── schema.py              # Session data models / Pydantic schemas only
├── escalation/
│   ├── __init__.py
│   ├── threshold.py           # Adaptive threshold calculation + hysteresis logic only
│   ├── circuit_breaker.py     # Silences LLM, triggers handover, fires compensation
│   └── queue.py               # Human agent WebSocket queue management only
├── retention/
│   ├── __init__.py
│   └── coupon.py              # Fraud gate logic + coupon API call only
├── storage/
│   ├── __init__.py
│   ├── schema.py              # PostgreSQL table definitions only
│   └── store.py               # All DB read/write/log operations only
├── utils/
│   ├── __init__.py
│   ├── text.py                # Shared text normalization, keyword detection, caps ratio
│   ├── embedder.py            # Single embedding utility used by all scoring modules
│   └── similarity.py         # Cosine similarity helpers used by context and telemetry
├── api/
│   ├── __init__.py
│   ├── chat.py                # POST /api/v1/chat/message endpoint only
│   ├── telemetry.py           # WebSocket /api/v1/telemetry endpoint only
│   └── agent.py               # Human agent dashboard WebSocket endpoint only
├── middleware.py              # Public entry point: IrritationMiddleware class
└── tests/
    ├── test_scoring.py
    ├── test_escalation.py
    ├── test_session.py
    ├── test_retention.py
    └── test_storage.py
```

**Rules for the structure:**
- Never put scoring logic in escalation files
- Never put session state logic in scoring files
- Never put configuration values outside `config.py`
- Never open a Redis connection outside `session/state.py`
- Never open a PostgreSQL connection outside `storage/store.py`
- `middleware.py` is the public entry point — it imports from everything else, nothing else imports from it
- If a new file is needed that doesn't fit this structure — ask before creating it

---

## 4. Check Before You Create

This is the most important rule operationally.

**Every time before writing a new function or class:**

1. Search for the function name or similar names in the codebase
2. Search for the core logic (e.g., "cosine similarity", "keyword match", "session score")
3. Check `utils/` first — it is the first home for any reusable logic
4. Check if an existing function can be extended with a parameter instead of duplicated

**Specific cases to watch:**
- Embedding text happens in ONE place: `utils/embedder.py` — never inline an embedding call anywhere else
- Cosine similarity happens in ONE place: `utils/similarity.py` — never reimplement it in scoring or context modules
- Text normalization happens in ONE place: `utils/text.py` — never write keyword detection or caps-ratio logic outside it
- Threshold values are read from ONE place: `config.py` — never hardcode `75`, `0.4`, `0.3`, `55`, or any numeric constant inline
- Redis connections are opened in ONE place: `session/state.py` — never open a Redis connection anywhere else
- PostgreSQL connections are opened in ONE place: `storage/store.py` — never open a DB connection anywhere else

---

## 5. Configuration — All of It Lives in config.py

These are the constants that must always be sourced from `config.py` and never hardcoded:

```python
# Score weights
SENTIMENT_WEIGHT = 0.4
TELEMETRY_WEIGHT = 0.3
CONTEXT_WEIGHT = 0.3

# Degraded mode weights (no telemetry)
SENTIMENT_WEIGHT_DEGRADED = 0.55
CONTEXT_WEIGHT_DEGRADED = 0.45

# Thresholds
BASE_ESCALATION_THRESHOLD = 75
ESCALATION_RESET_THRESHOLD = 55
HIGH_VALUE_LTV_THRESHOLD = 10000
HYSTERESIS_WINDOW_SECONDS = 30
HYSTERESIS_RESET_SECONDS = 60

# Context scoring
AI_LOOP_SIMILARITY_THRESHOLD = 0.85
USER_LOOP_SIMILARITY_THRESHOLD = 0.85
MAX_TURNS_WITHOUT_RESOLUTION = 12

# Coupon fraud gate
COUPON_COOLDOWN_DAYS = 30
MIN_IRRITATION_DURATION_FOR_COUPON = 60
MAX_LIFETIME_COUPONS = 3

# Model names
SENTIMENT_MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Redis
SESSION_TTL_SECONDS = 86400
AGENT_QUEUE_MAX_DEPTH = 50
```

If a constant does not exist in `config.py` yet — add it there first, then use it. Never the other way around.

---

## 6. Scoring Rules

- The Irritation Score formula is locked: `(S × 0.4) + (B × 0.3) + (C × 0.3)`
- Weights come from `config.py` — never hardcode them in `matrix.py` or anywhere else
- Every component score (S, B, C) must be independently testable — no entanglement between components
- The degraded formula (no telemetry) must be explicitly handled in `matrix.py` with a clear branch — not a silent default
- All component scores must be normalized to 0–100 before being passed to `matrix.py`

---

## 7. Session State Rules

- Session state is always read from and written to Redis via `session/state.py` — nowhere else
- Every scoring module receives session state as a parameter — it never fetches it directly
- Session state is immutable inside a scoring function — scoring functions return scores, they do not mutate state
- State mutation (updating scores, appending history) happens only in `router.py` after all scores are computed

---

## 8. Escalation Rules

These are architecture decisions already locked. Do not re-architect these:

- **Threshold evaluation** happens in `escalation/threshold.py` only — nowhere else computes "should we escalate"
- **Circuit breaker execution** happens in `escalation/circuit_breaker.py` only — never inline the severance logic in the router
- **Coupon fraud gate** is always checked before any coupon API call — no coupon fires without passing `should_issue_coupon()`
- **Queue depth check** always runs before pushing to the human agent queue — never push without checking `AGENT_QUEUE_MAX_DEPTH`
- **Hysteresis** is always enforced — single-turn spikes never trigger escalation regardless of score

---

## 9. Comments — Small and Purposeful

- **Comment the why, not the what** — the code shows what, the comment explains why
- One short comment per logical block — not per line
- Maximum comment length: one line (under 80 characters)
- Function docstrings: one line only, describing purpose not implementation
- No obvious comments

**Good comment:**
```python
# Degraded mode re-weights S higher since telemetry is unavailable
score = (S * SENTIMENT_WEIGHT_DEGRADED) + (C * CONTEXT_WEIGHT_DEGRADED)
```

**Bad comment:**
```python
# Multiply S by SENTIMENT_WEIGHT_DEGRADED and add C times CONTEXT_WEIGHT_DEGRADED
score = (S * SENTIMENT_WEIGHT_DEGRADED) + (C * CONTEXT_WEIGHT_DEGRADED)
```

---

## 10. Avoid Over-Complexity

- **Simplest working solution first** — optimize only if benchmarks show a problem
- No premature abstraction — don't build a class hierarchy for something a function handles
- No unnecessary design patterns — a simple function beats a Strategy class every time here
- Catch specific exceptions — never use blanket `except Exception` without logging the type
- If a solution feels complex to explain — it is too complex to build. Simplify first.
- Prefer readable over clever — a clear 5-line solution beats a cryptic 1-liner every time

**Complexity check before committing any code:**
> "Can I explain this function in one sentence?"
> If no — it is doing too much. Break it down.

---

## 11. Testing Rules

- Every new function in `scoring/`, `escalation/`, `retention/`, and `storage/` needs a corresponding test
- Tests go in `tests/` matching the module name
- Test with realistic conversational inputs — not just clean synthetic strings
- Test the degraded scoring path (no telemetry) explicitly — it is not covered by the default tests
- Test the fraud gate with edge cases: first-time claimants, repeat claimants, cooldown boundary
- Test hysteresis: a single spike must not escalate, a sustained score must escalate
- If a bug is fixed — add a test that would have caught it
- No test should depend on another test's state — each test is fully isolated
- Mock Redis and PostgreSQL in unit tests — never hit live infrastructure in tests

---

## 12. When You Are Unsure

If a task requires:
- Creating a file outside the defined structure
- Changing the Irritation Score formula or component weights
- Adding a new public method to `IrritationMiddleware`
- Changing a locked architecture decision (Redis for state, PostgreSQL for logs, ONNX for inference)
- Writing more than 200 lines in a single file

**Stop and ask the developer before proceeding.**

Do not make assumptions and build anyway. The cost of undoing a structural decision is higher than the cost of asking.

---

## 13. Quick Reference Checklist

Run this before marking any task complete:

- [ ] Did I check if this function already exists somewhere?
- [ ] Is this function under 40 lines?
- [ ] Is this file under 200 lines?
- [ ] Are all constants in `config.py`?
- [ ] Is embedding only called through `utils/embedder.py`?
- [ ] Is cosine similarity only called through `utils/similarity.py`?
- [ ] Is text normalization only called through `utils/text.py`?
- [ ] Is Redis only accessed through `session/state.py`?
- [ ] Is PostgreSQL only accessed through `storage/store.py`?
- [ ] Did I add a test for new logic?
- [ ] Did I test the degraded path if I touched scoring?
- [ ] Are comments explaining why, not what?
- [ ] Can I explain every new function in one sentence?
- [ ] Did I remove all unused imports and dead code?
