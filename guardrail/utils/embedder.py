# guardrail/utils/embedder.py
# Single entry point for generating dense semantic embeddings of conversational text

import hashlib
from typing import List
from guardrail.config import EMBEDDING_MODEL_NAME

# Global cache for the sentence-transformer model instance
_MODEL_INSTANCE = None


def _get_hash_embedding(text: str, dimensions: int = 384) -> List[float]:
    """Generate a deterministic, normalized fallback vector for a given text."""
    vector = [0.0] * dimensions
    words = text.lower().split()
    if not words:
        return vector
        
    for word in words:
        # Generate stable indices for dimensions based on MD5 hashing
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        index = h % dimensions
        vector[index] += 1.0
        
    # L2 normalize the vector
    norm = sum(v * v for v in vector) ** 0.5
    if norm > 0.0:
        vector = [v / norm for v in vector]
    return vector


def get_embedding(text: str) -> List[float]:
    """Retrieve 384-dimensional dense embedding vector for the input text."""
    global _MODEL_INSTANCE
    
    if not text:
        return [0.0] * 384
        
    try:
        from sentence_transformers import SentenceTransformer
        if _MODEL_INSTANCE is None:
            # Load the lightweight MiniLM transformer model
            _MODEL_INSTANCE = SentenceTransformer(EMBEDDING_MODEL_NAME)
        
        vector = _MODEL_INSTANCE.encode(text, convert_to_numpy=True)
        return vector.tolist()
    except Exception:
        # Graceful fallback to deterministic text hashing vectorizer
        return _get_hash_embedding(text, dimensions=384)
