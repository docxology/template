"""Text similarity algorithms for repetition detection.

Provides multiple similarity methods (Jaccard, TF-cosine, n-gram sequence)
and a hybrid combiner used by the repetition detection module.
"""

from __future__ import annotations

import math
import re
from collections import Counter


def _normalize_for_comparison(text: str) -> str:
    """Normalize text for comparison by removing whitespace variations.

    Args:
        text: Text to normalize

    Returns:
        Normalized text for comparison
    """
    # Remove extra whitespace
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    # Remove common markdown formatting
    normalized = re.sub(r"[#*_`\[\]()]", "", normalized)
    # Remove numbers (often vary in repetitive content)
    normalized = re.sub(r"\d+", "N", normalized)
    return normalized


def _jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity (word overlap)."""
    words1 = set(text1.split())
    words2 = set(text2.split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0

def _tf_cosine_similarity(text1: str, text2: str) -> float:
    """Calculate TF cosine similarity for semantic matching."""
    # Tokenize and count
    words1 = Counter(text1.split())
    words2 = Counter(text2.split())

    if not words1 or not words2:
        return 0.0

    # Get all unique words
    all_words = set(words1.keys()) | set(words2.keys())

    # Calculate TF-IDF vectors (simplified: just TF for now, can be enhanced)
    vec1 = {word: words1.get(word, 0) for word in all_words}
    vec2 = {word: words2.get(word, 0) for word in all_words}

    # Cosine similarity
    dot_product = sum(vec1[word] * vec2[word] for word in all_words)
    norm1 = math.sqrt(sum(val**2 for val in vec1.values()))
    norm2 = math.sqrt(sum(val**2 for val in vec2.values()))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


def _sequence_similarity(text1: str, text2: str) -> float:
    """Calculate sequence-based similarity using n-gram overlap."""

    def get_ngrams(text: str, n: int = 3):
        """Get n-grams from text."""
        words = text.split()
        return [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]

    ngrams1 = set(get_ngrams(text1, 3))
    ngrams2 = set(get_ngrams(text2, 3))

    if not ngrams1 or not ngrams2:
        return 0.0

    intersection = ngrams1 & ngrams2
    union = ngrams1 | ngrams2

    return len(intersection) / len(union) if union else 0.0


def _calculate_similarity(text1: str, text2: str, method: str = "hybrid") -> float:
    """Calculate similarity between two texts using multiple methods.

    Uses a hybrid approach combining Jaccard similarity, TF-IDF cosine similarity,
    and sequence-based similarity for better semantic matching.

    Args:
        text1: First text
        text2: Second text
        method: Similarity method ("jaccard", "tfidf", "hybrid")

    Returns:
        Similarity ratio from 0.0 to 1.0
    """
    if not text1 or not text2:
        return 0.0

    # Normalize texts for comparison
    norm1 = _normalize_for_comparison(text1)
    norm2 = _normalize_for_comparison(text2)

    if method == "jaccard":
        return _jaccard_similarity(norm1, norm2)
    elif method == "tfidf":
        return _tf_cosine_similarity(norm1, norm2)
    else:  # hybrid
        jaccard_sim = _jaccard_similarity(norm1, norm2)
        tfidf_sim = _tf_cosine_similarity(norm1, norm2)
        sequence_sim = _sequence_similarity(norm1, norm2)

        # Weighted combination: favor TF-IDF and sequence similarity
        return 0.3 * jaccard_sim + 0.4 * tfidf_sim + 0.3 * sequence_sim
