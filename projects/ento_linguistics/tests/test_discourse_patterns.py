"""Tests for analysis/discourse_patterns.py module.

Covers: DiscoursePattern, ArgumentativeStructure, DISCOURSE_MARKERS,
identify_patterns_in_text, extract_argumentative_structure.
"""
from __future__ import annotations

import pytest

from analysis.discourse_patterns import (
    DISCOURSE_MARKERS,
    ArgumentativeStructure,
    DiscoursePattern,
    extract_argumentative_structure,
    identify_patterns_in_text,
)


class TestDiscoursePattern:
    """Test DiscoursePattern dataclass."""

    def test_creation_defaults(self):
        """Test DiscoursePattern with default fields."""
        pattern = DiscoursePattern(pattern_type="causation")
        assert pattern.pattern_type == "causation"
        assert pattern.examples == []
        assert pattern.frequency == 0
        assert pattern.domains == set()
        assert pattern.rhetorical_function == ""

    def test_creation_full(self):
        """Test DiscoursePattern with all fields."""
        pattern = DiscoursePattern(
            pattern_type="contrast",
            examples=["however ants cooperate"],
            frequency=3,
            domains={"behavior_and_identity"},
            rhetorical_function="establishes contrast",
        )
        assert pattern.pattern_type == "contrast"
        assert len(pattern.examples) == 1
        assert pattern.frequency == 3
        assert "behavior_and_identity" in pattern.domains

    def test_add_example(self):
        """Test adding examples updates frequency."""
        pattern = DiscoursePattern(pattern_type="causation")
        pattern.add_example("because ants cooperate")
        assert pattern.frequency == 1
        assert "because ants cooperate" in pattern.examples

        pattern.add_example("since colonies grow")
        assert pattern.frequency == 2
        assert len(pattern.examples) == 2


class TestArgumentativeStructure:
    """Test ArgumentativeStructure dataclass."""

    def test_creation_defaults(self):
        """Test ArgumentativeStructure with default fields."""
        structure = ArgumentativeStructure()
        assert structure.claim == ""
        assert structure.evidence == []
        assert structure.warrant == ""
        assert structure.qualification == ""
        assert structure.discourse_markers == []

    def test_creation_full(self):
        """Test ArgumentativeStructure with all fields."""
        structure = ArgumentativeStructure(
            claim="Therefore ants cooperate",
            evidence=["Research shows colonies thrive"],
            warrant="Because cooperation improves fitness",
            qualification="However this varies by species",
            discourse_markers=["therefore", "because", "however"],
        )
        assert structure.claim == "Therefore ants cooperate"
        assert len(structure.evidence) == 1
        assert structure.warrant.startswith("Because")
        assert len(structure.discourse_markers) == 3


class TestDiscourseMarkers:
    """Test DISCOURSE_MARKERS constant."""

    def test_all_categories_present(self):
        """Test that all expected categories exist."""
        expected = {"causation", "contrast", "evidence", "generalization", "hedging", "certainty"}
        assert set(DISCOURSE_MARKERS.keys()) == expected

    def test_categories_have_markers(self):
        """Test that each category has at least one marker."""
        for category, markers in DISCOURSE_MARKERS.items():
            assert len(markers) > 0, f"Category {category} has no markers"
            assert all(isinstance(m, str) for m in markers)


class TestIdentifyPatternsInText:
    """Test identify_patterns_in_text function."""

    def test_empty_text(self):
        """Test with empty text returns no patterns."""
        result = identify_patterns_in_text("")
        assert result == {}

    def test_anthropomorphic_framing(self):
        """Test detection of anthropomorphic constructions."""
        text = "The ant colony decides where to forage. Workers choose which tasks to perform."
        result = identify_patterns_in_text(text)
        assert "anthropomorphic_framing" in result
        assert result["anthropomorphic_framing"]["domain"] == "behavior_and_identity"

    def test_hierarchical_framing(self):
        """Test detection of hierarchical language."""
        text = "The dominant ant controls subordinate workers through authority."
        result = identify_patterns_in_text(text)
        assert "hierarchical_framing" in result
        assert result["hierarchical_framing"]["domain"] == "power_and_labor"

    def test_economic_metaphors(self):
        """Test detection of economic metaphor patterns."""
        text = "The cost of foraging must be weighed against the benefit to the colony investment."
        result = identify_patterns_in_text(text)
        assert "economic_metaphors" in result
        assert result["economic_metaphors"]["domain"] == "economics"

    def test_scale_ambiguity(self):
        """Test detection of scale ambiguity patterns."""
        text = "The colony behavior emerges from individual behavior of each worker."
        result = identify_patterns_in_text(text)
        assert "scale_ambiguity" in result
        assert result["scale_ambiguity"]["domain"] == "unit_of_individuality"

    def test_multiple_patterns(self):
        """Test detection of multiple patterns in one text."""
        text = (
            "The ant colony decides to forage based on cost and benefit analysis. "
            "The dominant queen controls subordinate workers. "
            "Colony behavior emerges from individual behavior."
        )
        result = identify_patterns_in_text(text)
        assert len(result) >= 3

    def test_no_patterns_in_neutral_text(self):
        """Test that neutral text yields no patterns."""
        text = "The temperature was measured at 25 degrees Celsius."
        result = identify_patterns_in_text(text)
        assert result == {}


class TestExtractArgumentativeStructure:
    """Test extract_argumentative_structure function."""

    def test_empty_sentences(self):
        """Test with empty sentence list."""
        result = extract_argumentative_structure([])
        assert result.claim == ""
        assert result.evidence == []
        assert result.warrant == ""
        assert result.qualification == ""

    def test_claim_detection(self):
        """Test claim detection via 'therefore'."""
        sentences = [
            "Ants form complex colonies.",
            "Therefore ants exhibit eusocial behavior.",
        ]
        result = extract_argumentative_structure(sentences)
        assert "therefore" in result.claim.lower()

    def test_evidence_detection(self):
        """Test evidence detection via 'research shows'."""
        sentences = [
            "Research shows that ant colonies adapt to environmental changes.",
            "Some other observation.",
        ]
        result = extract_argumentative_structure(sentences)
        assert len(result.evidence) >= 1

    def test_warrant_detection(self):
        """Test warrant detection via 'because'."""
        sentences = [
            "Because cooperation improves colony fitness.",
        ]
        result = extract_argumentative_structure(sentences)
        assert "because" in result.warrant.lower()

    def test_qualification_detection(self):
        """Test qualification detection via 'however'."""
        sentences = [
            "However this varies among different species.",
        ]
        result = extract_argumentative_structure(sentences)
        assert "however" in result.qualification.lower()

    def test_discourse_markers_collected(self):
        """Test that discourse markers are collected from sentences."""
        sentences = [
            "Because ants cooperate, the colony therefore thrives.",
            "However, not all species behave this way.",
        ]
        result = extract_argumentative_structure(sentences)
        assert len(result.discourse_markers) > 0
        assert "because" in result.discourse_markers

    def test_full_argument(self):
        """Test extraction of a complete argumentative structure."""
        sentences = [
            "Research shows that eusocial insects exhibit division of labor.",
            "Because this division improves colony efficiency.",
            "Therefore ant colonies are highly organized.",
            "However, some species show less rigid hierarchies.",
        ]
        result = extract_argumentative_structure(sentences)
        assert len(result.evidence) >= 1
        assert result.warrant != ""
        assert result.claim != ""
        assert result.qualification != ""
