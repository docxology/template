"""CACE framework scoring for Ento-Linguistic analysis.

Implements the four-dimension CACE scoring system:
- **C**larity: Inverse of semantic entropy (low ambiguity = high clarity)
- **A**ppropriateness: Penalizes anthropomorphic terms (queen, slave, worker, etc.)
- **C**onsistency: Low variance in TF-IDF context vectors = high consistency
- **E**volvability: Scale-invariance across biological levels (gene/organism/colony)

Each dimension score is bounded [0, 1]. Aggregate = mean of four dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

__all__ = [
    "CACEScore",
    "ANTHROPOMORPHIC_TERMS",
    "SCALE_LEVELS",
    "score_clarity",
    "score_appropriateness",
    "score_consistency",
    "score_evolvability",
    "evaluate_term_cace",
    "compare_terms_cace",
]


@dataclass
class CACEScore:
    """CACE evaluation result for a single term.

    Attributes:
        term: The term being evaluated
        clarity: 1 - (H / H_max), where H is semantic entropy
        appropriateness: Penalty for anthropomorphic connotations
        consistency: Low variance of context vectors
        evolvability: Scale-invariance across biological levels
        aggregate: Mean of four dimension scores
    """

    term: str
    clarity: float
    appropriateness: float
    consistency: float
    evolvability: float
    aggregate: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "term": self.term,
            "clarity": self.clarity,
            "appropriateness": self.appropriateness,
            "consistency": self.consistency,
            "evolvability": self.evolvability,
            "aggregate": self.aggregate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CACEScore":
        """Create from dictionary."""
        return cls(**data)


# Anthropomorphic terms that project human social structures onto insect biology.
# These carry implicit framing assumptions that may distort scientific understanding.
ANTHROPOMORPHIC_TERMS: Set[str] = {
    "queen",
    "king",
    "slave",
    "worker",
    "soldier",
    "nurse",
    "princess",
    "maiden",
    "servant",
    "master",
    "parasite",
    "host",
    "altruist",
    "selfish",
    "lazy",
    "industrious",
    "ruler",
    "subject",
    "peasant",
    "tyrant",
}

# Biological scale levels for evolvability assessment
SCALE_LEVELS = {"gene", "cell", "organism", "colony", "population", "ecosystem"}

# Maximum theoretical entropy for clarity normalization.
# log2(10) ≈ 3.32 bits corresponds to 10 equiprobable semantic senses.
DEFAULT_MAX_ENTROPY = 3.32

# Anthropomorphic penalty weights for appropriateness scoring.
# Base penalty applied when any word overlaps with ANTHROPOMORPHIC_TERMS.
DEFAULT_ANTHROPOMORPHIC_BASE_PENALTY = 0.4
# Per-word penalty for each overlapping anthropomorphic word.
DEFAULT_ANTHROPOMORPHIC_WORD_PENALTY = 0.1
# Per-domain penalty for cross-domain anthropomorphic terms.
DEFAULT_ANTHROPOMORPHIC_DOMAIN_PENALTY = 0.05

# Divisor for domain-based evolvability scoring.
# A term spanning 3+ domains reaches maximum domain_score (1.0).
DEFAULT_SCALE_DIVISOR = 3.0


def score_clarity(
    semantic_entropy: float,
    max_entropy: float = DEFAULT_MAX_ENTROPY,
) -> float:
    """Score term clarity as inverse of semantic entropy.

    Clarity = 1 - (H / H_max), clamped to [0, 1].
    H_max defaults to log2(10) = 3.32 bits (10 equiprobable senses).

    Args:
        semantic_entropy: Shannon entropy in bits for the term
        max_entropy: Maximum possible entropy (default: log2(10))

    Returns:
        Clarity score in [0, 1] (1 = perfectly clear, 0 = maximally ambiguous)
    """
    if max_entropy <= 0:
        return 1.0
    clarity = 1.0 - (semantic_entropy / max_entropy)
    return float(max(0.0, min(1.0, clarity)))


def score_appropriateness(
    term: str,
    domains: Optional[List[str]] = None,
    anthropomorphic_set: Optional[Set[str]] = None,
) -> float:
    """Score term appropriateness by penalizing anthropomorphic language.

    Terms in the anthropomorphic set receive a penalty. The penalty is
    proportional to how many domains the anthropomorphic term spans,
    as cross-domain anthropomorphism compounds conceptual confusion.

    Args:
        term: The term to evaluate
        domains: List of Ento-Linguistic domains the term belongs to
        anthropomorphic_set: Override set of anthropomorphic terms

    Returns:
        Appropriateness score in [0, 1] (1 = fully appropriate, 0 = highly anthropomorphic)
    """
    if anthropomorphic_set is None:
        anthropomorphic_set = ANTHROPOMORPHIC_TERMS

    term_lower = term.lower().strip()
    domains = domains or []

    # Check if any word in the term is anthropomorphic
    term_words = set(term_lower.replace("-", " ").replace("_", " ").split())
    anthropomorphic_overlap = term_words & anthropomorphic_set

    if not anthropomorphic_overlap:
        return 1.0

    # Base penalty for being anthropomorphic
    base_penalty = DEFAULT_ANTHROPOMORPHIC_BASE_PENALTY

    # Additional penalty per overlapping anthropomorphic word
    word_penalty = DEFAULT_ANTHROPOMORPHIC_WORD_PENALTY * len(anthropomorphic_overlap)

    # Cross-domain penalty: more domains = more confusion potential
    domain_penalty = DEFAULT_ANTHROPOMORPHIC_DOMAIN_PENALTY * max(0, len(domains) - 1)

    score = 1.0 - base_penalty - word_penalty - domain_penalty
    return float(max(0.0, min(1.0, score)))


def score_consistency(
    term: str,
    contexts: List[str],
    min_contexts: int = 3,
) -> float:
    """Score term consistency via TF-IDF context vector variance.

    Low variance across context vectors = term used consistently.
    High variance = term meaning shifts across contexts.

    Args:
        term: The term to evaluate
        contexts: Usage contexts for the term
        min_contexts: Minimum contexts for meaningful analysis

    Returns:
        Consistency score in [0, 1] (1 = highly consistent, 0 = highly variable)
    """
    valid_contexts = [c.strip() for c in contexts if len(c.strip().split()) >= 3]

    if len(valid_contexts) < min_contexts:
        return 0.5  # Neutral score for insufficient data

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            min_df=1,
            max_features=500,
        )
        X = vectorizer.fit_transform(valid_contexts)

        # Calculate pairwise cosine similarity variance
        # Low variance = consistent usage
        X_dense = X.toarray()
        norms = np.linalg.norm(X_dense, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        X_normed = X_dense / norms

        # Mean pairwise cosine similarity
        similarity_matrix = X_normed @ X_normed.T
        n = similarity_matrix.shape[0]

        # Extract upper triangle (exclude diagonal)
        upper_indices = np.triu_indices(n, k=1)
        pairwise_similarities = similarity_matrix[upper_indices]

        if len(pairwise_similarities) == 0:
            return 0.5

        # Mean similarity maps to consistency: high mean sim = consistent
        mean_similarity = float(np.mean(pairwise_similarities))

        # Clamp to [0, 1]
        return float(max(0.0, min(1.0, mean_similarity)))

    except Exception:
        return 0.5  # Neutral score on error


def score_evolvability(
    term: str,
    domains: Optional[List[str]] = None,
    contexts: Optional[List[str]] = None,
) -> float:
    """Score term evolvability (scale-invariance across biological levels).

    A term that works at gene, organism, AND colony levels is more evolvable
    than one locked to a single scale. Also checks if contexts reference
    multiple scale levels.

    Args:
        term: The term to evaluate
        domains: Ento-Linguistic domains the term belongs to
        contexts: Usage contexts for the term

    Returns:
        Evolvability score in [0, 1] (1 = highly scale-invariant)
    """
    domains = domains or []
    contexts = contexts or []

    # Base score from domain breadth (more domains = more generalizable)
    n_domains = len(domains)
    domain_score = min(1.0, n_domains / DEFAULT_SCALE_DIVISOR)  # Caps at 3+ domains

    # Context-based scale detection
    scale_count = 0
    context_text = " ".join(contexts).lower()
    for level in SCALE_LEVELS:
        if level in context_text:
            scale_count += 1

    # Scale breadth score
    scale_score = min(1.0, scale_count / DEFAULT_SCALE_DIVISOR) if contexts else 0.0

    # Weighted combination
    if contexts:
        score = 0.5 * domain_score + 0.5 * scale_score
    else:
        score = domain_score

    return float(max(0.0, min(1.0, score)))


def evaluate_term_cace(
    term: str,
    semantic_entropy: float = 0.0,
    contexts: Optional[List[str]] = None,
    domains: Optional[List[str]] = None,
    max_entropy: float = DEFAULT_MAX_ENTROPY,
) -> CACEScore:
    """Evaluate a term across all four CACE dimensions.

    Args:
        term: The term to evaluate
        semantic_entropy: Pre-computed Shannon entropy in bits
        contexts: Usage contexts for consistency scoring
        domains: Ento-Linguistic domains for appropriateness/evolvability
        max_entropy: Maximum entropy for clarity normalization

    Returns:
        CACEScore with all four dimensions and aggregate
    """
    contexts = contexts or []
    domains = domains or []

    c = score_clarity(semantic_entropy, max_entropy)
    a = score_appropriateness(term, domains)
    co = score_consistency(term, contexts)
    e = score_evolvability(term, domains, contexts)

    aggregate = float(np.mean([c, a, co, e]))

    return CACEScore(
        term=term,
        clarity=c,
        appropriateness=a,
        consistency=co,
        evolvability=e,
        aggregate=aggregate,
    )


def compare_terms_cace(
    terms_data: List[Dict[str, Any]],
    max_entropy: float = DEFAULT_MAX_ENTROPY,
) -> List[CACEScore]:
    """Evaluate and compare multiple terms using CACE framework.

    Args:
        terms_data: List of dicts with keys: term, semantic_entropy, contexts, domains
        max_entropy: Maximum entropy for normalization

    Returns:
        List of CACEScores sorted by aggregate (highest first)
    """
    scores = []
    for td in terms_data:
        score = evaluate_term_cace(
            term=td["term"],
            semantic_entropy=td.get("semantic_entropy", 0.0),
            contexts=td.get("contexts", []),
            domains=td.get("domains", []),
            max_entropy=max_entropy,
        )
        scores.append(score)

    return sorted(scores, key=lambda s: s.aggregate, reverse=True)
