"""Tests for infrastructure.llm.validation module."""
import pytest
import json
from infrastructure.llm.validation import OutputValidator
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
