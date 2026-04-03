"""Tests for infrastructure.llm.validation.structure module.

Tests section completeness validation, structured section extraction,
and comprehensive response structure validation.
"""

from __future__ import annotations


from infrastructure.llm.validation.structure import (
    extract_structured_sections,
    validate_response_structure,
    validate_section_completeness,
)


class TestValidateSectionCompleteness:
    """Tests for validate_section_completeness."""

    def test_all_sections_present_exact_match(self):
        response = "## Overview\nSome content\n## Results\nMore content"
        headers = ["## Overview", "## Results"]
        is_complete, missing, details = validate_section_completeness(response, headers)
        assert is_complete is True
        assert missing == []
        assert len(details["found"]) == 2
        assert len(details["missing"]) == 0

    def test_missing_section(self):
        response = "## Overview\nSome content"
        headers = ["## Overview", "## Results"]
        is_complete, missing, details = validate_section_completeness(response, headers)
        assert is_complete is False
        assert "## Results" in missing
        assert len(details["missing"]) == 1

    def test_all_sections_missing(self):
        response = "Just some plain text without headers"
        headers = ["## Overview", "## Results"]
        is_complete, missing, details = validate_section_completeness(response, headers)
        assert is_complete is False
        assert len(missing) == 2

    def test_flexible_matching_case_insensitive(self):
        response = "# OVERVIEW\nSome content\n# RESULTS\nMore content"
        headers = ["## Overview", "## Results"]
        is_complete, missing, details = validate_section_completeness(
            response, headers, flexible=True
        )
        assert is_complete is True
        assert len(missing) == 0

    def test_strict_matching_no_flexible(self):
        response = "# OVERVIEW\nSome content"
        headers = ["## Overview"]
        is_complete, missing, details = validate_section_completeness(
            response, headers, flexible=False
        )
        assert is_complete is False
        assert "## Overview" in missing

    def test_empty_response(self):
        is_complete, missing, details = validate_section_completeness(
            "", ["## Overview"]
        )
        assert is_complete is False
        assert len(missing) == 1

    def test_empty_required_headers(self):
        is_complete, missing, details = validate_section_completeness(
            "Some content", []
        )
        assert is_complete is True
        assert missing == []

    def test_details_structure(self):
        response = "## Found\ncontent\n## Also Found\ncontent"
        headers = ["## Found", "## Missing"]
        _, _, details = validate_section_completeness(response, headers)
        assert "required" in details
        assert "found" in details
        assert "missing" in details
        assert details["required"] == headers

    def test_flexible_match_with_different_header_level(self):
        response = "### Overview\nSome content"
        headers = ["## Overview"]
        is_complete, missing, details = validate_section_completeness(
            response, headers, flexible=True
        )
        assert is_complete is True


class TestExtractStructuredSections:
    """Tests for extract_structured_sections."""

    def test_basic_extraction(self):
        response = "## Overview\nOverview content\n## Results\nResults content"
        sections = extract_structured_sections(response)
        assert "Overview" in sections
        assert "Results" in sections
        assert sections["Overview"] == "Overview content"
        assert sections["Results"] == "Results content"

    def test_nested_headers(self):
        response = "# Main\nMain content\n## Sub\nSub content\n### Deep\nDeep content"
        sections = extract_structured_sections(response)
        assert "Main" in sections
        assert "Sub" in sections
        assert "Deep" in sections

    def test_multiline_content(self):
        response = "## Section\nLine 1\nLine 2\nLine 3"
        sections = extract_structured_sections(response)
        assert "Section" in sections
        assert "Line 1\nLine 2\nLine 3" == sections["Section"]

    def test_empty_response(self):
        sections = extract_structured_sections("")
        assert sections == {}

    def test_no_headers(self):
        sections = extract_structured_sections("Just plain text\nno headers here")
        assert sections == {}

    def test_content_before_first_header_ignored(self):
        response = "Preamble text\n## Section\nActual content"
        sections = extract_structured_sections(response)
        assert len(sections) == 1
        assert "Section" in sections

    def test_empty_section(self):
        response = "## Empty\n## Next\nContent here"
        sections = extract_structured_sections(response)
        assert sections["Empty"] == ""
        assert sections["Next"] == "Content here"

    def test_header_with_special_chars(self):
        response = "## Section (v2.0)\nContent"
        sections = extract_structured_sections(response)
        assert "Section (v2.0)" in sections


class TestValidateResponseStructure:
    """Tests for validate_response_structure."""

    def test_valid_response(self):
        response = "## Overview\nSome content here with enough words\n## Results\nMore results content here"
        headers = ["## Overview", "## Results"]
        is_valid, issues, details = validate_response_structure(response, headers)
        assert is_valid is True
        assert issues == []

    def test_missing_sections_reported(self):
        response = "## Overview\nSome content"
        headers = ["## Overview", "## Results"]
        is_valid, issues, details = validate_response_structure(response, headers)
        assert is_valid is False
        assert any("Missing required sections" in i for i in issues)

    def test_too_short_response(self):
        response = "## Overview\nShort"
        is_valid, issues, details = validate_response_structure(
            response, ["## Overview"], min_word_count=100
        )
        assert is_valid is False
        assert any("too short" in i for i in issues)

    def test_too_long_response(self):
        response = "## Overview\n" + " ".join(["word"] * 200)
        is_valid, issues, details = validate_response_structure(
            response, ["## Overview"], max_word_count=50
        )
        assert is_valid is False
        assert any("too long" in i for i in issues)

    def test_word_count_in_details(self):
        response = "## Overview\nOne two three four five"
        _, _, details = validate_response_structure(response, ["## Overview"])
        assert "word_count" in details
        assert details["word_count"] > 0

    def test_extracted_sections_in_details(self):
        response = "## Overview\nContent\n## Methods\nContent"
        _, _, details = validate_response_structure(
            response, ["## Overview", "## Methods"]
        )
        assert "extracted_sections" in details
        assert "Overview" in details["extracted_sections"]
        assert "Methods" in details["extracted_sections"]

    def test_no_word_count_constraints(self):
        response = "## Overview\nContent"
        is_valid, issues, details = validate_response_structure(
            response, ["## Overview"]
        )
        assert is_valid is True

    def test_flexible_headers_default(self):
        response = "# OVERVIEW\nContent"
        is_valid, issues, details = validate_response_structure(
            response, ["## Overview"]
        )
        assert is_valid is True

    def test_strict_headers(self):
        response = "# OVERVIEW\nContent"
        is_valid, issues, details = validate_response_structure(
            response, ["## Overview"], flexible_headers=False
        )
        assert is_valid is False

    def test_multiple_issues(self):
        response = "short"
        is_valid, issues, _ = validate_response_structure(
            response, ["## Overview", "## Results"], min_word_count=100
        )
        assert is_valid is False
        assert len(issues) >= 2  # too short + missing sections
