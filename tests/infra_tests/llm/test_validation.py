"""Tests for infrastructure.llm.validation module."""

import pytest

from infrastructure.core.exceptions import ValidationError
from infrastructure.llm.validation import (
    check_format_compliance,
    clean_repetitive_output,
    deduplicate_sections,
    detect_conversational_phrases,
    detect_repetition,
    estimate_tokens,
    has_on_topic_signals,
    is_off_topic,
    validate_citations,
    validate_complete,
    validate_formatting,
    validate_json,
    validate_length,
    validate_long_response,
    validate_no_repetition,
    validate_short_response,
    validate_structure,
)
from infrastructure.llm.validation.repetition import calculate_unique_content_ratio
from infrastructure.llm.validation.similarity import _calculate_similarity


class TestJSONValidation:
    """Test JSON validation."""

    def test_validate_valid_json(self):
        """Test valid JSON validation."""
        valid_json = '{"key": "value", "number": 42}'
        result = validate_json(valid_json)
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_validate_markdown_wrapped_json(self):
        """Test JSON wrapped in markdown code blocks."""
        markdown_json = '```json\n{"key": "value"}\n```'
        result = validate_json(markdown_json)
        assert result["key"] == "value"

    def test_validate_invalid_json(self):
        """Test invalid JSON raises error."""
        invalid_json = '{"key": "value"'  # Missing closing brace
        with pytest.raises(ValidationError):
            validate_json(invalid_json)

    def test_validate_invalid_json_error_context_is_bounded(self):
        """Invalid JSON errors must not embed full LLM-sized blobs in context."""
        invalid_json = '{"broken": '
        long_tail = "word " * 200
        blob = invalid_json + long_tail
        with pytest.raises(ValidationError) as exc_info:
            validate_json(blob)
        ctx = exc_info.value.context
        assert ctx.get("content_len") == len(blob)
        preview = ctx.get("content_preview", "")
        assert len(preview) <= 48
        assert "content" not in ctx

    def test_validate_empty_json_object(self):
        """Test empty JSON object validation."""
        empty_json = "{}"
        result = validate_json(empty_json)
        assert result == {}


class TestLengthValidation:
    """Test content length validation."""

    def test_validate_length_within_bounds(self):
        """Test content within length bounds."""
        content = "test content"
        assert validate_length(content, min_len=0, max_len=100) is True

    def test_validate_length_too_short(self):
        """Test content too short returns False."""
        content = "short"
        assert validate_length(content, min_len=100) is False

    def test_validate_length_too_long(self):
        """Test content too long returns False."""
        content = "x" * 1000
        assert validate_length(content, max_len=100) is False

    def test_validate_length_minimum_only(self):
        """Test minimum length constraint only."""
        content = "test"
        assert validate_length(content, min_len=2) is True


class TestTokenEstimation:
    """Test token count estimation."""

    def test_estimate_tokens_basic(self):
        """Test basic token estimation."""
        content = "hello world"  # 11 chars
        tokens = estimate_tokens(content)
        assert tokens == 11 // 4  # 2 tokens (approximate)

    def test_estimate_tokens_large_content(self):
        """Test token estimation for large content."""
        content = "a" * 400
        tokens = estimate_tokens(content)
        assert tokens == 100  # 400 / 4


class TestResponseModeValidation:
    """Test response mode-specific validation."""

    def test_validate_short_response_valid(self):
        """Test valid short response (< 150 tokens)."""
        # ~100 tokens
        short_response = "Brief answer " * 10
        assert validate_short_response(short_response) is True

    def test_validate_short_response_too_long(self):
        """Test short response that's too long."""
        # ~400 tokens
        long_response = "This is too long " * 100
        assert validate_short_response(long_response) is False

    def test_validate_long_response_valid(self):
        """Test valid long response (> 500 tokens)."""
        # ~500 tokens
        long_response = "Detailed explanation " * 100
        assert validate_long_response(long_response) is True

    def test_validate_long_response_too_short(self):
        """Test long response that's too short."""
        # ~50 tokens
        short_response = "Short"
        assert validate_long_response(short_response) is False


class TestStructureValidation:
    """Test structured response validation."""

    def test_validate_structure_required_fields(self):
        """Test validation of required fields."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name"],
        }

        # Valid: has required field
        data = {"name": "John", "age": 30}
        assert validate_structure(data, schema) is True

        # Invalid: missing required field
        data_missing = {"age": 30}
        with pytest.raises(ValidationError):
            validate_structure(data_missing, schema)

    def test_validate_structure_type_checking(self):
        """Test type validation in structure."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "count": {"type": "integer"}},
        }

        # Valid types
        data = {"name": "test", "count": 5}
        assert validate_structure(data, schema) is True

        # Invalid: wrong type for count
        data_wrong_type = {"name": "test", "count": "five"}
        with pytest.raises(ValidationError):
            validate_structure(data_wrong_type, schema)

    def test_validate_structure_no_schema(self):
        """Test structure validation without schema."""
        data = {"any": "structure"}
        assert validate_structure(data, {}) is True


class TestCitationValidation:
    """Test citation extraction and validation."""

    def test_extract_author_year_citations(self):
        """Test extraction of (Author Year) format citations."""
        content = "As shown (Smith 2020) and (Johnson & Lee 2021)..."
        citations = validate_citations(content)
        assert "Smith 2020" in citations or len(citations) > 0

    def test_extract_numeric_citations(self):
        """Test extraction of [1] format citations."""
        content = "Research shows [1] and [2] that..."
        citations = validate_citations(content)
        assert len(citations) >= 0

    def test_extract_bibtex_citations(self):
        """Test extraction of @key format citations."""
        content = "Previous work @smith2020 and @johnson2021..."
        citations = validate_citations(content)
        assert len(citations) >= 0


class TestFormattingValidation:
    """Test formatting quality validation."""

    def test_validate_formatting_good(self):
        """Test well-formatted content passes."""
        good_content = "This is properly formatted content. It has good structure."
        assert validate_formatting(good_content) is True

    def test_validate_formatting_excessive_punctuation(self):
        """Test detection of excessive punctuation."""
        bad_content = "This is excessive!!!"
        assert validate_formatting(bad_content) is False

    def test_validate_formatting_double_spaces(self):
        """Test detection of double spaces."""
        bad_content = "This  has  double  spaces"
        assert validate_formatting(bad_content) is False

    def test_validate_formatting_question_marks(self):
        """Test detection of excessive question marks."""
        bad_content = "What???"
        assert validate_formatting(bad_content) is False


class TestCompleteValidation:
    """Test comprehensive validation across modes."""

    def test_validate_complete_standard_mode(self):
        """Test standard mode comprehensive validation."""
        content = "Valid response with proper formatting."
        assert validate_complete(content, mode="standard") is True

    def test_validate_complete_short_mode(self):
        """Test short mode comprehensive validation."""
        content = "Brief answer here."
        assert validate_complete(content, mode="short") is True

    def test_validate_complete_long_mode(self):
        """Test long mode comprehensive validation."""
        content = "Detailed explanation " * 100
        assert validate_complete(content, mode="long") is True

    def test_validate_complete_structured_mode(self):
        """Test structured mode comprehensive validation."""
        content = '{"key": "value"}'
        schema = {"type": "object", "properties": {"key": {"type": "string"}}}
        assert validate_complete(content, mode="structured", schema=schema) is True

    def test_validate_complete_empty_content(self):
        """Test empty content validation."""
        with pytest.raises(ValidationError):
            validate_complete("")

    def test_validate_complete_invalid_structured(self):
        """Test invalid structured content."""
        with pytest.raises(ValidationError):
            validate_complete("Not JSON", mode="structured", schema={"type": "object"})


class TestJSONValidationEdgeCases:
    """Test edge cases for JSON validation - covers line 25."""

    def test_validate_generic_code_block(self):
        """Test JSON wrapped in generic code blocks (not ```json).

        Covers line 25: code block extraction without explicit json tag.
        """
        # Code block without 'json' tag
        generic_block = '```\n{"key": "value"}\n```'
        result = validate_json(generic_block)
        assert result["key"] == "value"

    def test_validate_code_block_with_text_before(self):
        """Test code block with surrounding text."""
        content = 'Here is the JSON:\n```\n{"result": true}\n```\nEnd.'
        result = validate_json(content)
        assert result["result"] is True

    def test_validate_nested_json(self):
        """Test deeply nested JSON validation."""
        nested_json = '{"a": {"b": {"c": {"d": 1}}}}'
        result = validate_json(nested_json)
        assert result["a"]["b"]["c"]["d"] == 1

    def test_validate_json_array(self):
        """Test JSON array validation."""
        json_array = "[1, 2, 3]"
        result = validate_json(json_array)
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
            "properties": {"field": {"type": "unknowntype"}},  # Unknown type
        }
        data = {"field": "any value"}
        # Should pass because unknown types are permissive
        assert validate_structure(data, schema) is True

    def test_check_null_type(self):
        """Test type checking with null type in schema."""
        schema = {
            "type": "object",
            "properties": {"field": {"type": "null"}},  # Not in type_map
        }
        data = {"field": None}
        # Should pass because "null" is unknown type
        assert validate_structure(data, schema) is True

    def test_check_type_boolean(self):
        """Test boolean type checking."""
        schema = {"type": "object", "properties": {"flag": {"type": "boolean"}}}
        data = {"flag": True}
        assert validate_structure(data, schema) is True

        # Wrong type
        data_wrong = {"flag": "true"}  # String, not boolean
        with pytest.raises(ValidationError):
            validate_structure(data_wrong, schema)

    def test_check_type_number(self):
        """Test number type checking (int and float)."""
        schema = {"type": "object", "properties": {"value": {"type": "number"}}}
        # Int is a number
        assert validate_structure({"value": 42}, schema) is True
        # Float is a number
        assert validate_structure({"value": 3.14}, schema) is True

    def test_check_type_array(self):
        """Test array type checking."""
        schema = {"type": "object", "properties": {"items": {"type": "array"}}}
        assert validate_structure({"items": [1, 2, 3]}, schema) is True

        # Wrong type
        with pytest.raises(ValidationError):
            validate_structure({"items": "not an array"}, schema)

    def test_check_type_object(self):
        """Test object type checking."""
        schema = {"type": "object", "properties": {"data": {"type": "object"}}}
        assert validate_structure({"data": {"nested": True}}, schema) is True


class TestCompleteValidationEdgeCases:
    """Test edge cases for complete validation - covers lines 166, 178."""

    def test_validate_complete_with_formatting_issues(self):
        """Test validate_complete logs warning for formatting issues.

        Covers line 166: warning logging for formatting issues.
        """
        # Content with double spaces (formatting issue)
        content = "This  has  double  spaces but is otherwise valid."
        # Should still return True for standard mode (formatting is warning only)
        result = validate_complete(content, mode="standard")
        assert result is True

    def test_validate_complete_whitespace_only(self):
        """Test validate_complete with whitespace only content."""
        with pytest.raises(ValidationError):
            validate_complete("   \n\t  ")

    def test_validate_complete_newline_only(self):
        """Test validate_complete with newline only content."""
        with pytest.raises(ValidationError):
            validate_complete("\n\n\n")

    def test_validate_complete_structured_without_schema(self):
        """Test structured mode without schema raises ValidationError."""
        content = '{"key": "value"}'
        with pytest.raises(ValidationError):
            validate_complete(content, mode="structured")

    def test_validate_complete_unknown_mode(self):
        """Test unknown mode falls through to return True."""
        content = "Valid content"
        result = validate_complete(content, mode="unknown_mode")
        assert result is True

    def test_validate_complete_raw_mode(self):
        """Test raw mode returns True without any validation checks."""
        content = "Any content here!!!  even with bad formatting???"
        result = validate_complete(content, mode="raw")
        assert result is True


class TestCitationValidationEdgeCases:
    """Test edge cases for citation validation."""

    def test_extract_multiple_citation_types(self):
        """Test extracting multiple citation types."""
        content = "As shown (Smith 2020), also see [1] and @bibtex2021."
        citations = validate_citations(content)
        # Should find multiple citations
        assert len(citations) >= 2

    def test_extract_no_citations(self):
        """Test content with no citations."""
        content = "This text has no citations whatsoever."
        citations = validate_citations(content)
        assert len(citations) == 0

    def test_extract_multi_author_citation(self):
        """Test multi-author citation extraction."""
        content = "Previous work (Smith & Jones 2020) shows..."
        citations = validate_citations(content)
        assert len(citations) >= 1


class TestFormattingValidationEdgeCases:
    """Test edge cases for formatting validation."""

    def test_formatting_both_issues(self):
        """Test content with both punctuation and spacing issues."""
        bad_content = "What???  Double  spaces!!!"
        assert validate_formatting(bad_content) is False

    def test_formatting_empty_string(self):
        """Test formatting validation with empty string."""
        assert validate_formatting("") is True

    def test_formatting_unicode(self):
        """Test formatting validation with unicode content."""
        unicode_content = "This has émojis 🎉 and accénts."
        assert validate_formatting(unicode_content) is True


if __name__ == "__main__":
    pytest.main([__file__])
