# guardrail/scoring/sentiment.py
# Linguistic sentiment scoring module (S component) - 0-100 normalized

from guardrail.session.schema import SessionState
from guardrail.utils.text import (
    get_caps_ratio,
    count_repeated_punctuation,
    scan_keywords,
    scan_profanity,
)

# Cached pipeline instance for transformer model
_TRANSFORMER_PIPELINE = None


def _get_model_sentiment(text: str) -> float:
    """Load CardiffNLP RoBERTa model or execute lexical fallback to return neg probability."""
    global _TRANSFORMER_PIPELINE
    try:
        from transformers import pipeline
        if _TRANSFORMER_PIPELINE is None:
            # CardiffNLP Twitter RoBERTa sentiment analysis pipeline
            from guardrail.config import SENTIMENT_MODEL_NAME
            _TRANSFORMER_PIPELINE = pipeline(
                "sentiment-analysis", model=SENTIMENT_MODEL_NAME, device=-1
            )
        result = _TRANSFORMER_PIPELINE(text)[0]
        label = result["label"].lower()
        score = float(result["score"])
        
        # 'negative' label corresponds to high linguistic irritation
        if "neg" in label or "label_0" in label:
            return score
        elif "neu" in label or "label_1" in label:
            return score * 0.15
        return 0.0
    except Exception:
        # High-integrity regex/word matching fallback
        negative_words = {"angry", "mad", "hate", "stupid", "dumb", "annoyed", "frustrated", "bad"}
        words = text.lower().split()
        if not words:
            return 0.0
        match_count = sum(1 for w in words if w in negative_words)
        return min(1.0, (match_count / len(words)) * 2.5)


def _calculate_shift_penalty(session: SessionState) -> float:
    """Analyze shift in irritation scores across the last 3 turns to identify escalation speed."""
    history = session.score_history
    if len(history) < 2:
        return 0.0
    # Determine difference between recent turn and historical baseline
    recent_diff = history[-1] - history[-2]
    if len(history) >= 3:
        recent_diff = (history[-1] - history[-3]) / 2.0
        
    # Scale positive velocity shifts into a maximum 20-point penalty
    return min(20.0, max(0.0, recent_diff * 0.8))


def calculate_sentiment_score(text: str, session: SessionState) -> float:
    """Compute normalized S score based on model sentiment, triggers, caps, and shifts."""
    if not text:
        return 0.0
        
    # 1. Base neural probability (0.0 to 1.0)
    base_neg_prob = _get_model_sentiment(text)
    score = base_neg_prob * 45.0
    
    # 2. Trigger keywords and profanity checks
    score += len(scan_keywords(text)) * 15.0
    score += len(scan_profanity(text)) * 25.0
    
    # 3. Capitalization Shout Penalty
    caps = get_caps_ratio(text)
    if caps > 0.3:
        score += caps * 35.0
        
    # 4. Repeated punctuation penalty
    punc_repeats = count_repeated_punctuation(text)
    score += min(30.0, punc_repeats * 10.0)
    
    # 5. Rapid velocity shifts penalty
    score += _calculate_shift_penalty(session)
    
    return min(100.0, max(0.0, score))
