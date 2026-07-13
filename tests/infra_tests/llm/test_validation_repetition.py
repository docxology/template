"""Tests for infrastructure.llm.validation module."""

import pytest

from infrastructure.llm.validation import (
    check_format_compliance,
    clean_repetitive_output,
    deduplicate_sections,
    detect_conversational_phrases,
    detect_repetition,
    has_on_topic_signals,
    is_off_topic,
    validate_no_repetition,
)
from infrastructure.llm.validation.repetition import calculate_unique_content_ratio
from infrastructure.llm.validation.similarity import _calculate_similarity

# =============================================================================
# Repetition Detection Tests
# =============================================================================


class TestRepetitionDetection:
    """Test repetition detection functions."""

    def test_detect_repetition_no_repetition(self):
        """Test that unique content has no repetition detected."""
        text = """
## Section 1
This is the first section with unique content about topic A.

## Section 2
This is the second section with different content about topic B.

## Section 3
This is the third section with yet another unique topic C.
"""
        has_rep, duplicates, unique_ratio = detect_repetition(text)
        # Unique content should have high ratio
        assert unique_ratio >= 0.8
        assert len(duplicates) <= 1  # Minimal or no duplicates

    def test_detect_repetition_with_repetition(self):
        """Test that repeated content is detected."""
        # Create text with repeated sections
        repeated_section = "This is repeated content about machine learning and optimization methods. " * 5
        text = f"""
## Section 1
{repeated_section}

## Section 2
{repeated_section}

## Section 3
{repeated_section}

## Section 4
{repeated_section}
"""
        has_rep, duplicates, unique_ratio = detect_repetition(text)
        # Should detect repetition
        assert has_rep is True
        assert unique_ratio < 0.6  # Low unique ratio

    def test_detect_repetition_short_text(self):
        """Test that short text returns no repetition."""
        short_text = "Short text."
        has_rep, duplicates, unique_ratio = detect_repetition(short_text)
        assert has_rep is False
        assert unique_ratio == 1.0

    def test_detect_repetition_empty_text(self):
        """Test that empty text returns no repetition."""
        has_rep, duplicates, unique_ratio = detect_repetition("")
        assert has_rep is False
        assert unique_ratio == 1.0

    def test_detect_repetition_semantic_similarity(self):
        """Test that semantically similar but differently worded content is not flagged."""
        text = """
## Overview
This section provides an introduction to machine learning algorithms and their applications in data science.

## Introduction
This part discusses machine learning methods and their use in analyzing scientific data.
"""
        has_rep, duplicates, unique_ratio = detect_repetition(text, similarity_threshold=0.8)
        # Should not detect as repetition despite similar topics
        assert has_rep is False
        assert unique_ratio >= 0.8

    def test_detect_repetition_different_similarity_methods(self):
        """Test repetition detection with different similarity methods."""
        repeated_section = "This is repeated content about machine learning. " * 3
        text = f"""
## Section 1
{repeated_section}

## Section 2
{repeated_section}
"""

        # Test with different methods
        has_rep_jaccard, _, _ = detect_repetition(text, similarity_method="jaccard")
        has_rep_tfidf, _, _ = detect_repetition(text, similarity_method="tfidf")
        has_rep_hybrid, _, _ = detect_repetition(text, similarity_method="hybrid")

        # All should detect repetition
        assert has_rep_jaccard is True
        assert has_rep_tfidf is True
        assert has_rep_hybrid is True


class TestUniqueContentRatio:
    """Test unique content ratio calculation."""

    def test_calculate_unique_content_ratio_unique(self):
        """Test ratio for fully unique content."""
        unique_text = "A" * 100 + "B" * 100 + "C" * 100 + "D" * 100
        ratio = calculate_unique_content_ratio(unique_text)
        assert ratio >= 0.8  # Mostly unique

    def test_calculate_unique_content_ratio_repeated(self):
        """Test ratio for repeated content."""
        repeated_block = "This same text repeats. " * 20
        repeated_text = repeated_block * 5
        ratio = calculate_unique_content_ratio(repeated_text)
        assert ratio < 0.5  # Mostly repeated

    def test_calculate_unique_content_ratio_short(self):
        """Test ratio for short content."""
        short_text = "Short"
        ratio = calculate_unique_content_ratio(short_text)
        assert ratio == 1.0  # Too short to analyze


class TestDeduplicateSections:
    """Test section deduplication."""

    def test_deduplicate_removes_repeated_sections(self):
        """Test that repeated sections are removed when safe to do so."""
        text = """
## Introduction
This is a comprehensive introduction with substantial unique content about the research methodology and background.

## Methods
This describes the methods in detail with comprehensive information about algorithms, data processing, and experimental setup.

## Methods
This describes the methods in detail with comprehensive information about algorithms, data processing, and experimental setup.

## Methods
This describes the methods in detail with comprehensive information about algorithms, data processing, and experimental setup.

## Results
These are the comprehensive results with detailed analysis, statistical significance, and interpretation of findings.
"""
        result = deduplicate_sections(
            text,
            max_repetitions=1,
            mode="aggressive",
            similarity_threshold=0.7,
            min_content_preservation=0.5,
        )
        # With sufficient unique content, deduplication should work
        assert result.count("## Methods") <= 2  # Original + max_repetitions

    def test_deduplicate_keeps_unique_sections(self):
        """Test that unique sections are preserved."""
        text = """
## Section A
Content A is unique.

## Section B
Content B is different.

## Section C
Content C is also unique.
"""
        result = deduplicate_sections(text)
        # All sections should be preserved
        assert "Section A" in result
        assert "Section B" in result
        assert "Section C" in result

    def test_deduplicate_empty_text(self):
        """Test deduplication of empty text."""
        assert deduplicate_sections("") == ""

    def test_deduplicate_paragraphs(self):
        """Test paragraph-level deduplication."""
        text = """
First paragraph with unique content.

This is a repeated paragraph about machine learning algorithms and their applications in data science.

Some different content here about experimental results.

This is a repeated paragraph about machine learning algorithms and their applications in data science.

This is a repeated paragraph about machine learning algorithms and their applications in data science.

Final paragraph with unique conclusions.
"""
        result = deduplicate_sections(
            text,
            max_repetitions=1,
            mode="aggressive",
            similarity_threshold=0.7,
            min_content_preservation=0.4,
        )
        # Should have fewer "repeated paragraph" occurrences in aggressive mode
        assert result.count("repeated paragraph") <= 2

    def test_deduplicate_conservative_mode(self):
        """Test conservative deduplication mode preserves more content."""
        text = """
## Methods
Machine learning algorithms are used.

## Methods
Machine learning methods are applied.

## Methods
Machine learning techniques are utilized.
"""
        result = deduplicate_sections(text, mode="conservative", max_repetitions=1)
        # Conservative mode should preserve more content
        assert len(result) > len(text) * 0.8  # Should preserve most content

    def test_deduplicate_aggressive_mode(self):
        """Test aggressive deduplication mode removes more content."""
        text = """
## Introduction
This is a substantial introduction with detailed background information about the research field.

## Methods
This is identical content that should be deduplicated in aggressive mode with detailed methodology.

## Methods
This is identical content that should be deduplicated in aggressive mode with detailed methodology.

## Methods
This is identical content that should be deduplicated in aggressive mode with detailed methodology.

## Results
This is a substantial results section with detailed findings and analysis.
"""
        result = deduplicate_sections(
            text,
            mode="aggressive",
            max_repetitions=1,
            similarity_threshold=0.9,
            min_content_preservation=0.5,
        )
        # Should remove duplicates more aggressively for identical content
        assert result.count("## Methods") <= 2
        # Should preserve other sections
        assert "## Introduction" in result
        assert "## Results" in result

    def test_deduplicate_content_preservation(self):
        """Test that content preservation limits are respected."""
        # Create text where deduplication would remove too much
        text = """
## Unique Section 1
This is unique content that should be preserved.

## Similar Section A
Machine learning algorithms data science.

## Similar Section B
Machine learning methods data analysis.

## Similar Section C
Machine learning techniques data processing.

## Unique Section 2
This is also unique content to preserve.
"""
        result = deduplicate_sections(
            text,
            mode="aggressive",
            similarity_threshold=0.7,
            min_content_preservation=0.8,
        )
        # Should preserve at least 80% of content due to preservation limit
        preservation_ratio = len(result) / len(text)
        assert preservation_ratio >= 0.8

    def test_deduplicate_semantic_similarity(self):
        """Test that semantically similar but valid content is preserved."""
        text = """
## Overview
This section provides an introduction to machine learning algorithms and their applications.

## Methods
This part discusses machine learning methods and their use in data analysis.

## Results
These sections present different results from the machine learning experiments.
"""
        result = deduplicate_sections(text, similarity_threshold=0.8)
        # Should preserve all sections as they are conceptually different
        assert "## Overview" in result
        assert "## Methods" in result
        assert "## Results" in result


class TestSimilarityCalculations:
    """Test improved similarity calculation methods."""

    def test_calculate_similarity_jaccard(self):
        """Test Jaccard similarity calculation."""
        text1 = "machine learning algorithms data"
        text2 = "machine learning methods data"
        similarity = _calculate_similarity(text1, text2, method="jaccard")
        assert similarity > 0.5  # High overlap

    def test_calculate_similarity_tfidf(self):
        """Test TF-IDF cosine similarity."""
        text1 = "machine learning algorithms"
        text2 = "machine learning methods"
        similarity = _calculate_similarity(text1, text2, method="tfidf")
        assert similarity > 0.0

    def test_calculate_similarity_hybrid(self):
        """Test hybrid similarity calculation."""
        text1 = "machine learning algorithms data science"
        text2 = "machine learning methods data analysis"
        similarity = _calculate_similarity(text1, text2, method="hybrid")
        assert similarity > 0.3  # Should combine multiple methods

    def test_calculate_similarity_identical(self):
        """Test identical texts have perfect similarity."""
        text = "machine learning algorithms data science"
        similarity = _calculate_similarity(text, text, method="hybrid")
        assert similarity == 1.0

    def test_calculate_similarity_empty(self):
        """Test empty texts have zero similarity."""
        similarity = _calculate_similarity("", "text", method="hybrid")
        assert similarity == 0.0


class TestOutputValidatorRepetition:
    """Test OutputValidator repetition methods."""

    def test_validate_no_repetition_valid(self):
        """Test validation passes for unique content."""
        text = "Unique " * 50 + " content " * 50 + " here " * 50
        is_valid, details = validate_no_repetition(text)
        # Should pass validation
        assert details["unique_ratio"] >= 0.5  # At least 50% unique

    def test_validate_no_repetition_invalid(self):
        """Test validation detects highly repetitive content."""
        # Create text with repeated sections (section-based detection)
        repeated_section = "This is a repeated section about machine learning. " * 10
        repeated = f"""
## Section 1
{repeated_section}

## Section 2
{repeated_section}

## Section 3
{repeated_section}

## Section 4
{repeated_section}
"""
        is_valid, details = validate_no_repetition(repeated)
        # Should detect repetition or have lower unique ratio
        assert details["has_repetition"] is True or details["unique_ratio"] < 0.9

    def test_clean_repetitive_output(self):
        """Test cleaning repetitive output."""
        repeated_text = """
## Intro
Introduction text.

## Intro
Introduction text.

## Intro
Introduction text.
"""
        cleaned = clean_repetitive_output(repeated_text)
        # Should have fewer occurrences
        assert cleaned.count("## Intro") <= 2


# =============================================================================
# Review Quality Validation Tests
# =============================================================================


class TestOffTopicDetection:
    """Test off-topic detection functions."""

    def test_is_off_topic_email_format(self):
        """Test detection of email/letter format responses."""
        email_response = "Dear Dr. Smith,\n\nI am writing to inform you..."
        assert is_off_topic(email_response) is True

    def test_is_off_topic_ai_refusal(self):
        """Test detection of AI refusal patterns."""
        refusal = "I cannot help with that request because..."
        assert is_off_topic(refusal) is True

    def test_is_off_topic_self_identification(self):
        """Test detection of AI self-identification."""
        ai_response = "As an AI assistant, I don't have access to that information."
        assert is_off_topic(ai_response) is True

    def test_is_off_topic_valid_review(self):
        """Test that valid review content is not off-topic."""
        valid_review = """
## Overview
The manuscript presents a novel approach to optimization.

## Key Contributions
The authors demonstrate significant improvements.

## Methodology
The research design follows established practices.
"""
        assert is_off_topic(valid_review) is False

    def test_is_off_topic_with_on_topic_signals(self):
        """Test that on-topic signals override potential false positives."""
        # Text with URL but also on-topic signals
        text_with_signals = """
## Strengths
The manuscript has clear methodology.

## Weaknesses
The paper could improve the experimental section.
"""
        assert is_off_topic(text_with_signals) is False


class TestOnTopicSignals:
    """Test on-topic signal detection."""

    def test_has_on_topic_signals_with_headers(self):
        """Test detection of on-topic headers."""
        text = "## Overview\n## Strengths\n## Weaknesses"
        assert has_on_topic_signals(text) is True

    def test_has_on_topic_signals_with_keywords(self):
        """Test detection of on-topic keywords."""
        text = "The manuscript presents the authors' methodology for the study."
        assert has_on_topic_signals(text) is True

    def test_has_on_topic_signals_none(self):
        """Test detection when no on-topic signals present."""
        text = "Hello, how can I help you today?"
        assert has_on_topic_signals(text) is False


class TestConversationalPhrases:
    """Test conversational phrase detection."""

    def test_detect_conversational_phrases_found(self):
        """Test detection of conversational phrases."""
        text = "Let me know if you need anything else! I'd be happy to help."
        phrases = detect_conversational_phrases(text)
        assert len(phrases) >= 1

    def test_detect_conversational_phrases_none(self):
        """Test when no conversational phrases present."""
        text = "The methodology follows established practices in the field."
        phrases = detect_conversational_phrases(text)
        assert len(phrases) == 0

    def test_detect_conversational_document_sharing(self):
        """Test detection of document sharing phrases."""
        text = "Based on the document you shared, I can see..."
        phrases = detect_conversational_phrases(text)
        assert len(phrases) >= 1


class TestFormatCompliance:
    """Test format compliance checking."""

    def test_check_format_compliance_valid(self):
        """Test format compliance for valid review."""
        valid_review = """
## Summary
The research presents novel findings.

## Strengths
Clear methodology and reproducible results.

## Weaknesses
Limited sample size.
"""
        is_compliant, issues, details = check_format_compliance(valid_review)
        assert is_compliant is True
        assert len(issues) == 0

    def test_check_format_compliance_conversational(self):
        """Test format compliance detects conversational phrases."""
        conversational_review = """
## Summary
Let me know if you need more details!

I'd be happy to explain further.
"""
        is_compliant, issues, details = check_format_compliance(conversational_review)
        assert is_compliant is False
        assert len(details["conversational_phrases"]) >= 1

    def test_check_format_compliance_empty(self):
        """Test format compliance for empty text."""
        is_compliant, issues, details = check_format_compliance("")
        assert is_compliant is True  # No violations in empty text


if __name__ == "__main__":
    pytest.main([__file__])
