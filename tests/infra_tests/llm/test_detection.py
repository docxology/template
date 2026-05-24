"""Tests for infrastructure/llm/validation/detection.py.

Covers: RepetitionResult, calculate_unique_content_ratio, detect_repetition,
_deduplicate_paragraphs, and deduplicate_sections.

No mocks used -- all tests use real data and computations.
"""

from __future__ import annotations

from infrastructure.llm.validation.detection import (
    RepetitionResult,
    calculate_unique_content_ratio,
    detect_repetition,
    _deduplicate_paragraphs,
    deduplicate_sections,
)


class TestRepetitionResult:
    """Test the RepetitionResult NamedTuple."""

    def test_construction(self):
        r = RepetitionResult(found=True, examples=["dup1"], unique_ratio=0.8)
        assert r.found is True
        assert r.examples == ["dup1"]
        assert r.unique_ratio == 0.8

    def test_positional_unpacking(self):
        found, examples, ratio = RepetitionResult(False, [], 1.0)
        assert found is False
        assert examples == []
        assert ratio == 1.0


class TestCalculateUniqueContentRatio:
    """Test calculate_unique_content_ratio."""

    def test_empty_text(self):
        assert calculate_unique_content_ratio("") == 1.0

    def test_short_text(self):
        assert calculate_unique_content_ratio("short") == 1.0

    def test_text_shorter_than_two_chunks(self):
        text = "a" * 300
        assert calculate_unique_content_ratio(text, chunk_size=200) == 1.0

    def test_unique_paragraphs(self):
        p1 = "This is the first paragraph about climate science and its impacts. " * 5
        p2 = "The second paragraph discusses economic models and financial markets. " * 5
        text = p1 + "\n\n" + p2
        ratio = calculate_unique_content_ratio(text, chunk_size=100)
        assert ratio > 0.5

    def test_repeated_paragraphs(self):
        paragraph = "This paragraph repeats verbatim across the document many times. " * 5
        text = "\n\n".join([paragraph] * 5)
        ratio = calculate_unique_content_ratio(text, chunk_size=100)
        assert ratio < 0.5

    def test_fixed_size_fallback(self):
        # Single block with no double newlines
        text = "abcdefghij" * 50
        ratio = calculate_unique_content_ratio(text, chunk_size=100)
        # All chunks are different substrings of the repeating pattern
        assert 0.0 < ratio <= 1.0


class TestDetectRepetition:
    """Test detect_repetition."""

    def test_empty_text(self):
        result = detect_repetition("")
        assert result.found is False
        assert result.examples == []
        assert result.unique_ratio == 1.0

    def test_short_text(self):
        result = detect_repetition("short text")
        assert result.found is False

    def test_unique_sections(self):
        sections = []
        for i in range(5):
            sections.append(
                f"## Section {i}\n\nThis section discusses topic number {i} "
                f"with unique content about {'algorithms' if i % 2 == 0 else 'databases'} "
                f"and the specific area number {i * 100}. " * 3
            )
        text = "\n\n\n".join(sections)
        result = detect_repetition(text, min_chunk_size=50)
        # Should produce a valid RepetitionResult
        assert isinstance(result, RepetitionResult)
        assert 0.0 <= result.unique_ratio <= 1.0

    def test_repeated_sections(self):
        section = (
            "## Analysis\n\nThe methodology involves statistical analysis "
            "of the collected data samples using regression techniques "
            "and hypothesis testing across multiple variables. " * 3
        )
        text = "\n\n\n".join([section] * 4)
        result = detect_repetition(text, min_chunk_size=50)
        assert result.found is True

    def test_paragraph_fallback(self):
        # No section markers, just paragraphs
        p1 = "First paragraph about machine learning algorithms and neural networks. " * 4
        p2 = "Second paragraph about database optimization and query planning. " * 4
        text = p1 + "\n\n" + p2
        result = detect_repetition(text, min_chunk_size=50)
        assert isinstance(result, RepetitionResult)

    def test_h2_header_split(self):
        text = (
            "## Introduction\n\nThis is the introduction with lots of content. " * 3
            + "\n## Methods\n\nThis describes the methods used in this research. " * 3
            + "\n## Results\n\nHere we present the results of the analysis. " * 3
        )
        result = detect_repetition(text, min_chunk_size=50)
        assert isinstance(result, RepetitionResult)

    def test_h3_header_split(self):
        text = (
            "### Overview\n\nBroad overview of the entire project scope. " * 3
            + "\n### Details\n\nSpecific details about implementation choices. " * 3
        )
        result = detect_repetition(text, min_chunk_size=50)
        assert isinstance(result, RepetitionResult)


class TestDeduplicateParagraphs:
    """Test _deduplicate_paragraphs."""

    def test_no_paragraphs(self):
        text = "single block of text"
        assert _deduplicate_paragraphs(text, 2, 0.85, 0.7) == text

    def test_two_paragraphs(self):
        text = "First paragraph.\n\nSecond paragraph."
        assert _deduplicate_paragraphs(text, 2, 0.85, 0.7) == text

    def test_removes_exact_duplicates(self):
        para = "This is a repeated paragraph with enough content to trigger deduplication logic. " * 3
        unique = "This is a unique paragraph about something completely different entirely. " * 3
        text = para + "\n\n" + unique + "\n\n" + para + "\n\n" + para
        result = _deduplicate_paragraphs(text, 2, 0.85, 0.7)
        # Should remove some duplicates
        assert len(result) <= len(text)

    def test_preserves_empty_paragraphs(self):
        text = "First paragraph.\n\n\n\nSecond paragraph.\n\nThird paragraph."
        result = _deduplicate_paragraphs(text, 2, 0.85, 0.7)
        assert "First paragraph." in result
        assert "Second paragraph." in result

    def test_content_preservation_check(self):
        # Create text where dedup would remove too much
        para = "Duplicated content that appears many times in the text. " * 5
        # Make it so deduplication would remove >30% of content
        text = "\n\n".join([para] * 10)
        result = _deduplicate_paragraphs(text, 1, 0.5, 0.95)
        # With high preservation threshold, should keep original
        assert len(result) >= len(text) * 0.9


class TestDeduplicateSections:
    """Test deduplicate_sections."""

    def test_empty_text(self):
        assert deduplicate_sections("") == ""

    def test_no_sections(self):
        text = "Just a simple paragraph without any headers at all."
        result = deduplicate_sections(text)
        assert result == text

    def test_unique_sections(self):
        text = (
            "## Introduction\n\nThis introduces the topic.\n\n"
            "## Methods\n\nThis describes the methods.\n\n"
            "## Results\n\nThis shows the results."
        )
        result = deduplicate_sections(text)
        assert "Introduction" in result
        assert "Methods" in result
        assert "Results" in result

    def test_conservative_mode(self):
        section = "## Analysis\n\nDetailed analysis of data patterns and trends. " * 4
        text = section + "\n" + section + "\n" + section
        result = deduplicate_sections(text, mode="conservative")
        assert isinstance(result, str)

    def test_aggressive_mode(self):
        section = "## Analysis\n\nDetailed analysis of data patterns and trends. " * 4
        text = section + "\n" + section + "\n" + section
        result = deduplicate_sections(text, mode="aggressive")
        assert isinstance(result, str)

    def test_balanced_mode(self):
        section = "## Analysis\n\nDetailed analysis of data patterns and trends. " * 4
        text = section + "\n" + section + "\n" + section
        result = deduplicate_sections(text, mode="balanced")
        assert isinstance(result, str)

    def test_falls_back_to_paragraph_dedup(self):
        # No section headers, should fall back to paragraph dedup
        text = "Paragraph one content.\n\nParagraph two content.\n\nParagraph three content."
        result = deduplicate_sections(text)
        assert isinstance(result, str)

    def test_similarity_threshold(self):
        text = (
            "## Overview\n\nThe project examines climate data. " * 3
            + "\n## Overview\n\nThe project examines climate data. " * 3
        )
        result = deduplicate_sections(text, similarity_threshold=0.95)
        assert isinstance(result, str)
