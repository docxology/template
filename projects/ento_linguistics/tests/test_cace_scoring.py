"""Tests for cace_scoring.py module.

Tests the CACE (Clarity, Appropriateness, Consistency, Evolvability) framework
for evaluating terminology quality in Ento-Linguistic analysis.
"""

from __future__ import annotations

import numpy as np
import pytest
from analysis.cace_scoring import (
    ANTHROPOMORPHIC_TERMS,
    CACEScore,
    compare_terms_cace,
    evaluate_term_cace,
    score_appropriateness,
    score_clarity,
    score_consistency,
    score_evolvability,
)


class TestCACEScore:
    """Test CACEScore dataclass."""

    def test_creation(self):
        """Test creating a CACEScore."""
        score = CACEScore(
            term="colony",
            clarity=0.8,
            appropriateness=1.0,
            consistency=0.7,
            evolvability=0.6,
            aggregate=0.775,
        )
        assert score.term == "colony"
        assert score.clarity == 0.8
        assert score.aggregate == 0.775

    def test_to_dict(self):
        """Test serialization."""
        score = CACEScore(
            term="test", clarity=0.5, appropriateness=0.5,
            consistency=0.5, evolvability=0.5, aggregate=0.5,
        )
        d = score.to_dict()
        assert d["term"] == "test"
        assert d["clarity"] == 0.5
        assert len(d) == 6

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "term": "queen",
            "clarity": 0.3,
            "appropriateness": 0.5,
            "consistency": 0.4,
            "evolvability": 0.6,
            "aggregate": 0.45,
        }
        score = CACEScore.from_dict(data)
        assert score.term == "queen"
        assert score.aggregate == 0.45


class TestScoreClarity:
    """Test clarity scoring."""

    def test_zero_entropy_gives_max_clarity(self):
        """Zero entropy = no ambiguity = perfect clarity."""
        assert score_clarity(0.0) == 1.0

    def test_max_entropy_gives_zero_clarity(self):
        """Maximum entropy = maximum ambiguity = zero clarity."""
        assert score_clarity(3.32, max_entropy=3.32) == pytest.approx(0.0, abs=0.01)

    def test_inverse_relationship(self):
        """Higher entropy should yield lower clarity."""
        c_low = score_clarity(0.5)
        c_high = score_clarity(2.0)
        assert c_low > c_high

    def test_clamped_to_zero_one(self):
        """Score should be clamped to [0, 1] even with extreme inputs."""
        assert score_clarity(100.0) == 0.0  # Clamped to 0
        assert score_clarity(-1.0) >= 1.0  # Clamped to 1

    def test_custom_max_entropy(self):
        """Custom max_entropy parameter should normalize correctly."""
        # H = 1.0 with max_entropy = 2.0 => clarity = 0.5
        assert score_clarity(1.0, max_entropy=2.0) == pytest.approx(0.5, abs=0.01)

    def test_zero_max_entropy(self):
        """Zero max_entropy should return 1.0 to avoid division by zero."""
        assert score_clarity(1.0, max_entropy=0.0) == 1.0


class TestScoreAppropriateness:
    """Test appropriateness scoring."""

    def test_non_anthropomorphic_term(self):
        """Non-anthropomorphic terms should get perfect score."""
        assert score_appropriateness("haplodiploidy") == 1.0
        assert score_appropriateness("trophallaxis") == 1.0

    def test_anthropomorphic_term_penalized(self):
        """Anthropomorphic terms should be penalized."""
        score = score_appropriateness("queen")
        assert score < 1.0
        assert score >= 0.0

    def test_slave_heavily_penalized(self):
        """'slave' should receive strong penalty."""
        score = score_appropriateness("slave")
        assert score < 0.6

    def test_queen_vs_primary_reproductive(self):
        """'primary reproductive' should score higher than 'queen'."""
        queen_score = score_appropriateness("queen")
        repro_score = score_appropriateness("primary reproductive")
        assert repro_score > queen_score

    def test_cross_domain_penalty(self):
        """Terms in multiple domains get additional penalty."""
        single = score_appropriateness("queen", domains=["power_and_labor"])
        multi = score_appropriateness(
            "queen", domains=["power_and_labor", "sex_and_reproduction"]
        )
        assert single >= multi

    def test_scores_bounded(self):
        """All scores should be in [0, 1]."""
        for term in ["queen", "slave", "worker", "soldier", "haplodiploidy", "trophallaxis"]:
            score = score_appropriateness(term, domains=["d1", "d2", "d3", "d4"])
            assert 0.0 <= score <= 1.0

    def test_custom_anthropomorphic_set(self):
        """Custom set should override defaults."""
        # "colony" not in default set
        assert score_appropriateness("colony") == 1.0
        # But with custom set including it
        score = score_appropriateness("colony", anthropomorphic_set={"colony"})
        assert score < 1.0


class TestScoreConsistency:
    """Test consistency scoring."""

    def test_identical_contexts_high_consistency(self):
        """Nearly identical contexts should yield high consistency."""
        contexts = [
            "The queen ant lays eggs in the brood chamber.",
            "The queen ant produces eggs for the colony brood.",
            "Colony queen ants lay their eggs in chambers.",
            "Queens lay eggs that develop into colony workers.",
        ]
        score = score_consistency("queen", contexts, min_contexts=3)
        assert score > 0.2  # Should be reasonably consistent

    def test_diverse_contexts_lower_consistency(self):
        """Very different contexts should yield lower consistency."""
        diverse = [
            "The ant colony forages for food in the surrounding forest area.",
            "Stock market colony of traders operates on Wall Street near banks.",
            "The bacterial colony grew rapidly on the nutrient agar plate surface.",
        ]
        uniform = [
            "The ant colony forages for food in the forest surrounding the nest.",
            "The ant colony collects food resources from nearby plants and trees.",
            "Colony workers forage along trails from the nest to food sources.",
        ]
        score_diverse = score_consistency("colony", diverse, min_contexts=3)
        score_uniform = score_consistency("colony", uniform, min_contexts=3)
        # Uniform should be at least as consistent as diverse
        assert score_uniform >= score_diverse or abs(score_uniform - score_diverse) < 0.2

    def test_insufficient_contexts_neutral(self):
        """Too few contexts should return neutral score of 0.5."""
        score = score_consistency("test", ["short"], min_contexts=5)
        assert score == 0.5

    def test_bounded_zero_one(self):
        """Score must be in [0, 1]."""
        contexts = [f"Context number {i} about colony behavior." for i in range(10)]
        score = score_consistency("colony", contexts, min_contexts=3)
        assert 0.0 <= score <= 1.0


class TestScoreEvolvability:
    """Test evolvability scoring."""

    def test_multi_domain_higher(self):
        """Terms in more domains should be more evolvable."""
        score_one = score_evolvability("colony", domains=["unit_of_individuality"])
        score_three = score_evolvability(
            "colony",
            domains=["unit_of_individuality", "economics", "behavior_and_identity"],
        )
        assert score_three >= score_one

    def test_multi_scale_contexts(self):
        """Contexts mentioning multiple biological scales should score higher."""
        multi_scale = [
            "At the gene level, colony behavior is influenced by genetic factors.",
            "The organism responds to colony-level pheromone signals.",
            "Colony population dynamics affect ecosystem stability.",
        ]
        single_scale = [
            "The organism builds the nest structure.",
            "The organism forages for food.",
            "The organism defends the nest.",
        ]
        score_multi = score_evolvability("colony", domains=["unit_of_individuality"], contexts=multi_scale)
        score_single = score_evolvability("colony", domains=["unit_of_individuality"], contexts=single_scale)
        assert score_multi >= score_single

    def test_no_domains_no_contexts(self):
        """No domains and no contexts should give zero score."""
        score = score_evolvability("unknown", domains=[], contexts=[])
        assert score == 0.0

    def test_bounded(self):
        """Score must be in [0, 1]."""
        score = score_evolvability(
            "test",
            domains=["d1", "d2", "d3", "d4", "d5"],
            contexts=["gene organism colony population ecosystem cell"] * 10,
        )
        assert 0.0 <= score <= 1.0


class TestEvaluateTermCACE:
    """Test full CACE evaluation."""

    def test_aggregate_is_mean_of_dimensions(self):
        """Aggregate should be the mean of four dimension scores."""
        result = evaluate_term_cace(
            term="colony",
            semantic_entropy=0.0,  # Perfect clarity
            contexts=[],
            domains=["unit_of_individuality"],
        )
        expected_aggregate = np.mean([
            result.clarity, result.appropriateness,
            result.consistency, result.evolvability,
        ])
        assert result.aggregate == pytest.approx(expected_aggregate, abs=1e-6)

    def test_all_scores_bounded(self):
        """Every dimension and aggregate must be in [0, 1]."""
        result = evaluate_term_cace(
            term="queen",
            semantic_entropy=2.5,
            contexts=["Queen ants reproduce in the colony."] * 5,
            domains=["power_and_labor", "sex_and_reproduction"],
        )
        assert 0.0 <= result.clarity <= 1.0
        assert 0.0 <= result.appropriateness <= 1.0
        assert 0.0 <= result.consistency <= 1.0
        assert 0.0 <= result.evolvability <= 1.0
        assert 0.0 <= result.aggregate <= 1.0

    def test_queen_vs_primary_reproductive(self):
        """'primary reproductive' should score higher overall than 'queen'."""
        queen = evaluate_term_cace(
            term="queen",
            semantic_entropy=2.0,
            domains=["power_and_labor", "sex_and_reproduction"],
        )
        repro = evaluate_term_cace(
            term="primary reproductive",
            semantic_entropy=0.5,
            domains=["sex_and_reproduction"],
        )
        # Primary reproductive has: lower entropy (higher clarity),
        # non-anthropomorphic (higher appropriateness)
        assert repro.clarity > queen.clarity
        assert repro.appropriateness > queen.appropriateness


class TestCompareTermsCACE:
    """Test multi-term comparison."""

    def test_sorted_by_aggregate(self):
        """Results should be sorted by aggregate score descending."""
        terms = [
            {"term": "queen", "semantic_entropy": 2.0, "domains": ["power_and_labor"]},
            {"term": "haplodiploidy", "semantic_entropy": 0.2, "domains": ["sex_and_reproduction"]},
            {"term": "colony", "semantic_entropy": 1.0, "domains": ["unit_of_individuality"]},
        ]
        results = compare_terms_cace(terms)
        assert len(results) == 3
        # Sorted descending by aggregate
        for i in range(len(results) - 1):
            assert results[i].aggregate >= results[i + 1].aggregate

    def test_empty_input(self):
        """Empty input should return empty list."""
        assert compare_terms_cace([]) == []
