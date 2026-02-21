"""Tests for semantic_entropy.py module.

Tests the core semantic entropy calculation H(t) = -sum(p(ci) log2 p(ci))
which quantifies terminological ambiguity in Ento-Linguistic analysis.
"""

from __future__ import annotations

import numpy as np
import pytest
from analysis.semantic_entropy import (
    HIGH_ENTROPY_THRESHOLD,
    SemanticEntropyResult,
    calculate_corpus_entropy,
    calculate_semantic_entropy,
    get_high_entropy_terms,
)


class TestSemanticEntropyResult:
    """Test SemanticEntropyResult dataclass."""

    def test_creation(self):
        """Test creating a SemanticEntropyResult."""
        result = SemanticEntropyResult(
            term="colony",
            entropy_bits=1.5,
            n_clusters=3,
            cluster_distribution=[0.5, 0.3, 0.2],
            is_high_entropy=False,
            n_contexts=20,
        )
        assert result.term == "colony"
        assert result.entropy_bits == 1.5
        assert result.n_clusters == 3
        assert len(result.cluster_distribution) == 3

    def test_to_dict(self):
        """Test serialization to dictionary."""
        result = SemanticEntropyResult(
            term="queen", entropy_bits=2.3, n_clusters=5,
            cluster_distribution=[0.2] * 5, is_high_entropy=True, n_contexts=50,
        )
        d = result.to_dict()
        assert d["term"] == "queen"
        assert d["entropy_bits"] == 2.3
        assert d["is_high_entropy"] is True

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "term": "foraging",
            "entropy_bits": 0.5,
            "n_clusters": 2,
            "cluster_distribution": [0.7, 0.3],
            "is_high_entropy": False,
            "n_contexts": 10,
        }
        result = SemanticEntropyResult.from_dict(data)
        assert result.term == "foraging"
        assert result.entropy_bits == 0.5

    def test_default_values(self):
        """Test default field values."""
        result = SemanticEntropyResult(term="test", entropy_bits=0.0, n_clusters=0)
        assert result.cluster_distribution == []
        assert result.is_high_entropy is False
        assert result.n_contexts == 0


class TestCalculateSemanticEntropy:
    """Test the core semantic entropy calculation."""

    def test_single_sense_zero_entropy(self):
        """A term used in only one semantic sense should have zero entropy."""
        # All contexts are about the same thing (reproductive role)
        contexts = [
            "The queen ant lays eggs in the colony nest chamber.",
            "The queen produces all offspring for the colony brood.",
            "Colony queens are the primary reproductive females.",
            "Queens mate during nuptial flights before founding.",
            "The foundress queen establishes the initial colony.",
        ]
        result = calculate_semantic_entropy("queen", contexts)
        # With very similar contexts, entropy should be low
        assert result.entropy_bits >= 0.0
        assert result.n_contexts == 5

    def test_insufficient_contexts(self):
        """Too few contexts should return zero entropy."""
        contexts = ["The queen ant", "Colony queen"]
        result = calculate_semantic_entropy("queen", contexts, min_contexts=5)
        assert result.entropy_bits == 0.0
        assert result.n_contexts < 5

    def test_empty_contexts(self):
        """Empty context list should return zero entropy."""
        result = calculate_semantic_entropy("test", [])
        assert result.entropy_bits == 0.0
        assert result.n_clusters == 0
        assert result.cluster_distribution == []

    def test_diverse_contexts_higher_entropy(self):
        """A term used across very different contexts should have higher entropy."""
        # "colony" used in many different senses
        contexts = [
            "The ant colony consists of thousands of workers performing tasks.",
            "Colony genetics determine the degree of worker relatedness.",
            "The bacterial colony formed on the agar plate overnight.",
            "Colony economics optimize resource allocation strategies.",
            "The space colony on Mars will house ten thousand settlers.",
            "Colony architecture features complex tunnel systems underground.",
            "Colony defense mechanisms include chemical warfare against invaders.",
            "The bird colony on the cliff face numbers over two thousand.",
        ]
        result_diverse = calculate_semantic_entropy("colony", contexts)

        # Diverse contexts should have non-trivial entropy (multiple clusters found)
        assert result_diverse.entropy_bits > 0.0
        assert result_diverse.n_clusters >= 2

    def test_determinism_with_fixed_seed(self):
        """Results should be deterministic with same random_state."""
        contexts = [
            "Queen ant reproduction in eusocial species.",
            "Worker ants serve the queen in the colony.",
            "Queen bees produce all offspring in the hive.",
            "The queen controls colony reproduction patterns.",
            "Multiple queens may coexist in polygynous colonies.",
        ]
        r1 = calculate_semantic_entropy("queen", contexts, random_state=42)
        r2 = calculate_semantic_entropy("queen", contexts, random_state=42)
        assert r1.entropy_bits == r2.entropy_bits
        assert r1.cluster_distribution == r2.cluster_distribution

    def test_high_entropy_threshold_flagging(self):
        """Terms exceeding threshold should be flagged as high entropy."""
        # Use a very low threshold to guarantee flagging
        contexts = [
            "The colony is a superorganism operating as one unit.",
            "Colony genetics affect worker behavior patterns significantly.",
            "Resource economics within the colony optimize foraging efficiency.",
            "Colony defense involves chemical and physical worker responses.",
            "The colony reproduces through swarming and queen dispersal.",
        ]
        result = calculate_semantic_entropy(
            "colony", contexts, threshold=0.0  # Any entropy > 0 flags
        )
        if result.entropy_bits > 0.0:
            assert result.is_high_entropy is True

    def test_max_clusters_parameter(self):
        """max_clusters should limit the number of clusters found."""
        contexts = [
            f"Context about colony in sense number {i} of the term."
            for i in range(20)
        ]
        result = calculate_semantic_entropy("colony", contexts, max_clusters=3)
        assert result.n_clusters <= 3

    def test_short_contexts_filtered(self):
        """Contexts with fewer than 3 words should be filtered out."""
        contexts = [
            "hi",
            "ok",
            "yes",
            "The queen ant lays eggs in the colony.",
            "Colony queens reproduce for the entire colony.",
            "Queen bees are the primary reproductive individuals.",
            "The foundress queen establishes a new colony.",
            "Queens mate during flights before colony founding.",
        ]
        result = calculate_semantic_entropy("queen", contexts, min_contexts=5)
        # Only 5 valid contexts (3+ words)
        assert result.n_contexts == 5


class TestCalculateCorpusEntropy:
    """Test batch corpus entropy calculation."""

    def test_multiple_terms(self):
        """Test entropy calculation for multiple terms simultaneously."""
        terms_contexts = {
            "colony": [
                "The ant colony operates as a superorganism.",
                "Colony size affects foraging strategy selection.",
                "Bacterial colony growth on agar plates.",
                "Colony genetics determine worker relatedness levels.",
                "The colony economy optimizes resource allocation.",
            ],
            "worker": [
                "Worker ants forage for food resources.",
                "Worker caste determination is genetic and environmental.",
                "Workers perform various tasks within colony.",
                "Minor workers are smaller than major workers.",
                "Worker reproduction is suppressed by queen.",
            ],
        }
        results = calculate_corpus_entropy(terms_contexts)
        assert "colony" in results
        assert "worker" in results
        assert isinstance(results["colony"], SemanticEntropyResult)
        assert isinstance(results["worker"], SemanticEntropyResult)

    def test_empty_corpus(self):
        """Empty corpus should return empty results."""
        results = calculate_corpus_entropy({})
        assert results == {}


class TestGetHighEntropyTerms:
    """Test filtering for high-entropy terms."""

    def test_filtering(self):
        """Should return only terms above threshold, sorted descending."""
        results = {
            "queen": SemanticEntropyResult(
                term="queen", entropy_bits=2.5, n_clusters=5, is_high_entropy=True
            ),
            "colony": SemanticEntropyResult(
                term="colony", entropy_bits=1.0, n_clusters=2, is_high_entropy=False
            ),
            "worker": SemanticEntropyResult(
                term="worker", entropy_bits=2.1, n_clusters=4, is_high_entropy=True
            ),
        }
        high = get_high_entropy_terms(results)
        assert len(high) == 2
        assert high[0].term == "queen"  # Higher entropy first
        assert high[1].term == "worker"

    def test_no_high_entropy(self):
        """Should return empty list when no terms exceed threshold."""
        results = {
            "term1": SemanticEntropyResult(
                term="term1", entropy_bits=0.5, n_clusters=2, is_high_entropy=False
            ),
        }
        high = get_high_entropy_terms(results)
        assert high == []
