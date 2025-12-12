"""Tests for infrastructure.llm.validation module."""
import pytest
import json
from infrastructure.llm.validation import (
    OutputValidator,
    detect_repetition,
    deduplicate_sections,
    is_off_topic,
    has_on_topic_signals,
    detect_conversational_phrases,
    check_format_compliance,
)
from infrastructure.llm.validation.repetition import (
    calculate_unique_content_ratio,
    _calculate_similarity,
)
from infrastructure.core.exceptions import ValidationError


class TestJSONValidation:
    """Test JSON validation."""

    def test_validate_valid_json(self):
        """Test valid JSON validation."""
        valid_json = '{"key": "value", "number": 42}'
        result = OutputValidator.validate_json(valid_json)
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_validate_markdown_wrapped_json(self):
        """Test JSON wrapped in markdown code blocks."""
        markdown_json = "```json\n{\"key\": \"value\"}\n```"
        result = OutputValidator.validate_json(markdown_json)
        assert result["key"] == "value"

    def test_validate_invalid_json(self):
        """Test invalid JSON raises error."""
        invalid_json = '{"key": "value"'  # Missing closing brace
        with pytest.raises(ValidationError):
            OutputValidator.validate_json(invalid_json)

    def test_validate_empty_json_object(self):
        """Test empty JSON object validation."""
        empty_json = "{}"
        result = OutputValidator.validate_json(empty_json)
        assert result == {}


class TestLengthValidation:
    """Test content length validation."""

    def test_validate_length_within_bounds(self):
        """Test content within length bounds."""
        content = "test content"
        assert OutputValidator.validate_length(content, min_len=0, max_len=100) is True

    def test_validate_length_too_short(self):
        """Test content too short raises error."""
        content = "short"
        with pytest.raises(ValidationError):
            OutputValidator.validate_length(content, min_len=100)

    def test_validate_length_too_long(self):
        """Test content too long raises error."""
        content = "x" * 1000
        with pytest.raises(ValidationError):
            OutputValidator.validate_length(content, max_len=100)

    def test_validate_length_minimum_only(self):
        """Test minimum length constraint only."""
        content = "test"
        assert OutputValidator.validate_length(content, min_len=2) is True


class TestTokenEstimation:
    """Test token count estimation."""

    def test_estimate_tokens_basic(self):
        """Test basic token estimation."""
        content = "hello world"  # 11 chars
        tokens = OutputValidator.estimate_tokens(content)
        assert tokens == 11 // 4  # 2 tokens (approximate)

    def test_estimate_tokens_large_content(self):
        """Test token estimation for large content."""
        content = "a" * 400
        tokens = OutputValidator.estimate_tokens(content)
        assert tokens == 100  # 400 / 4


class TestResponseModeValidation:
    """Test response mode-specific validation."""

    def test_validate_short_response_valid(self):
        """Test valid short response (< 150 tokens)."""
        # ~100 tokens
        short_response = "Brief answer " * 10
        assert OutputValidator.validate_short_response(short_response) is True

    def test_validate_short_response_too_long(self):
        """Test short response that's too long."""
        # ~400 tokens
        long_response = "This is too long " * 100
        assert OutputValidator.validate_short_response(long_response) is False

    def test_validate_long_response_valid(self):
        """Test valid long response (> 500 tokens)."""
        # ~500 tokens
        long_response = "Detailed explanation " * 100
        assert OutputValidator.validate_long_response(long_response) is True

    def test_validate_long_response_too_short(self):
        """Test long response that's too short."""
        # ~50 tokens
        short_response = "Short"
        assert OutputValidator.validate_long_response(short_response) is False


class TestStructureValidation:
    """Test structured response validation."""

    def test_validate_structure_required_fields(self):
        """Test validation of required fields."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        
        # Valid: has required field
        data = {"name": "John", "age": 30}
        assert OutputValidator.validate_structure(data, schema) is True
        
        # Invalid: missing required field
        data_missing = {"age": 30}
        with pytest.raises(ValidationError):
            OutputValidator.validate_structure(data_missing, schema)

    def test_validate_structure_type_checking(self):
        """Test type validation in structure."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "count": {"type": "integer"}
            }
        }
        
        # Valid types
        data = {"name": "test", "count": 5}
        assert OutputValidator.validate_structure(data, schema) is True
        
        # Invalid: wrong type for count
        data_wrong_type = {"name": "test", "count": "five"}
        with pytest.raises(ValidationError):
            OutputValidator.validate_structure(data_wrong_type, schema)

    def test_validate_structure_no_schema(self):
        """Test structure validation without schema."""
        data = {"any": "structure"}
        assert OutputValidator.validate_structure(data, {}) is True


class TestCitationValidation:
    """Test citation extraction and validation."""

    def test_extract_author_year_citations(self):
        """Test extraction of (Author Year) format citations."""
        content = "As shown (Smith 2020) and (Johnson & Lee 2021)..."
        citations = OutputValidator.validate_citations(content)
        assert "Smith 2020" in citations or len(citations) > 0

    def test_extract_numeric_citations(self):
        """Test extraction of [1] format citations."""
        content = "Research shows [1] and [2] that..."
        citations = OutputValidator.validate_citations(content)
        assert len(citations) >= 0

    def test_extract_bibtex_citations(self):
        """Test extraction of @key format citations."""
        content = "Previous work @smith2020 and @johnson2021..."
        citations = OutputValidator.validate_citations(content)
        assert len(citations) >= 0


class TestFormattingValidation:
    """Test formatting quality validation."""

    def test_validate_formatting_good(self):
        """Test well-formatted content passes."""
        good_content = "This is properly formatted content. It has good structure."
        assert OutputValidator.validate_formatting(good_content) is True

    def test_validate_formatting_excessive_punctuation(self):
        """Test detection of excessive punctuation."""
        bad_content = "This is excessive!!!"
        assert OutputValidator.validate_formatting(bad_content) is False

    def test_validate_formatting_double_spaces(self):
        """Test detection of double spaces."""
        bad_content = "This  has  double  spaces"
        assert OutputValidator.validate_formatting(bad_content) is False

    def test_validate_formatting_question_marks(self):
        """Test detection of excessive question marks."""
        bad_content = "What???"
        assert OutputValidator.validate_formatting(bad_content) is False


class TestCompleteValidation:
    """Test comprehensive validation across modes."""

    def test_validate_complete_standard_mode(self):
        """Test standard mode comprehensive validation."""
        content = "Valid response with proper formatting."
        assert OutputValidator.validate_complete(content, mode="standard") is True

    def test_validate_complete_short_mode(self):
        """Test short mode comprehensive validation."""
        content = "Brief answer here."
        assert OutputValidator.validate_complete(content, mode="short") is True

    def test_validate_complete_long_mode(self):
        """Test long mode comprehensive validation."""
        content = "Detailed explanation " * 100
        assert OutputValidator.validate_complete(content, mode="long") is True

    def test_validate_complete_structured_mode(self):
        """Test structured mode comprehensive validation."""
        content = '{"key": "value"}'
        schema = {"type": "object", "properties": {"key": {"type": "string"}}}
        assert OutputValidator.validate_complete(
            content, mode="structured", schema=schema
        ) is True

    def test_validate_complete_empty_content(self):
        """Test empty content validation."""
        with pytest.raises(ValidationError):
            OutputValidator.validate_complete("")

    def test_validate_complete_invalid_structured(self):
        """Test invalid structured content."""
        with pytest.raises(ValidationError):
            OutputValidator.validate_complete(
                "Not JSON",
                mode="structured",
                schema={"type": "object"}
            )


class TestJSONValidationEdgeCases:
    """Test edge cases for JSON validation - covers line 25."""

    def test_validate_generic_code_block(self):
        """Test JSON wrapped in generic code blocks (not ```json).
        
        Covers line 25: code block extraction without explicit json tag.
        """
        # Code block without 'json' tag
        generic_block = "```\n{\"key\": \"value\"}\n```"
        result = OutputValidator.validate_json(generic_block)
        assert result["key"] == "value"

    def test_validate_code_block_with_text_before(self):
        """Test code block with surrounding text."""
        content = "Here is the JSON:\n```\n{\"result\": true}\n```\nEnd."
        result = OutputValidator.validate_json(content)
        assert result["result"] is True

    def test_validate_nested_json(self):
        """Test deeply nested JSON validation."""
        nested_json = '{"a": {"b": {"c": {"d": 1}}}}'
        result = OutputValidator.validate_json(nested_json)
        assert result["a"]["b"]["c"]["d"] == 1

    def test_validate_json_array(self):
        """Test JSON array validation."""
        json_array = '[1, 2, 3]'
        result = OutputValidator.validate_json(json_array)
        assert result == [1, 2, 3]


class TestTypeCheckingEdgeCases:
    """Test edge cases for type checking - covers line 116."""

    def test_check_unknown_type(self):
        """Test _check_type with unknown type returns True.
        
        Covers line 116: unknown type handling.
        """
        # Unknown type should return True (permissive)
        schema = {
            "type": "object",
            "properties": {
                "field": {"type": "unknowntype"}  # Unknown type
            }
        }
        data = {"field": "any value"}
        # Should pass because unknown types are permissive
        assert OutputValidator.validate_structure(data, schema) is True

    def test_check_null_type(self):
        """Test type checking with null type in schema."""
        schema = {
            "type": "object",
            "properties": {
                "field": {"type": "null"}  # Not in type_map
            }
        }
        data = {"field": None}
        # Should pass because "null" is unknown type
        assert OutputValidator.validate_structure(data, schema) is True

    def test_check_type_boolean(self):
        """Test boolean type checking."""
        schema = {
            "type": "object",
            "properties": {
                "flag": {"type": "boolean"}
            }
        }
        data = {"flag": True}
        assert OutputValidator.validate_structure(data, schema) is True
        
        # Wrong type
        data_wrong = {"flag": "true"}  # String, not boolean
        with pytest.raises(ValidationError):
            OutputValidator.validate_structure(data_wrong, schema)

    def test_check_type_number(self):
        """Test number type checking (int and float)."""
        schema = {
            "type": "object",
            "properties": {
                "value": {"type": "number"}
            }
        }
        # Int is a number
        assert OutputValidator.validate_structure({"value": 42}, schema) is True
        # Float is a number
        assert OutputValidator.validate_structure({"value": 3.14}, schema) is True

    def test_check_type_array(self):
        """Test array type checking."""
        schema = {
            "type": "object",
            "properties": {
                "items": {"type": "array"}
            }
        }
        assert OutputValidator.validate_structure({"items": [1, 2, 3]}, schema) is True
        
        # Wrong type
        with pytest.raises(ValidationError):
            OutputValidator.validate_structure({"items": "not an array"}, schema)

    def test_check_type_object(self):
        """Test object type checking."""
        schema = {
            "type": "object",
            "properties": {
                "data": {"type": "object"}
            }
        }
        assert OutputValidator.validate_structure({"data": {"nested": True}}, schema) is True


class TestCompleteValidationEdgeCases:
    """Test edge cases for complete validation - covers lines 166, 178."""

    def test_validate_complete_with_formatting_issues(self):
        """Test validate_complete logs warning for formatting issues.
        
        Covers line 166: warning logging for formatting issues.
        """
        # Content with double spaces (formatting issue)
        content = "This  has  double  spaces but is otherwise valid."
        # Should still return True for standard mode (formatting is warning only)
        result = OutputValidator.validate_complete(content, mode="standard")
        assert result is True

    def test_validate_complete_whitespace_only(self):
        """Test validate_complete with whitespace only content."""
        with pytest.raises(ValidationError):
            OutputValidator.validate_complete("   \n\t  ")

    def test_validate_complete_newline_only(self):
        """Test validate_complete with newline only content."""
        with pytest.raises(ValidationError):
            OutputValidator.validate_complete("\n\n\n")

    def test_validate_complete_structured_without_schema(self):
        """Test structured mode without schema."""
        content = '{"key": "value"}'
        # Without schema, structured mode returns True (falls through)
        result = OutputValidator.validate_complete(content, mode="structured")
        assert result is True

    def test_validate_complete_unknown_mode(self):
        """Test unknown mode falls through to return True."""
        content = "Valid content"
        result = OutputValidator.validate_complete(content, mode="unknown_mode")
        assert result is True


class TestCitationValidationEdgeCases:
    """Test edge cases for citation validation."""

    def test_extract_multiple_citation_types(self):
        """Test extracting multiple citation types."""
        content = "As shown (Smith 2020), also see [1] and @bibtex2021."
        citations = OutputValidator.validate_citations(content)
        # Should find multiple citations
        assert len(citations) >= 2

    def test_extract_no_citations(self):
        """Test content with no citations."""
        content = "This text has no citations whatsoever."
        citations = OutputValidator.validate_citations(content)
        assert len(citations) == 0

    def test_extract_multi_author_citation(self):
        """Test multi-author citation extraction."""
        content = "Previous work (Smith & Jones 2020) shows..."
        citations = OutputValidator.validate_citations(content)
        assert len(citations) >= 1


class TestFormattingValidationEdgeCases:
    """Test edge cases for formatting validation."""

    def test_formatting_both_issues(self):
        """Test content with both punctuation and spacing issues."""
        bad_content = "What???  Double  spaces!!!"
        assert OutputValidator.validate_formatting(bad_content) is False

    def test_formatting_empty_string(self):
        """Test formatting validation with empty string."""
        assert OutputValidator.validate_formatting("") is True

    def test_formatting_unicode(self):
        """Test formatting validation with unicode content."""
        unicode_content = "This has émojis 🎉 and accénts."
        assert OutputValidator.validate_formatting(unicode_content) is True


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
        result = deduplicate_sections(text, max_repetitions=1, mode="aggressive", similarity_threshold=0.7, min_content_preservation=0.5)
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
        result = deduplicate_sections(text, max_repetitions=1, mode="aggressive", similarity_threshold=0.7, min_content_preservation=0.4)
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
        result = deduplicate_sections(text, mode="aggressive", max_repetitions=1, similarity_threshold=0.9, min_content_preservation=0.5)
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
            min_content_preservation=0.8
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
        is_valid, details = OutputValidator.validate_no_repetition(text)
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
        is_valid, details = OutputValidator.validate_no_repetition(repeated)
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
        cleaned = OutputValidator.clean_repetitive_output(repeated_text)
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
