"""Tests for infrastructure/llm/validation/structure.py.

Covers: validate_section_completeness, extract_structured_sections,
validate_response_structure.

No mocks used -- all tests use real data and computations.
"""

from __future__ import annotations

from infrastructure.llm.validation.structure import (
    validate_section_completeness,
    extract_structured_sections,
    validate_response_structure,
)


class TestValidateSectionCompleteness:
    """Test validate_section_completeness."""

    def test_all_headers_present(self):
        response = "## Overview\n\nContent.\n\n## Methods\n\nMore content."
        is_complete, missing, details = validate_section_completeness(
            response, ["## Overview", "## Methods"]
        )
        assert is_complete is True
        assert missing == []

    def test_missing_header(self):
        response = "## Overview\n\nContent."
        is_complete, missing, details = validate_section_completeness(
            response, ["## Overview", "## Methods"]
        )
        assert is_complete is False
        assert "## Methods" in missing

    def test_flexible_match(self):
        response = "# OVERVIEW\n\nContent about the overview."
        is_complete, missing, details = validate_section_completeness(
            response, ["## Overview"], flexible=True
        )
        assert is_complete is True

    def test_strict_match(self):
        response = "# overview\n\nContent."
        is_complete, missing, details = validate_section_completeness(
            response, ["## Overview"], flexible=False
        )
        assert is_complete is False

    def test_empty_response(self):
        is_complete, missing, details = validate_section_completeness(
            "", ["## Overview"]
        )
        assert is_complete is False

    def test_details_structure(self):
        response = "## Results\n\nData here."
        _, _, details = validate_section_completeness(
            response, ["## Results", "## Discussion"]
        )
        assert "required" in details
        assert "found" in details
        assert "missing" in details
        assert "## Discussion" in details["missing"]


class TestExtractStructuredSections:
    """Test extract_structured_sections."""

    def test_basic_extraction(self):
        response = "## Overview\n\nIntro content.\n\n## Methods\n\nMethod details."
        sections = extract_structured_sections(response)
        assert "Overview" in sections
        assert "Methods" in sections
        assert "Intro content." in sections["Overview"]

    def test_nested_headers(self):
        response = "# Main\n\nTop level.\n\n## Sub\n\nSub content.\n\n### Detail\n\nDetails."
        sections = extract_structured_sections(response)
        assert "Main" in sections
        assert "Sub" in sections
        assert "Detail" in sections

    def test_no_headers(self):
        response = "Just plain text without headers."
        sections = extract_structured_sections(response)
        assert sections == {}

    def test_empty_response(self):
        sections = extract_structured_sections("")
        assert sections == {}

    def test_header_with_content(self):
        response = "## Results\n\nLine 1.\nLine 2.\nLine 3."
        sections = extract_structured_sections(response)
        assert "Results" in sections
        assert "Line 1." in sections["Results"]
        assert "Line 3." in sections["Results"]


class TestValidateResponseStructure:
    """Test validate_response_structure."""

    def test_valid_response(self):
        response = "## Overview\n\n" + "word " * 100 + "\n\n## Methods\n\n" + "word " * 100
        is_valid, issues, details = validate_response_structure(
            response, ["## Overview", "## Methods"], min_word_count=50
        )
        assert is_valid is True
        assert issues == []

    def test_too_short(self):
        response = "## Overview\n\nShort."
        is_valid, issues, details = validate_response_structure(
            response, ["## Overview"], min_word_count=100
        )
        assert is_valid is False
        assert any("too short" in i.lower() for i in issues)

    def test_too_long(self):
        response = "## Overview\n\n" + "word " * 500
        is_valid, issues, details = validate_response_structure(
            response, ["## Overview"], max_word_count=100
        )
        assert is_valid is False
        assert any("too long" in i.lower() for i in issues)

    def test_missing_sections(self):
        response = "## Overview\n\n" + "word " * 50
        is_valid, issues, details = validate_response_structure(
            response, ["## Overview", "## Methods"], min_word_count=10
        )
        assert is_valid is False
        assert any("missing" in i.lower() for i in issues)

    def test_details_word_count(self):
        response = "## Overview\n\none two three four five"
        _, _, details = validate_response_structure(response, ["## Overview"])
        assert "word_count" in details
        assert details["word_count"] > 0

    def test_extracted_sections_in_details(self):
        response = "## Intro\n\nContent.\n\n## Results\n\nMore content."
        _, _, details = validate_response_structure(
            response, ["## Intro", "## Results"]
        )
        assert "extracted_sections" in details
        assert "Intro" in details["extracted_sections"]

    def test_flexible_headers(self):
        response = "# overview\n\n" + "word " * 50
        is_valid, issues, details = validate_response_structure(
            response, ["## Overview"], flexible_headers=True
        )
        assert is_valid is True
