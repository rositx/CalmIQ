# guardrail/utils/text.py
# Preprocessing, normalization, caps ratio, and punctuation analysis helpers

import re
from typing import Set
from guardrail.config import TRIGGER_KEYWORDS, PROFANITY_KEYWORDS


def normalize_text(text: str) -> str:
    """Normalize input text for consistent keyword search and tokenization."""
    if not text:
        return ""
    # Convert to lowercase and strip excess whitespace
    return " ".join(text.lower().split())


def get_caps_ratio(text: str) -> float:
    """Compute the ratio of ALL CAPS words to total words (ignoring short words)."""
    if not text:
        return 0.0
    words = [w for w in text.split() if any(c.isalpha() for c in w)]
    if not words:
        return 0.0
    # Only count words longer than 1 character to ignore "I", "A", etc.
    caps_words = [w for w in words if w.isupper() and len(w) > 1]
    return len(caps_words) / len(words)


def count_repeated_punctuation(text: str) -> int:
    """Count occurrences of repeated punctuation patterns like !!!, ???, or ...."""
    if not text:
        return 0
    # Matches three or more repeated exclamation/question marks or periods
    pattern = r"([!?\.])\1{2,}"
    return len(re.findall(pattern, text))


def scan_keywords(text: str) -> Set[str]:
    """Scan normalized text for pre-configured trigger words."""
    normalized = normalize_text(text)
    words = set(re.findall(r"\b\w+\b", normalized))
    return words.intersection(set(TRIGGER_KEYWORDS))


def scan_profanity(text: str) -> Set[str]:
    """Scan normalized text for pre-configured profanities."""
    normalized = normalize_text(text)
    words = set(re.findall(r"\b\w+\b", normalized))
    return words.intersection(set(PROFANITY_KEYWORDS))
