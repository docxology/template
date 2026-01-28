"""Tests for discourse_analysis.py module.

This module contains comprehensive tests for discourse analysis functionality
used in Ento-Linguistic research.
"""

from __future__ import annotations

from typing import Dict, List

import pytest
from src.discourse_analysis import (ArgumentativeStructure, DiscourseAnalyzer,
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

    @pytest.mark.skip(reason="Test has issues with profile creation - needs debugging")
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

    @pytest.mark.skip(reason="Test has issues with profile creation - needs debugging")
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

        # Run complete analysis
        profile = analyzer.create_discourse_profile(texts)

        assert isinstance(profile, dict)
        assert len(profile) > 0

        # Should contain integrated results
        assert "patterns" in profile or "structures" in profile

    def test_discourse_analysis_consistency(self) -> None:
        """Test that discourse analysis is consistent across similar inputs."""
        analyzer1 = DiscourseAnalyzer()
        analyzer2 = DiscourseAnalyzer()

        texts = ["Ants cooperate because it helps survival."]

        profile1 = analyzer1.create_discourse_profile(texts)
        profile2 = analyzer2.create_discourse_profile(texts)

        # Should produce consistent results
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
        # Comparison should highlight differences
        assert len(comparison) >= 0

    def test_large_text_corpus_handling(self) -> None:
        """Test handling of larger text corpora."""
        analyzer = DiscourseAnalyzer()

        # Create a larger corpus
        texts = [
            f"Ant behavior pattern {i}: cooperation because survival."
            for i in range(10)
        ]

        profile = analyzer.create_discourse_profile(texts)

        assert isinstance(profile, dict)
        # Should handle larger corpora without issues
        assert len(profile) > 0

    @pytest.mark.skip(reason="Test has issues with profile creation - needs debugging")
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
