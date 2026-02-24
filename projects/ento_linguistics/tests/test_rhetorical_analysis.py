"""Tests for analysis/rhetorical_analysis.py module.

Covers: analyze_rhetorical_strategies, identify_narrative_frameworks,
quantify_rhetorical_patterns, score_argumentative_structures,
analyze_narrative_frequency, and private helpers.
"""
from __future__ import annotations

import pytest

from analysis.rhetorical_analysis import (
    analyze_narrative_frequency,
    analyze_rhetorical_strategies,
    identify_narrative_frameworks,
    quantify_rhetorical_patterns,
    score_argumentative_structures,
)
from analysis.discourse_patterns import ArgumentativeStructure


@pytest.fixture
def sample_texts():
    """Texts with varied rhetorical strategies."""
    return [
        "Ant colonies exhibit complex behavior (Smith 2021). Like human cities, ant nests organize labor.",
        "All ant species cooperate. For example, leafcutter ants farm fungi.",
        "Recent progress in understanding ant communication reveals intricate signaling.",
        "The struggle for resources drives adaptation and competition among colonies.",
        "Scientists discover new mechanisms that operate within ant societies.",
    ]


@pytest.fixture
def plain_texts():
    """Texts without strong rhetorical features."""
    return [
        "Temperature readings were recorded daily.",
        "Sample sizes ranged from 50 to 200.",
    ]


class TestAnalyzeRhetoricalStrategies:
    """Test analyze_rhetorical_strategies function."""

    def test_empty_texts(self):
        """Test with empty text list."""
        result = analyze_rhetorical_strategies([])
        assert "authority" in result
        assert "analogy" in result
        assert "generalization" in result
        assert "anecdotal" in result
        for strategy in result.values():
            assert strategy["frequency"] == 0

    def test_authority_detection(self):
        """Test detection of authority citations."""
        texts = ["Ant behavior is complex (Jones 2022)."]
        result = analyze_rhetorical_strategies(texts)
        assert result["authority"]["frequency"] >= 1

    def test_analogy_detection(self):
        """Test detection of analogies involving ants."""
        texts = ["Colonies function like ant cities in many respects."]
        result = analyze_rhetorical_strategies(texts)
        assert result["analogy"]["frequency"] >= 1

    def test_generalization_detection(self):
        """Test detection of generalizations."""
        texts = ["All ant species exhibit some form of cooperation."]
        result = analyze_rhetorical_strategies(texts)
        assert result["generalization"]["frequency"] >= 1

    def test_anecdotal_detection(self):
        """Test detection of anecdotal evidence markers."""
        texts = ["For example, leafcutter ants maintain fungal gardens."]
        result = analyze_rhetorical_strategies(texts)
        assert result["anecdotal"]["frequency"] >= 1

    def test_multiple_texts(self, sample_texts):
        """Test with multiple texts accumulates counts."""
        result = analyze_rhetorical_strategies(sample_texts)
        total = sum(s["frequency"] for s in result.values())
        assert total > 0

    def test_examples_limited(self):
        """Test that examples are limited per text."""
        texts = ["(A 2020) (B 2021) (C 2022) (D 2023)"]
        result = analyze_rhetorical_strategies(texts)
        assert len(result["authority"]["examples"]) <= 2


class TestIdentifyNarrativeFrameworks:
    """Test identify_narrative_frameworks function."""

    def test_empty_texts(self):
        """Test with empty list."""
        result = identify_narrative_frameworks([])
        assert result == {
            "progress_narrative": [],
            "conflict_narrative": [],
            "discovery_narrative": [],
            "complexity_narrative": [],
        }

    def test_progress_narrative(self):
        """Test progress narrative detection."""
        texts = ["The advance of colony research shows great improvement."]
        result = identify_narrative_frameworks(texts)
        assert len(result["progress_narrative"]) >= 1

    def test_conflict_narrative(self):
        """Test conflict narrative detection."""
        texts = ["The struggle for resources drives competition among ant colonies."]
        result = identify_narrative_frameworks(texts)
        assert len(result["conflict_narrative"]) >= 1

    def test_discovery_narrative(self):
        """Test discovery narrative detection."""
        texts = ["Researchers discover that ants reveal hidden communication patterns."]
        result = identify_narrative_frameworks(texts)
        assert len(result["discovery_narrative"]) >= 1

    def test_complexity_narrative(self):
        """Test complexity narrative detection."""
        texts = ["Ant colonies exhibit complex and sophisticated organization."]
        result = identify_narrative_frameworks(texts)
        assert len(result["complexity_narrative"]) >= 1

    def test_text_truncated_in_examples(self):
        """Test that examples are truncated to 100 chars + '...'."""
        long_text = "The advance of colony research " * 10
        result = identify_narrative_frameworks([long_text])
        for example in result["progress_narrative"]:
            assert example.endswith("...")
            assert len(example) <= 104  # 100 chars + "..."


class TestQuantifyRhetoricalPatterns:
    """Test quantify_rhetorical_patterns function."""

    def test_empty_texts(self):
        """Test with empty list."""
        result = quantify_rhetorical_patterns([])
        for pattern in result.values():
            assert pattern["effectiveness_score"] == 0

    def test_returns_quantified_data(self, sample_texts):
        """Test that quantified patterns have expected keys."""
        result = quantify_rhetorical_patterns(sample_texts)
        for pattern_name, data in result.items():
            assert "total_occurrences" in data
            assert "text_coverage" in data
            assert "effectiveness_score" in data
            assert "persuasiveness_rating" in data
            assert "context_examples" in data

    def test_effectiveness_bounded(self, sample_texts):
        """Test effectiveness scores are between 0 and 1."""
        result = quantify_rhetorical_patterns(sample_texts)
        for data in result.values():
            assert 0 <= data["effectiveness_score"] <= 1

    def test_persuasiveness_bounded(self, sample_texts):
        """Test persuasiveness ratings are between 0 and 1."""
        result = quantify_rhetorical_patterns(sample_texts)
        for data in result.values():
            assert 0 <= data["persuasiveness_rating"] <= 1


class TestScoreArgumentativeStructures:
    """Test score_argumentative_structures function."""

    def test_empty_structures(self):
        """Test with no structures."""
        result = score_argumentative_structures([], ["some text"])
        assert result == {}

    def test_single_structure(self):
        """Test scoring a single structure."""
        structure = ArgumentativeStructure(
            claim="Therefore ants cooperate in foraging activities.",
            evidence=["Research shows colony-level coordination of foraging behavior."],
            warrant="Because cooperation improves colony fitness over time.",
            qualification="However variation exists among species.",
        )
        result = score_argumentative_structures([structure], ["text"])
        assert "structure_0" in result
        scored = result["structure_0"]
        assert "claim_strength" in scored
        assert "evidence_quality" in scored
        assert "reasoning_coherence" in scored
        assert "overall_strength" in scored
        assert "confidence_score" in scored

    def test_scores_bounded(self):
        """Test all scores are between 0 and 1."""
        structure = ArgumentativeStructure(
            claim="Therefore the hypothesis is supported by data.",
            evidence=["The data clearly support this observation."],
            warrant="Because the evidence aligns with predictions.",
        )
        result = score_argumentative_structures([structure], ["text"])
        scored = result["structure_0"]
        assert 0 <= scored["claim_strength"] <= 1
        assert 0 <= scored["evidence_quality"] <= 1
        assert 0 <= scored["reasoning_coherence"] <= 1
        assert 0 <= scored["overall_strength"] <= 1
        assert 0 <= scored["confidence_score"] <= 1

    def test_empty_claim_lower_strength(self):
        """Test that empty claim yields lower strength."""
        weak = ArgumentativeStructure(claim="", evidence=[], warrant="")
        strong = ArgumentativeStructure(
            claim="Therefore this result is significant in context.",
            evidence=["The study data confirms the prediction."],
            warrant="Because the model predicts this outcome precisely.",
        )
        weak_result = score_argumentative_structures([weak], ["text"])
        strong_result = score_argumentative_structures([strong], ["text"])
        assert weak_result["structure_0"]["overall_strength"] < strong_result["structure_0"]["overall_strength"]

    def test_multiple_structures(self):
        """Test scoring multiple structures."""
        structures = [
            ArgumentativeStructure(claim="Thus ants cooperate."),
            ArgumentativeStructure(claim="Hence colonies thrive."),
        ]
        result = score_argumentative_structures(structures, ["text"])
        assert "structure_0" in result
        assert "structure_1" in result


class TestAnalyzeNarrativeFrequency:
    """Test analyze_narrative_frequency function."""

    def test_empty_texts(self):
        """Test with empty list."""
        result = analyze_narrative_frequency([])
        for framework in result.values():
            assert framework["frequency"] == 0
            assert framework["coverage_percentage"] == 0

    def test_returns_expected_keys(self, sample_texts):
        """Test that output has expected structure."""
        result = analyze_narrative_frequency(sample_texts)
        for framework_name, data in result.items():
            assert "frequency" in data
            assert "coverage_percentage" in data
            assert "average_text_length" in data
            assert "unique_phrase_count" in data
            assert "examples" in data
            assert "consistency_score" in data

    def test_coverage_bounded(self, sample_texts):
        """Test coverage percentage is between 0 and 100."""
        result = analyze_narrative_frequency(sample_texts)
        for data in result.values():
            assert 0 <= data["coverage_percentage"] <= 100

    def test_examples_limited(self):
        """Test examples are limited to 3."""
        texts = [
            f"The advance of research {i} shows progress." for i in range(10)
        ]
        result = analyze_narrative_frequency(texts)
        for data in result.values():
            assert len(data["examples"]) <= 3

    def test_consistency_score_bounded(self, sample_texts):
        """Test consistency scores are between 0 and 1."""
        result = analyze_narrative_frequency(sample_texts)
        for data in result.values():
            assert 0 <= data["consistency_score"] <= 1
