"""Tests for analysis/persuasive_analysis.py module.

Covers: analyze_persuasive_techniques, measure_persuasive_effectiveness,
analyze_term_usage_context, track_conceptual_shifts, quantify_framing_effects,
and private helpers.
"""
from __future__ import annotations

import pytest

from analysis.persuasive_analysis import (
    analyze_persuasive_techniques,
    analyze_term_usage_context,
    measure_persuasive_effectiveness,
    quantify_framing_effects,
    track_conceptual_shifts,
)


@pytest.fixture
def sample_texts():
    """Texts with various persuasive features."""
    return [
        "How do ants decide where to forage? Like a factory, the colony system operates efficiently.",
        "Ant colonies process 50% more food (Smith 2021). Workers choose tasks adaptively.",
        "The mechanism of pheromone signaling determines foraging behavior as a result.",
    ]


@pytest.fixture
def temporal_texts():
    """Texts representing different time periods."""
    return [
        "Ants decide to cooperate. Workers choose their tasks (Early 2010).",
        "Colony mechanism operates efficiently. The system controls behavior.",
        "New studies discover complex mechanisms that function in ant societies.",
    ]


class TestAnalyzePersuasiveTechniques:
    """Test analyze_persuasive_techniques function."""

    def test_empty_texts(self):
        """Test with empty list."""
        result = analyze_persuasive_techniques([])
        assert "rhetorical_questions" in result
        assert "metaphorical_language" in result
        assert "quantitative_emphasis" in result
        assert "authoritative_citations" in result
        for technique in result.values():
            assert technique["count"] == 0

    def test_rhetorical_questions(self):
        """Test detection of rhetorical questions."""
        texts = ["how do ants organize? what drives cooperation?"]
        result = analyze_persuasive_techniques(texts)
        assert result["rhetorical_questions"]["count"] >= 1

    def test_metaphorical_language(self):
        """Test detection of metaphorical language."""
        texts = ["Ant colonies function like a city. Similar to human organizations."]
        result = analyze_persuasive_techniques(texts)
        assert result["metaphorical_language"]["count"] >= 1

    def test_quantitative_emphasis(self):
        """Test detection of quantitative emphasis."""
        texts = ["Colonies process 50% more food. Workers are 3.5 times faster."]
        result = analyze_persuasive_techniques(texts)
        assert result["quantitative_emphasis"]["count"] >= 1

    def test_authoritative_citations(self):
        """Test detection of authoritative citations."""
        texts = ["Ant colonies exhibit cooperation (Smith 2021) and division of labor (Jones 2022)."]
        result = analyze_persuasive_techniques(texts)
        assert result["authoritative_citations"]["count"] >= 2

    def test_multiple_texts_accumulate(self, sample_texts):
        """Test that counts accumulate across texts."""
        result = analyze_persuasive_techniques(sample_texts)
        total = sum(t["count"] for t in result.values())
        assert total > 0

    def test_examples_collected(self):
        """Test that examples are collected for rhetorical questions."""
        texts = ["how do ants forage? what drives colony behavior?"]
        result = analyze_persuasive_techniques(texts)
        assert len(result["rhetorical_questions"]["examples"]) >= 1


class TestMeasurePersuasiveEffectiveness:
    """Test measure_persuasive_effectiveness function."""

    def test_empty_texts(self):
        """Test with empty list."""
        result = measure_persuasive_effectiveness([])
        for technique in result.values():
            assert "impact_score" in technique
            assert "effectiveness_rating" in technique

    def test_returns_expected_keys(self, sample_texts):
        """Test output has expected structure."""
        result = measure_persuasive_effectiveness(sample_texts)
        for technique_name, data in result.items():
            assert "usage_frequency" in data
            assert "context_relevance" in data
            assert "impact_score" in data
            assert "effectiveness_rating" in data
            assert "success_examples" in data

    def test_impact_score_bounded(self, sample_texts):
        """Test impact scores are between 0 and 1."""
        result = measure_persuasive_effectiveness(sample_texts)
        for data in result.values():
            assert 0 <= data["impact_score"] <= 1

    def test_effectiveness_rating_valid(self, sample_texts):
        """Test effectiveness rating is a valid category."""
        valid_ratings = {
            "highly_effective",
            "effective",
            "moderately_effective",
            "minimally_effective",
            "ineffective",
        }
        result = measure_persuasive_effectiveness(sample_texts)
        for data in result.values():
            assert data["effectiveness_rating"] in valid_ratings


class TestAnalyzeTermUsageContext:
    """Test analyze_term_usage_context function."""

    def test_empty_inputs(self):
        """Test with empty terms and texts."""
        result = analyze_term_usage_context([], [])
        assert result == {}

    def test_term_not_found(self):
        """Test with term not present in texts."""
        result = analyze_term_usage_context(["quantum"], ["Ants forage for food."])
        assert result == {}

    def test_term_found(self):
        """Test with term present in texts."""
        texts = [
            "The colony organizes foraging behavior. However colony size matters.",
            "Because the colony adapts to conditions.",
        ]
        result = analyze_term_usage_context(["colony"], texts)
        assert "colony" in result
        data = result["colony"]
        assert data["total_occurrences"] >= 2
        assert "context_types" in data
        assert "context_diversity" in data
        assert "position_distribution" in data

    def test_context_types_classified(self):
        """Test that context types are properly classified."""
        texts = [
            "However colony behavior changes. Because colony fitness matters. "
            "For example colony size varies. Therefore colony success depends on this."
        ]
        result = analyze_term_usage_context(["colony"], texts)
        assert "colony" in result
        types = result["colony"]["context_types"]
        assert len(types) > 0

    def test_position_distribution(self):
        """Test position distribution has expected keys."""
        texts = ["Colony behavior is complex. " * 10]
        result = analyze_term_usage_context(["colony"], texts)
        if "colony" in result:
            dist = result["colony"]["position_distribution"]
            assert "early" in dist
            assert "middle" in dist
            assert "late" in dist

    def test_usage_consistency_bounded(self):
        """Test usage consistency is between 0 and 1."""
        texts = ["The colony forages. However colony adapts. Because colony grows."]
        result = analyze_term_usage_context(["colony"], texts)
        if "colony" in result:
            assert 0 <= result["colony"]["usage_consistency"] <= 1

    def test_examples_limited(self):
        """Test context examples are limited to 5."""
        texts = [". ".join([f"Colony observation {i}" for i in range(20)])]
        result = analyze_term_usage_context(["colony"], texts)
        if "colony" in result:
            assert len(result["colony"]["context_examples"]) <= 5

    def test_multiple_terms(self):
        """Test analyzing multiple terms."""
        texts = ["The colony forages for food. Workers collect nectar."]
        result = analyze_term_usage_context(["colony", "workers"], texts)
        assert "colony" in result
        assert "workers" in result


class TestTrackConceptualShifts:
    """Test track_conceptual_shifts function."""

    def test_single_text_no_shifts(self):
        """Test with single text produces no shifts."""
        result = track_conceptual_shifts(["Some text about ants."])
        assert result == {}

    def test_two_periods(self, temporal_texts):
        """Test with texts across two periods."""
        periods = ["period_0", "period_0", "period_1"]
        result = track_conceptual_shifts(temporal_texts[:3], time_periods=periods)
        assert "period_0_to_period_1" in result

    def test_auto_generated_periods(self, temporal_texts):
        """Test that periods are auto-generated when not provided."""
        result = track_conceptual_shifts(temporal_texts)
        # Should have period_0_to_period_1 and period_1_to_period_2
        assert len(result) == len(temporal_texts) - 1

    def test_mismatched_periods_raises(self):
        """Test that mismatched periods raises ValueError."""
        with pytest.raises(ValueError, match="same length"):
            track_conceptual_shifts(["text1", "text2"], time_periods=["p1"])

    def test_shift_structure(self, temporal_texts):
        """Test that shift results have expected structure."""
        result = track_conceptual_shifts(temporal_texts)
        for shift_key, shift_data in result.items():
            assert "pattern_shifts" in shift_data
            assert "overall_shift_intensity" in shift_data
            assert "significant_shifts" in shift_data

    def test_pattern_shift_directions(self):
        """Test shift direction values."""
        texts = [
            "Authority citations (Smith 2020) show ant behavior.",
            "Simple observation of ants.",
        ]
        result = track_conceptual_shifts(texts)
        for shift_data in result.values():
            for pattern_shift in shift_data["pattern_shifts"].values():
                assert pattern_shift["shift_direction"] in {"increased", "decreased", "stable"}

    def test_custom_analyzer(self):
        """Test with custom rhetorical analyzer."""
        def custom_analyzer(texts):
            return {"custom_pattern": {"total_occurrences": len(texts)}}

        texts = ["Text A about ants.", "Text B about colonies."]
        result = track_conceptual_shifts(texts, rhetorical_analyzer=custom_analyzer)
        assert len(result) == 1


class TestQuantifyFramingEffects:
    """Test quantify_framing_effects function."""

    def test_empty_texts(self):
        """Test with empty text list."""
        result = quantify_framing_effects([])
        assert result == {}

    def test_default_framing_concepts(self):
        """Test with default framing concepts."""
        texts = [
            "Ants think and decide where to forage.",
            "The mechanism of colony function operates through pheromones.",
            "The purpose of foraging behavior is to optimize colony fitness.",
        ]
        result = quantify_framing_effects(texts)
        # At least one framing concept should match
        assert len(result) > 0

    def test_custom_framing_concepts(self):
        """Test with custom framing concepts."""
        texts = ["Ants think and decide where to forage."]
        result = quantify_framing_effects(texts, framing_concepts=["anthropomorphic"])
        if "anthropomorphic" in result:
            data = result["anthropomorphic"]
            assert "framing_strength" in data
            assert "consistency_score" in data
            assert "impact_score" in data

    def test_framing_strength_bounded(self):
        """Test framing strength is between 0 and 1."""
        texts = ["Ants decide to cooperate.", "Workers choose tasks."]
        result = quantify_framing_effects(texts, framing_concepts=["anthropomorphic"])
        for data in result.values():
            assert 0 <= data["framing_strength"] <= 1

    def test_no_matching_framing(self):
        """Test when no texts match framing concepts."""
        texts = ["Temperature was 25 degrees."]
        result = quantify_framing_effects(texts, framing_concepts=["anthropomorphic"])
        # "think", "decide", etc. not in text, so no match
        assert "anthropomorphic" not in result

    def test_with_argumentative_analyzer(self):
        """Test with custom argumentative analyzer."""
        def arg_analyzer(texts):
            return [{"claim": t} for t in texts]

        texts = ["The mechanism controls behavior.", "The system function operates."]
        result = quantify_framing_effects(
            texts,
            framing_concepts=["mechanistic"],
            argumentative_analyzer=arg_analyzer,
        )
        if "mechanistic" in result:
            assert result["mechanistic"]["argumentation_structures"] >= 0

    def test_output_structure(self):
        """Test output has expected keys for matching concepts."""
        texts = ["The colony mechanism operates efficiently. The system controls behavior."]
        result = quantify_framing_effects(texts, framing_concepts=["mechanistic"])
        if "mechanistic" in result:
            data = result["mechanistic"]
            assert "framing_strength" in data
            assert "consistency_score" in data
            assert "affected_texts" in data
            assert "downstream_rhetorical_patterns" in data
            assert "framing_indicators_used" in data
            assert "impact_score" in data
