# CalmIQ AI Guardrail Middleware — Project Phases and Submodules

This document outlines the breakdown of the CalmIQ AI Guardrail Middleware project into structured implementation phases. Each submodule is associated with a dedicated git branch.

---

## Development Phases and Branches

```
Phase 0: Base Repository Setup (Branch: main)
   └── RULES.md, SPEC_SHEET.md, TECH_SHEET.md, PHASES.md

Phase 1: Configuration and State Schemas (Branch: feature/config-schemas)
   ├── guardrail/config.py
   └── guardrail/session/schema.py

Phase 2: Common Utilities (Branch: feature/utilities)
   ├── guardrail/utils/text.py
   ├── guardrail/utils/embedder.py
   └── guardrail/utils/similarity.py

Phase 3: State and Storage Persistence (Branch: feature/state-storage)
   ├── guardrail/session/state.py
   ├── guardrail/storage/schema.py
   └── guardrail/storage/store.py

Phase 4: Component Scoring Modules (Branch: feature/scoring-engines)
   ├── guardrail/scoring/sentiment.py
   ├── guardrail/scoring/telemetry.py
   ├── guardrail/scoring/context.py
   └── guardrail/scoring/matrix.py

Phase 5: Escalation and Hysteresis Engine (Branch: feature/escalation-engine)
   ├── guardrail/escalation/threshold.py
   ├── guardrail/escalation/circuit_breaker.py
   └── guardrail/escalation/queue.py

Phase 6: Retention Systems (Branch: feature/retention-systems)
   └── guardrail/retention/coupon.py

Phase 7: Unified Middleware and API Layer (Branch: feature/api-middleware)
   ├── guardrail/api/chat.py
   ├── guardrail/api/telemetry.py
   ├── guardrail/api/agent.py
   └── guardrail/middleware.py

Phase 8: Diagnostic Unit and Integration Tests (Branch: feature/testing)
   ├── tests/test_scoring.py
   ├── tests/test_escalation.py
   ├── tests/test_session.py
   ├── tests/test_retention.py
   └── tests/test_storage.py
```

---

## Detailed Submodule Breakdown

### Submodule 1: Global Configuration (`guardrail/config.py`)
- **Purpose:** Store all system-wide thresholds, weights, and parameters in a single, non-hardcoded namespace.
- **Branch:** `feature/config-schemas`

### Submodule 2: Shared Text Utilities (`guardrail/utils/text.py`)
- **Purpose:** Clean, normalize, check for capitalization patterns, and scan text for specific keyword triggers.
- **Branch:** `feature/utilities`

### Submodule 3: Embedder Engine (`guardrail/utils/embedder.py`)
- **Purpose:** Handle model caching and ONNX runtime setup for sentiment classification and cosine similarity calculations.
- **Branch:** `feature/utilities`

### Submodule 4: Similarity Utility (`guardrail/utils/similarity.py`)
- **Purpose:** Compute cosine similarity over vectors to check for loop patterns.
- **Branch:** `feature/utilities`

### Submodule 5: Session Data Models (`guardrail/session/schema.py`)
- **Purpose:** Define runtime telemetry schemas and Redis session state models using Pydantic.
- **Branch:** `feature/config-schemas`

### Submodule 6: Redis State Management (`guardrail/session/state.py`)
- **Purpose:** Save and load active session states, append history arrays, and keep state immutable inside scoring routines.
- **Branch:** `feature/state-storage`

### Submodule 7: Database Store (`guardrail/storage/schema.py`, `guardrail/storage/store.py`)
- **Purpose:** PostgreSQL tables and log writers for analytics, tracking turn-by-turn scores, and escalation history.
- **Branch:** `feature/state-storage`

### Submodule 8: Component Scorers (`guardrail/scoring/`)
- **Purpose:** Compute isolated normalized scores (0-100) for Sentiment (S), Telemetry (B), and Context (C). Combine scores via Matrix scoring engine.
- **Branch:** `feature/scoring-engines`

### Submodule 9: Escalation & Hysteresis (`guardrail/escalation/`)
- **Purpose:** Adjust base thresholds dynamically based on value metrics. Track historical windows to enforce hysteresis.
- **Branch:** `feature/escalation-engine`

### Submodule 10: Retention & Fraud Protection (`guardrail/retention/`)
- **Purpose:** Apply cooldowns and duration constraints before issuing discount vouchers.
- **Branch:** `feature/retention-systems`

### Submodule 11: Unified Proxy API (`guardrail/api/`, `guardrail/middleware.py`)
- **Purpose:** Intercept incoming requests, execute scoring, block LLM access upon breach, and provide WebSocket queue feeds.
- **Branch:** `feature/api-middleware`
