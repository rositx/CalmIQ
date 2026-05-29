# guardrail/utils/similarity.py
# Pure-Python mathematical helper for calculating cosine similarity between vectors

import math
from typing import List


def cosine_similarity(vector_a: List[float], vector_b: List[float]) -> float:
    """Calculate the cosine similarity between two float lists."""
    if not vector_a or not vector_b or len(vector_a) != len(vector_b):
        return 0.0
        
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))
    
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
        
    return dot_product / (norm_a * norm_b)
