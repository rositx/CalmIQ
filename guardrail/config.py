# guardrail/config.py
# Single repository for all constants, models, and thresholds across CalmIQ

import os

# Multilingual switch for code-switched languages (e.g., Hindi-English)
MULTILINGUAL_MODE = os.getenv("MULTILINGUAL_MODE", "false").lower() == "true"

# Weights used when behavioral telemetry is fully available
SENTIMENT_WEIGHT = 0.4
TELEMETRY_WEIGHT = 0.3
CONTEXT_WEIGHT = 0.3

# Rebalanced weights utilized during telemetry outages or disabled telemetry
SENTIMENT_WEIGHT_DEGRADED = 0.55
CONTEXT_WEIGHT_DEGRADED = 0.45

# Threshold metrics for escalations and returning client behaviors
BASE_ESCALATION_THRESHOLD = 75
ESCALATION_RESET_THRESHOLD = 55
HIGH_VALUE_LTV_THRESHOLD = 10000.0
HYSTERESIS_WINDOW_SECONDS = 30
HYSTERESIS_RESET_SECONDS = 60

# Thresholds for checking conversational loop patterns
AI_LOOP_SIMILARITY_THRESHOLD = 0.85
USER_LOOP_SIMILARITY_THRESHOLD = 0.85
MAX_TURNS_WITHOUT_RESOLUTION = 12

# Coupon anti-fraud gate parameters
COUPON_COOLDOWN_DAYS = 30
MIN_IRRITATION_DURATION_FOR_COUPON = 60
MAX_LIFETIME_COUPONS = 3

# AI model identifiers for sentiment classification and embeddings
SENTIMENT_MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Session management constants
SESSION_TTL_SECONDS = 86400
AGENT_QUEUE_MAX_DEPTH = 50

# Database configurations
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/calmiq")
