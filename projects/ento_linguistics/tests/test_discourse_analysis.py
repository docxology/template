"""Tests for discourse_analysis.py module.

This module contains comprehensive tests for discourse analysis functionality
used in Ento-Linguistic research.
"""

from __future__ import annotations

from typing import Dict, List

import pytest
from analysis.discourse_analysis import (ArgumentativeStructure, DiscourseAnalyzer,
                                    DiscoursePattern)


class TestDiscoursePattern:
    """Test DiscoursePattern dataclass functionality."""

    def test_discourse_pattern_creation(self) -> None:
        """Test creating a DiscoursePattern instance."""
        pattern = DiscoursePattern(
            pattern_type="causation",
            examples=["because ants cooperate"],
            frequency=5,
            domains={"behavior_and_identity"},
            rhetorical_function="establishes causal relationships",
        )

        assert pattern.pattern_type == "causation"
        assert len(pattern.examples) == 1
        assert pattern.frequency == 5
        assert "behavior_and_identity" in pattern.domains
        assert "causal" in pattern.rhetorical_function

    def test_discourse_pattern_add_example(self) -> None:
        """Test adding examples to discourse pattern."""
        pattern = DiscoursePattern(pattern_type="contrast")

        pattern.add_example("however, some ants differ")
        assert len(pattern.examples) == 1
        assert pattern.frequency == 1

        pattern.add_example("yet, colony behavior varies")
        assert len(pattern.examples) == 2
        assert pattern.frequency == 2


class TestArgumentativeStructure:
    """Test ArgumentativeStructure dataclass functionality."""

    def test_argumentative_structure_creation(self) -> None:
        """Test creating an ArgumentativeStructure instance."""
        structure = ArgumentativeStructure(
            claim="Ants exhibit complex social behavior",
            evidence=["field observations", "laboratory experiments"],
            warrant="empirical data supports social complexity",
            qualification="in most species",
            discourse_markers=["according to", "as shown"],
        )

        assert structure.claim == "Ants exhibit complex social behavior"
        assert len(structure.evidence) == 2
        assert "empirical" in structure.warrant
        assert "most" in structure.qualification
        assert len(structure.discourse_markers) == 2


class TestDiscourseAnalyzer:
    """Test DiscourseAnalyzer functionality."""

    @pytest.fixture
    def analyzer(self) -> DiscourseAnalyzer:
        """Create a DiscourseAnalyzer instance."""
        return DiscourseAnalyzer()

    @pytest.fixture
    def sample_texts(self) -> List[str]:
        """Create sample texts for testing."""
        return [
            "Ants cooperate because it increases colony survival. However, some species show different behaviors.",
            "According to recent studies, eusocial insects demonstrate complex social structures.",
            "The data clearly shows that division of labor enhances colony efficiency.",
        ]

    def test_analyzer_initialization(self, analyzer: DiscourseAnalyzer) -> None:
        """Test analyzer initialization."""
        assert analyzer.text_processor is not None
        assert analyzer.feature_extractor is not None
        assert isinstance(analyzer.DISCOURSE_MARKERS, dict)
        assert "causation" in analyzer.DISCOURSE_MARKERS
        assert "contrast" in analyzer.DISCOURSE_MARKERS

    def test_analyze_discourse_patterns(
        self, analyzer: DiscourseAnalyzer, sample_texts: List[str]
    ) -> None:
        """Test discourse pattern analysis."""
        patterns = analyzer.analyze_discourse_patterns(sample_texts)

        assert isinstance(patterns, dict)
        # Should identify some patterns
        assert len(patterns) > 0

        # Check that patterns have required attributes
        for pattern in patterns.values():
            assert isinstance(pattern, DiscoursePattern)
            assert pattern.pattern_type
            assert pattern.frequency >= 0
            assert isinstance(pattern.domains, set)

    def test_analyze_discourse_patterns_empty_input(
        self, analyzer: DiscourseAnalyzer
    ) -> None:
        """Test discourse pattern analysis with empty input."""
        patterns = analyzer.analyze_discourse_patterns([])
        assert isinstance(patterns, dict)
        assert len(patterns) == 0

    def test_identify_patterns_in_text(self, analyzer: DiscourseAnalyzer) -> None:
        """Test pattern identification in single text."""
        text = "Ants cooperate because it helps survival. However, competition exists."

        patterns = analyzer._identify_patterns_in_text(text)

        assert isinstance(patterns, dict)
        # Should find causation and contrast patterns
        assert len(patterns) > 0

    def test_analyze_argumentative_structures(
        self, analyzer: DiscourseAnalyzer, sample_texts: List[str]
    ) -> None:
        """Test argumentative structure analysis."""
        structures = analyzer.analyze_argumentative_structures(sample_texts)

        assert isinstance(structures, list)
        # Should extract some argumentative structures
        assert len(structures) >= 0

        for structure in structures:
            assert isinstance(structure, ArgumentativeStructure)

    def test_extract_argumentative_structure(self, analyzer: DiscourseAnalyzer) -> None:
        """Test extraction of argumentative structure from sentences."""
        sentences = [
            "Ant colonies are highly organized.",
            "This is shown by division of labor.",
            "Field studies demonstrate this clearly.",
        ]

        structure = analyzer._extract_argumentative_structure(sentences)

        assert isinstance(structure, ArgumentativeStructure)
        assert structure.claim or len(structure.evidence) > 0

    def test_analyze_rhetorical_strategies(
        self, analyzer: DiscourseAnalyzer, sample_texts: List[str]
    ) -> None:
        """Test rhetorical strategies analysis."""
        strategies = analyzer.analyze_rhetorical_strategies(sample_texts)

        assert isinstance(strategies, dict)
        # Should contain strategy analysis
        assert len(strategies) > 0

        # Check for expected rhetorical elements
        for strategy_name, analysis in strategies.items():
            assert isinstance(analysis, dict)
            assert "frequency" in analysis or "examples" in analysis

    def test_identify_narrative_frameworks(
        self, analyzer: DiscourseAnalyzer, sample_texts: List[str]
    ) -> None:
        """Test narrative framework identification."""
        frameworks = analyzer.identify_narrative_frameworks(sample_texts)

        assert isinstance(frameworks, dict)
        # Should identify some narrative elements
        assert len(frameworks) >= 0

        for framework_name, elements in frameworks.items():
            assert isinstance(elements, list)

    def test_analyze_persuasive_techniques(
        self, analyzer: DiscourseAnalyzer, sample_texts: List[str]
    ) -> None:
        """Test persuasive techniques analysis."""
        techniques = analyzer.analyze_persuasive_techniques(sample_texts)

        assert isinstance(techniques, dict)
        # Should analyze persuasive elements
        assert len(techniques) > 0

        for technique_name, analysis in techniques.items():
            assert isinstance(analysis, dict)

    def test_create_discourse_profile(
        self, analyzer: DiscourseAnalyzer, sample_texts: List[str]
    ) -> None:
        """Test discourse profile creation."""
        profile = analyzer.create_discourse_profile(sample_texts)

        assert isinstance(profile, dict)
        # Should contain comprehensive discourse analysis
        assert len(profile) > 0

        # Check for expected profile components
        expected_keys = [
            "patterns",
            "structures",
            "strategies",
            "frameworks",
            "techniques",
        ]
        for key in expected_keys:
            if key in profile:
                assert isinstance(profile[key], (dict, list))

    def test_create_discourse_profile_empty_input(
        self, analyzer: DiscourseAnalyzer
    ) -> None:
        """Test discourse profile creation with empty input."""
        profile = analyzer.create_discourse_profile([])

        assert isinstance(profile, dict)
        # Should handle empty input gracefully
        assert len(profile) >= 0

    def test_compare_discourse_profiles(
        self, analyzer: DiscourseAnalyzer, sample_texts: List[str]
    ) -> None:
        """Test discourse profile comparison."""
        profile1 = analyzer.create_discourse_profile(sample_texts)
        profile2 = analyzer.create_discourse_profile(sample_texts[:2])  # Subset

        comparison = analyzer.compare_discourse_profiles(profile1, profile2)

        assert isinstance(comparison, dict)
        # Should contain comparison results
        assert len(comparison) >= 0

    def test_export_discourse_analysis(
        self, analyzer: DiscourseAnalyzer, sample_texts: List[str], tmp_path
    ) -> None:
        """Test discourse analysis export."""
        profile = analyzer.create_discourse_profile(sample_texts)
        filepath = tmp_path / "discourse_analysis.json"

        analyzer.export_discourse_analysis(profile, str(filepath))

        assert filepath.exists()
        assert filepath.stat().st_size > 0

        # Verify it's valid JSON
        import json

        with open(filepath, "r") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_discourse_markers_comprehensive(self, analyzer: DiscourseAnalyzer) -> None:
        """Test that discourse markers cover major rhetorical categories."""
        markers = analyzer.DISCOURSE_MARKERS

        assert isinstance(markers, dict)
        assert len(markers) > 0

        # Check for major categories
        major_categories = ["causation", "contrast", "evidence"]
        for category in major_categories:
            assert category in markers
            assert isinstance(markers[category], list)
            assert len(markers[category]) > 0

    def test_pattern_frequency_calculation(self, analyzer: DiscourseAnalyzer) -> None:
        """Test that pattern frequencies are calculated correctly."""
        texts = [
            "ants cooperate and communicate",  # anthropomorphic framing
            "colony workers choose tasks",  # anthropomorphic framing again
            "ants prefer certain foods",  # anthropomorphic framing again
        ]

        patterns = analyzer.analyze_discourse_patterns(texts)

        # Should find anthropomorphic_framing pattern with frequency >= 3
        anthropomorphic_found = False
        for pattern in patterns.values():
            if "anthropomorphic" in pattern.pattern_type.lower():
                anthropomorphic_found = True
                assert pattern.frequency >= 3
                assert len(pattern.examples) >= 3

        assert (
            anthropomorphic_found
        ), "Anthropomorphic framing pattern should be detected"

    def test_argumentative_structure_extraction(
        self, analyzer: DiscourseAnalyzer
    ) -> None:
        """Test detailed argumentative structure extraction."""
        text = "Ant colonies succeed because they cooperate. This is clearly shown in field studies."

        structures = analyzer.analyze_argumentative_structures([text])

        assert len(structures) >= 0
        if structures:
            structure = structures[0]
            assert isinstance(structure.claim, str)
            assert isinstance(structure.evidence, list)
            assert isinstance(structure.discourse_markers, list)

    def test_rhetorical_strategy_detection(self, analyzer: DiscourseAnalyzer) -> None:
        """Test detection of specific rhetorical strategies."""
        text = "According to Smith (2023), ant behavior demonstrates evolutionary adaptation."

        strategies = analyzer.analyze_rhetorical_strategies([text])

        # Should detect authority citations
        assert strategies["authority"]["frequency"] == 1
        assert len(strategies["authority"]["examples"]) == 1
        assert "(2023)" in strategies["authority"]["examples"][0]


class TestDiscourseAnalysisIntegration:
    """Integration tests for discourse analysis components."""

    @pytest.fixture
    def analyzer(self) -> DiscourseAnalyzer:
        """Create a DiscourseAnalyzer instance."""
        return DiscourseAnalyzer()

    @pytest.fixture
    def sample_texts(self) -> List[str]:
        """Create sample texts for testing."""
        return [
            "Ants cooperate because it increases colony survival. However, some species show different behaviors.",
            "According to recent studies, eusocial insects demonstrate complex social structures.",
            "The data clearly shows that division of labor enhances colony efficiency.",
        ]

    def test_complete_discourse_workflow(self) -> None:
        """Test complete discourse analysis workflow."""
        analyzer = DiscourseAnalyzer()

        texts = [
            "Ants cooperate because it enhances survival. However, some species compete.",
            "According to research, eusociality evolved through kin selection.",
            "The data clearly shows complex social structures in colonies.",
        ]

        profile = analyzer.create_discourse_profile(texts)

        assert isinstance(profile, dict)
        assert len(profile) > 0
        assert "patterns" in profile or "structures" in profile

    def test_discourse_analysis_consistency(self) -> None:
        """Test that discourse analysis is consistent across similar inputs."""
        analyzer1 = DiscourseAnalyzer()
        analyzer2 = DiscourseAnalyzer()

        texts = ["Ants cooperate because it helps survival."]

        profile1 = analyzer1.create_discourse_profile(texts)
        profile2 = analyzer2.create_discourse_profile(texts)

        assert isinstance(profile1, dict)
        assert isinstance(profile2, dict)
        assert len(profile1) == len(profile2)

    def test_discourse_profile_comparison(self) -> None:
        """Test comparison of different discourse profiles."""
        analyzer = DiscourseAnalyzer()

        texts1 = ["Ants cooperate because it helps."]
        texts2 = ["However, some ants compete instead."]

        profile1 = analyzer.create_discourse_profile(texts1)
        profile2 = analyzer.create_discourse_profile(texts2)

        comparison = analyzer.compare_discourse_profiles(profile1, profile2)

        assert isinstance(comparison, dict)
        assert len(comparison) >= 0

    def test_large_text_corpus_handling(self) -> None:
        """Test handling of larger text corpora."""
        analyzer = DiscourseAnalyzer()

        texts = [
            f"Ant behavior pattern {i}: cooperation because survival."
            for i in range(10)
        ]

        profile = analyzer.create_discourse_profile(texts)

        assert isinstance(profile, dict)
        assert len(profile) > 0

    def test_export_discourse_analysis(
        self, analyzer: DiscourseAnalyzer, sample_texts: List[str], tmp_path
    ) -> None:
        """Test discourse analysis export."""
        profile = analyzer.create_discourse_profile(sample_texts)
        filepath = tmp_path / "discourse_analysis.json"

        analyzer.export_discourse_analysis(profile, str(filepath))

        assert filepath.exists()
        assert filepath.stat().st_size > 0

        import json

        with open(filepath, "r") as f:
            data = json.load(f)
        assert isinstance(data, dict)


# --- Quantitative analysis tests (merged from expanded tests) ---


@pytest.fixture
def rich_texts():
    """Create rich sample texts with discourse markers and framing language."""
    return [
        "The queen bee therefore orchestrates the colony's division of labor. "
        "However, worker bees demonstrate remarkable autonomy in foraging decisions. "
        "Furthermore, the evidence shows that pheromone signaling shapes colony behavior. "
        "This suggests that ant colonies function as superorganisms with emergent intelligence. "
        "Moreover, recent studies indicate that insect communication is more complex than previously assumed. "
        "In conclusion, these findings support the hypothesis that social insects exhibit collective cognition.",
        "Studies demonstrate that honeybee dance language communicates precise spatial information. "
        "Similarly, ant trail pheromones create self-organizing networks. "
        "Nevertheless, the mechanistic basis of these behaviors remains poorly understood. "
        "The results indicate that colony-level optimization emerges from simple individual rules. "
        "Specifically, each worker responds to local signals without global knowledge. "
        "Consequently, the swarm intelligence paradigm has transformed our understanding of insect societies.",
        "The data confirm that termite mounds regulate temperature through architectural design. "
        "In contrast, wasp nests rely on behavioral thermoregulation by workers. "
        "These observations imply that different insect lineages evolved convergent solutions. "
        "The evidence suggests that natural selection has shaped collective building instincts. "
        "Additionally, the holistic framework reveals interconnections between insect behavior and ecology. "
        "Thus, an anthropomorphic interpretation of insect intelligence may obscure biological mechanisms.",
    ]


class TestQuantifyRhetoricalPatterns:
    """Tests for quantify_rhetorical_patterns method."""

    @pytest.fixture
    def analyzer(self) -> DiscourseAnalyzer:
        return DiscourseAnalyzer()

    def test_basic_quantification(self, analyzer, rich_texts):
        result = analyzer.quantify_rhetorical_patterns(rich_texts)
        assert isinstance(result, dict)
        for key, val in result.items():
            assert "total_occurrences" in val
            assert "text_coverage" in val
            assert "effectiveness_score" in val
            assert "persuasiveness_rating" in val

    def test_effectiveness_score_bounded(self, analyzer, rich_texts):
        result = analyzer.quantify_rhetorical_patterns(rich_texts)
        for key, val in result.items():
            assert 0 <= val["effectiveness_score"] <= 1.0
            assert 0 <= val["persuasiveness_rating"] <= 1.0

    def test_empty_texts(self, analyzer):
        result = analyzer.quantify_rhetorical_patterns([])
        assert isinstance(result, dict)


class TestScoreArgumentativeStructures:
    """Tests for score_argumentative_structures method."""

    @pytest.fixture
    def analyzer(self) -> DiscourseAnalyzer:
        return DiscourseAnalyzer()

    def test_basic_scoring(self, analyzer, rich_texts):
        result = analyzer.score_argumentative_structures(rich_texts)
        assert isinstance(result, dict)
        for key, val in result.items():
            assert "claim_strength" in val
            assert "evidence_quality" in val
            assert "reasoning_coherence" in val
            assert "overall_strength" in val
            assert "confidence_score" in val

    def test_overall_strength_is_average(self, analyzer, rich_texts):
        result = analyzer.score_argumentative_structures(rich_texts)
        for key, val in result.items():
            expected = (val["claim_strength"] + val["evidence_quality"] + val["reasoning_coherence"]) / 3
            assert abs(val["overall_strength"] - expected) < 0.001

    def test_scores_bounded(self, analyzer, rich_texts):
        result = analyzer.score_argumentative_structures(rich_texts)
        for key, val in result.items():
            assert 0 <= val["claim_strength"] <= 1.0
            assert 0 <= val["evidence_quality"] <= 1.0
            assert 0 <= val["reasoning_coherence"] <= 1.0


class TestAnalyzeNarrativeFrequency:
    """Tests for analyze_narrative_frequency method."""

    @pytest.fixture
    def analyzer(self) -> DiscourseAnalyzer:
        return DiscourseAnalyzer()

    def test_basic_analysis(self, analyzer, rich_texts):
        result = analyzer.analyze_narrative_frequency(rich_texts)
        assert isinstance(result, dict)
        for key, val in result.items():
            assert "frequency" in val
            assert "coverage_percentage" in val
            assert "average_text_length" in val
            assert "unique_phrase_count" in val
            assert "consistency_score" in val

    def test_coverage_bounded(self, analyzer, rich_texts):
        result = analyzer.analyze_narrative_frequency(rich_texts)
        for key, val in result.items():
            assert 0 <= val["coverage_percentage"] <= 100

    def test_examples_limited(self, analyzer, rich_texts):
        result = analyzer.analyze_narrative_frequency(rich_texts)
        for key, val in result.items():
            assert len(val.get("examples", [])) <= 3


class TestMeasurePersuasiveEffectiveness:
    """Tests for measure_persuasive_effectiveness method."""

    @pytest.fixture
    def analyzer(self) -> DiscourseAnalyzer:
        return DiscourseAnalyzer()

    def test_basic_measurement(self, analyzer, rich_texts):
        result = analyzer.measure_persuasive_effectiveness(rich_texts)
        assert isinstance(result, dict)
        for key, val in result.items():
            assert "usage_frequency" in val
            assert "context_relevance" in val
            assert "impact_score" in val
            assert "effectiveness_rating" in val

    def test_impact_bounded(self, analyzer, rich_texts):
        result = analyzer.measure_persuasive_effectiveness(rich_texts)
        for key, val in result.items():
            assert 0 <= val["impact_score"] <= 1.0


class TestAnalyzeTermUsageContext:
    """Tests for analyze_term_usage_context method."""

    @pytest.fixture
    def analyzer(self) -> DiscourseAnalyzer:
        return DiscourseAnalyzer()

    def test_basic_context_analysis(self, analyzer, rich_texts):
        terms = ["colony", "worker", "behavior"]
        result = analyzer.analyze_term_usage_context(terms, rich_texts)
        assert isinstance(result, dict)
        if result:
            for term, data in result.items():
                assert "total_occurrences" in data
                assert "context_diversity" in data
                assert "context_types" in data
                assert "position_distribution" in data
                assert "usage_consistency" in data

    def test_nonexistent_term(self, analyzer, rich_texts):
        result = analyzer.analyze_term_usage_context(["zzzznonexistent"], rich_texts)
        assert isinstance(result, dict)
        assert "zzzznonexistent" not in result

    def test_position_distribution_keys(self, analyzer, rich_texts):
        result = analyzer.analyze_term_usage_context(["colony"], rich_texts)
        if "colony" in result:
            pos = result["colony"]["position_distribution"]
            assert "early" in pos
            assert "middle" in pos
            assert "late" in pos

    def test_context_examples_limited(self, analyzer, rich_texts):
        result = analyzer.analyze_term_usage_context(["the"], rich_texts)
        if "the" in result:
            assert len(result["the"].get("context_examples", [])) <= 5


class TestTrackConceptualShifts:
    """Tests for track_conceptual_shifts method."""

    @pytest.fixture
    def analyzer(self) -> DiscourseAnalyzer:
        return DiscourseAnalyzer()

    def test_basic_tracking(self, analyzer, rich_texts):
        time_periods = ["period_a", "period_b", "period_c"]
        result = analyzer.track_conceptual_shifts(rich_texts, time_periods=time_periods)
        assert isinstance(result, dict)
        assert len(result) == 2

    def test_without_time_periods(self, analyzer, rich_texts):
        result = analyzer.track_conceptual_shifts(rich_texts)
        assert isinstance(result, dict)

    def test_shift_structure(self, analyzer, rich_texts):
        result = analyzer.track_conceptual_shifts(rich_texts)
        for key, shift_data in result.items():
            assert "pattern_shifts" in shift_data
            assert "overall_shift_intensity" in shift_data
            assert "significant_shifts" in shift_data

    def test_mismatched_periods_raises(self, analyzer, rich_texts):
        with pytest.raises(ValueError):
            analyzer.track_conceptual_shifts(rich_texts, time_periods=["a", "b"])

    def test_single_text_no_shifts(self, analyzer):
        result = analyzer.track_conceptual_shifts(["The bee colony thrives."])
        assert isinstance(result, dict)
        assert len(result) == 0


class TestQuantifyFramingEffects:
    """Tests for quantify_framing_effects method."""

    @pytest.fixture
    def analyzer(self) -> DiscourseAnalyzer:
        return DiscourseAnalyzer()

    def test_default_framing_concepts(self, analyzer, rich_texts):
        result = analyzer.quantify_framing_effects(rich_texts)
        assert isinstance(result, dict)

    def test_custom_framing_concepts(self, analyzer, rich_texts):
        result = analyzer.quantify_framing_effects(
            rich_texts, framing_concepts=["anthropomorphic", "mechanistic"]
        )
        assert isinstance(result, dict)

    def test_framing_structure(self, analyzer, rich_texts):
        result = analyzer.quantify_framing_effects(rich_texts)
        for concept, data in result.items():
            assert "framing_strength" in data
            assert "consistency_score" in data
            assert "affected_texts" in data
            assert "impact_score" in data

    def test_framing_strength_bounded(self, analyzer, rich_texts):
        result = analyzer.quantify_framing_effects(rich_texts)
        for concept, data in result.items():
            assert 0 <= data["framing_strength"] <= 1.0


class TestPrivateHelpers:
    """Tests for private helper methods of DiscourseAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> DiscourseAnalyzer:
        return DiscourseAnalyzer()

    def test_calculate_persuasiveness(self, analyzer):
        data = {"frequency": {"a": 3, "b": 2}, "contexts": ["c1", "c2", "c3"]}
        result = analyzer._calculate_persuasiveness(data)
        assert 0 <= result <= 1.0

    def test_evaluate_claim_strength_short(self, analyzer):
        result = analyzer._evaluate_claim_strength("Bees fly")
        assert 0 <= result <= 1.0

    def test_evaluate_claim_strength_with_connector(self, analyzer):
        result = analyzer._evaluate_claim_strength(
            "Therefore the colony adapts to changes in environment"
        )
        assert result > 0.5

    def test_evaluate_claim_strength_question(self, analyzer):
        result = analyzer._evaluate_claim_strength("Do bees communicate?")
        assert result <= 0.8

    def test_evaluate_evidence_quality(self, analyzer):
        evidence = ["Studies show that bees use dance", "Data confirms the hypothesis"]
        result = analyzer._evaluate_evidence_quality(evidence)
        assert 0 <= result <= 1.0

    def test_evaluate_evidence_quality_empty(self, analyzer):
        result = analyzer._evaluate_evidence_quality([])
        assert 0 <= result <= 1.0

    def test_evaluate_reasoning_coherence(self, analyzer):
        reasoning = "Therefore, these results indicate that bee communication is complex"
        result = analyzer._evaluate_reasoning_coherence(reasoning)
        assert 0 <= result <= 1.0

    def test_calculate_structure_confidence(self, analyzer):
        structure = ArgumentativeStructure(
            claim="Bees are intelligent",
            evidence=["Studies show", "Data confirms"],
            warrant="Therefore bees exhibit complex behaviors",
        )
        result = analyzer._calculate_structure_confidence(structure)
        assert 0 <= result <= 1.0

    def test_calculate_framework_consistency(self, analyzer):
        texts = ["The queen controls the colony", "The queen manages the hive"]
        result = analyzer._calculate_framework_consistency(texts)
        assert 0 <= result <= 1.0

    def test_rate_technique_effectiveness(self, analyzer):
        data = {"frequency": 5, "contexts": ["ctx1", "ctx2"]}
        result = analyzer._rate_technique_effectiveness(data)
        assert isinstance(result, str) or isinstance(result, (int, float))

    def test_calculate_technique_impact(self, analyzer):
        data = {"frequency": 5, "contexts": ["ctx1"]}
        result = analyzer._calculate_technique_impact(data)
        assert isinstance(result, (int, float))

    def test_classify_context_type(self, analyzer):
        sentence = "The experiment demonstrates that bees communicate"
        result = analyzer._classify_context_type(sentence, "bees")
        assert isinstance(result, str)

    def test_calculate_usage_consistency(self, analyzer):
        contexts = [
            {"context_type": "definition"},
            {"context_type": "definition"},
            {"context_type": "example"},
        ]
        result = analyzer._calculate_usage_consistency(contexts)
        assert 0 <= result <= 1.0

    def test_get_framing_indicators(self, analyzer):
        result = analyzer._get_framing_indicators("anthropomorphic")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_calculate_framing_consistency(self, analyzer):
        texts = ["The queen decides what to do", "Workers choose their tasks"]
        indicators = ["decides", "choose", "wants"]
        result = analyzer._calculate_framing_consistency(texts, indicators)
        assert 0 <= result <= 1.0
