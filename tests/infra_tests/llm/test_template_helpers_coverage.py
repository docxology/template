"""Tests for infrastructure/llm/templates/helpers.py.

Covers: format_requirements, token_budget_awareness, content_requirements,
section_structure, validation_hints.

No mocks used -- all tests use real data and string operations.
"""

from __future__ import annotations

from infrastructure.llm.templates.helpers import (
    format_requirements,
    token_budget_awareness,
    content_requirements,
    section_structure,
    validation_hints,
)


class TestFormatRequirements:
    """Test format_requirements."""

    def test_basic_headers(self):
        result = format_requirements(["## Overview", "## Methods"])
        assert "FORMAT REQUIREMENTS:" in result
        assert "## Overview" in result
        assert "## Methods" in result

    def test_markdown_format_true(self):
        result = format_requirements(["## Intro"], markdown_format=True)
        assert "markdown formatting" in result

    def test_markdown_format_false(self):
        result = format_requirements(["## Intro"], markdown_format=False)
        assert "markdown formatting" not in result

    def test_section_requirements(self):
        result = format_requirements(
            ["## Results"],
            section_requirements={"Results": "minimum 200 words"},
        )
        assert "Results: minimum 200 words" in result

    def test_empty_headers(self):
        result = format_requirements([])
        assert "FORMAT REQUIREMENTS:" in result


class TestTokenBudgetAwareness:
    """Test token_budget_awareness."""

    def test_total_tokens(self):
        result = token_budget_awareness(total_tokens=2000)
        assert "TOKEN BUDGET AWARENESS:" in result
        assert "2000 tokens" in result

    def test_section_budgets(self):
        result = token_budget_awareness(
            section_budgets={"Overview": 500, "Methods": 800}
        )
        assert "Overview" in result
        assert "~500 tokens" in result

    def test_word_targets(self):
        result = token_budget_awareness(
            word_targets={"Summary": (100, 300)}
        )
        assert "Summary" in result
        assert "100-300 words" in result

    def test_all_options(self):
        result = token_budget_awareness(
            total_tokens=3000,
            section_budgets={"Intro": 500},
            word_targets={"Intro": (100, 200)},
        )
        assert "3000 tokens" in result
        assert "Intro" in result

    def test_no_options(self):
        result = token_budget_awareness()
        assert "TOKEN BUDGET AWARENESS:" in result


class TestContentRequirements:
    """Test content_requirements."""

    def test_all_defaults(self):
        result = content_requirements()
        assert "NO HALLUCINATION" in result
        assert "CITE SOURCES" in result
        assert "EVIDENCE-BASED" in result
        assert "NO META-COMMENTARY" in result

    def test_disable_hallucination(self):
        result = content_requirements(no_hallucination=False)
        assert "NO HALLUCINATION" not in result

    def test_disable_cite_sources(self):
        result = content_requirements(cite_sources=False)
        assert "CITE SOURCES" not in result

    def test_disable_evidence(self):
        result = content_requirements(evidence_based=False)
        assert "EVIDENCE-BASED" not in result

    def test_disable_meta_commentary(self):
        result = content_requirements(no_meta_commentary=False)
        assert "NO META-COMMENTARY" not in result

    def test_all_disabled(self):
        result = content_requirements(
            no_hallucination=False,
            cite_sources=False,
            evidence_based=False,
            no_meta_commentary=False,
        )
        assert result == "CONTENT QUALITY REQUIREMENTS:"


class TestSectionStructure:
    """Test section_structure."""

    def test_basic_sections(self):
        result = section_structure(["Overview", "Methods", "Results"])
        assert "SECTION STRUCTURE:" in result
        assert "1. Overview" in result
        assert "2. Methods" in result

    def test_required_order_true(self):
        result = section_structure(["A", "B"], required_order=True)
        assert "exact order" in result

    def test_required_order_false(self):
        result = section_structure(["A", "B"], required_order=False)
        assert "Include these sections" in result

    def test_with_descriptions(self):
        result = section_structure(
            ["Overview", "Methods"],
            section_descriptions={"Overview": "High-level summary"},
        )
        assert "Overview: High-level summary" in result

    def test_missing_description(self):
        result = section_structure(
            ["Overview"],
            section_descriptions={"Other": "desc"},
        )
        assert "1. Overview" in result


class TestValidationHints:
    """Test validation_hints."""

    def test_word_count_range(self):
        result = validation_hints(word_count_range=(200, 500))
        assert "VALIDATION HINTS" in result
        assert "200" in result
        assert "500" in result

    def test_required_elements(self):
        result = validation_hints(required_elements=["heading", "conclusion"])
        assert "heading" in result
        assert "conclusion" in result

    def test_format_checks(self):
        result = validation_hints(format_checks=["no emoji", "markdown headers"])
        assert "no emoji" in result
        assert "markdown headers" in result

    def test_all_options(self):
        result = validation_hints(
            word_count_range=(100, 200),
            required_elements=["intro"],
            format_checks=["valid markdown"],
        )
        assert "100" in result
        assert "intro" in result
        assert "valid markdown" in result

    def test_no_options(self):
        result = validation_hints()
        assert "VALIDATION HINTS" in result
