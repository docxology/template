"""Tests for infrastructure.llm.templates.research module.

Tests all ResearchTemplate subclasses using real string inputs (No Mocks Policy).
"""

from __future__ import annotations

import pytest

from infrastructure.llm.templates.research import (
    CitationNetworkAnalysis,
    CodeDocumentation,
    ComparativeAnalysis,
    DataInterpretation,
    LiteratureReview,
    LiteratureReviewSynthesis,
    PaperSummarization,
    ResearchGapIdentification,
    ScienceCommunicationNarrative,
    SummarizeAbstract,
)


class TestSummarizeAbstract:
    """Tests for SummarizeAbstract template."""

    def test_render_returns_string(self):
        result = SummarizeAbstract().render(text="Experimental results show...")
        assert isinstance(result, str)

    def test_render_includes_text(self):
        result = SummarizeAbstract().render(text="Test abstract content")
        assert "Test abstract content" in result

    def test_render_missing_variable_raises(self):
        with pytest.raises(Exception):
            SummarizeAbstract().render()


class TestLiteratureReview:
    """Tests for LiteratureReview template."""

    def test_render_returns_string(self):
        result = LiteratureReview().render(summaries="Paper 1: ...\nPaper 2: ...")
        assert isinstance(result, str)

    def test_render_includes_summaries(self):
        result = LiteratureReview().render(summaries="Smith et al. 2023")
        assert "Smith et al. 2023" in result

    def test_render_missing_variable_raises(self):
        with pytest.raises(Exception):
            LiteratureReview().render()


class TestCodeDocumentation:
    """Tests for CodeDocumentation template."""

    def test_render_returns_string(self):
        result = CodeDocumentation().render(code="def foo(): pass")
        assert isinstance(result, str)

    def test_render_includes_code(self):
        code = "def add(a, b): return a + b"
        result = CodeDocumentation().render(code=code)
        assert code in result

    def test_render_missing_variable_raises(self):
        with pytest.raises(Exception):
            CodeDocumentation().render()


class TestDataInterpretation:
    """Tests for DataInterpretation template."""

    def test_render_returns_string(self):
        result = DataInterpretation().render(stats="mean=5.2, std=1.3")
        assert isinstance(result, str)

    def test_render_includes_stats(self):
        result = DataInterpretation().render(stats="n=100, p=0.001")
        assert "n=100, p=0.001" in result


class TestPaperSummarization:
    """Tests for PaperSummarization template."""

    def test_render_returns_string(self):
        result = PaperSummarization().render(
            title="Test Paper",
            authors="Smith, J.",
            year="2023",
            source="Nature",
            text="The paper presents...",
        )
        assert isinstance(result, str)

    def test_render_includes_title(self):
        result = PaperSummarization().render(
            title="My Research Paper",
            authors="Doe, J.",
            year="2024",
            source="arXiv",
            text="Abstract text here.",
        )
        assert "My Research Paper" in result

    def test_render_includes_domain_info(self):
        result = PaperSummarization().render(
            title="T",
            authors="A",
            year="2024",
            source="S",
            text="Paper text",
            domain="biology",
        )
        assert "biology" in result.lower()
        assert "Paper text" in result

    def test_render_with_reference_count(self):
        result = PaperSummarization().render(
            title="T",
            authors="A",
            year="2024",
            source="S",
            text="Content",
            reference_count=42,
        )
        assert isinstance(result, str)


class TestLiteratureReviewSynthesis:
    """Tests for LiteratureReviewSynthesis template."""

    def test_render_returns_string(self):
        result = LiteratureReviewSynthesis().render(
            summaries="Paper A, Paper B",
            num_papers="2",
            focus="methodology",
        )
        assert isinstance(result, str)

    def test_render_includes_focus(self):
        result = LiteratureReviewSynthesis().render(
            summaries="...",
            num_papers="3",
            focus="deep learning",
        )
        assert "deep learning" in result

    def test_render_includes_num_papers(self):
        result = LiteratureReviewSynthesis().render(
            summaries="...",
            num_papers="5",
            focus="results",
        )
        assert "5" in result


class TestScienceCommunicationNarrative:
    """Tests for ScienceCommunicationNarrative template."""

    def test_render_returns_string(self):
        result = ScienceCommunicationNarrative().render(
            papers="Paper 1 content",
            num_papers="1",
            audience="general public",
            narrative_style="journalistic",
        )
        assert isinstance(result, str)

    def test_render_includes_audience(self):
        result = ScienceCommunicationNarrative().render(
            papers="...",
            num_papers="1",
            audience="high school students",
            narrative_style="storytelling",
        )
        assert "high school students" in result


class TestComparativeAnalysis:
    """Tests for ComparativeAnalysis template."""

    def test_render_returns_string(self):
        result = ComparativeAnalysis().render(
            papers="Paper A\nPaper B",
            num_papers="2",
            aspect="methodology",
        )
        assert isinstance(result, str)

    def test_render_includes_aspect(self):
        result = ComparativeAnalysis().render(
            papers="...",
            num_papers="2",
            aspect="experimental design",
        )
        assert "experimental design" in result


class TestResearchGapIdentification:
    """Tests for ResearchGapIdentification template."""

    def test_render_returns_string(self):
        result = ResearchGapIdentification().render(
            papers="Paper 1\nPaper 2",
            num_papers="2",
            domain="machine learning",
        )
        assert isinstance(result, str)

    def test_render_includes_domain(self):
        result = ResearchGapIdentification().render(
            papers="...",
            num_papers="3",
            domain="genomics",
        )
        assert "genomics" in result


class TestCitationNetworkAnalysis:
    """Tests for CitationNetworkAnalysis template."""

    def test_render_returns_string(self):
        result = CitationNetworkAnalysis().render(
            papers="Smith 2020, Jones 2021",
            num_papers="2",
            analysis_focus="key works",
        )
        assert isinstance(result, str)

    def test_render_includes_analysis_focus(self):
        result = CitationNetworkAnalysis().render(
            papers="...",
            num_papers="2",
            analysis_focus="foundational papers",
        )
        assert "foundational papers" in result
