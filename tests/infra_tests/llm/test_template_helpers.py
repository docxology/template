"""Tests for infrastructure.llm.templates.helpers module.

Tests pure string-generating helper functions (No Mocks Policy).
"""

from __future__ import annotations

from infrastructure.llm.templates.helpers import (
    content_requirements,
    format_requirements,
    section_structure,
    token_budget_awareness,
    validation_hints,
)


class TestFormatRequirements:
    """Tests for format_requirements."""

    def test_returns_string(self):
        """Always returns a string."""
        result = format_requirements(["## Section 1", "## Section 2"])
        assert isinstance(result, str)

    def test_includes_header_lines(self):
        """Listed headers appear in output."""
        result = format_requirements(["## Introduction", "## Methods"])
        assert "## Introduction" in result
        assert "## Methods" in result

    def test_includes_format_label(self):
        """Output contains FORMAT REQUIREMENTS label."""
        result = format_requirements([])
        assert "FORMAT REQUIREMENTS" in result

    def test_section_requirements_included(self):
        """Section requirements appear when provided."""
        result = format_requirements(
            ["## Results"],
            section_requirements={"## Results": "Include tables"},
        )
        assert "Include tables" in result

    def test_no_section_requirements(self):
        """Works without section_requirements."""
        result = format_requirements(["## A"], section_requirements=None)
        assert "## A" in result


class TestTokenBudgetAwareness:
    """Tests for token_budget_awareness."""

    def test_returns_string(self):
        """Always returns a string."""
        result = token_budget_awareness()
        assert isinstance(result, str)

    def test_includes_total_tokens(self):
        """Total token budget appears in output."""
        result = token_budget_awareness(total_tokens=2000)
        assert "2000" in result

    def test_includes_section_budgets(self):
        """Section budgets appear in output."""
        result = token_budget_awareness(section_budgets={"Introduction": 300})
        assert "Introduction" in result
        assert "300" in result

    def test_includes_word_targets(self):
        """Word targets (min/max) appear in output."""
        result = token_budget_awareness(word_targets={"Abstract": (100, 200)})
        assert "Abstract" in result
        assert "100" in result
        assert "200" in result

    def test_empty_call(self):
        """No arguments returns minimal string."""
        result = token_budget_awareness()
        assert "TOKEN BUDGET" in result


class TestContentRequirements:
    """Tests for content_requirements."""

    def test_returns_string(self):
        """Always returns a string."""
        result = content_requirements()
        assert isinstance(result, str)

    def test_no_hallucination_included_by_default(self):
        """NO HALLUCINATION appears by default."""
        result = content_requirements()
        assert "NO HALLUCINATION" in result

    def test_no_hallucination_excluded(self):
        """NO HALLUCINATION excluded when flag is False."""
        result = content_requirements(no_hallucination=False)
        assert "NO HALLUCINATION" not in result

    def test_no_meta_commentary_included(self):
        """NO META-COMMENTARY appears by default."""
        result = content_requirements()
        assert "NO META-COMMENTARY" in result

    def test_all_false_returns_label_only(self):
        """All flags False returns only the section header."""
        result = content_requirements(
            no_hallucination=False,
            cite_sources=False,
            evidence_based=False,
            no_meta_commentary=False,
        )
        assert "CONTENT QUALITY REQUIREMENTS" in result
        assert "HALLUCINATION" not in result


class TestSectionStructure:
    """Tests for section_structure."""

    def test_returns_string(self):
        """Always returns a string."""
        result = section_structure(["Introduction", "Methods"])
        assert isinstance(result, str)

    def test_sections_listed(self):
        """All sections appear in output."""
        result = section_structure(["Introduction", "Results", "Discussion"])
        assert "Introduction" in result
        assert "Results" in result
        assert "Discussion" in result

    def test_section_descriptions_included(self):
        """Section descriptions appear when provided."""
        result = section_structure(
            ["Methods"],
            section_descriptions={"Methods": "Describe experimental setup"},
        )
        assert "Describe experimental setup" in result

    def test_required_order_flag(self):
        """required_order=False changes wording."""
        ordered = section_structure(["A"], required_order=True)
        unordered = section_structure(["A"], required_order=False)
        assert "exact order" in ordered
        assert "exact order" not in unordered


class TestValidationHints:
    """Tests for validation_hints."""

    def test_returns_string(self):
        """Always returns a string."""
        result = validation_hints()
        assert isinstance(result, str)

    def test_word_count_range(self):
        """Word count range appears in output."""
        result = validation_hints(word_count_range=(500, 1500))
        assert "500" in result
        assert "1500" in result

    def test_required_elements(self):
        """Required elements appear in output."""
        result = validation_hints(required_elements=["Executive summary", "References"])
        assert "Executive summary" in result
        assert "References" in result

    def test_format_checks(self):
        """Format checks appear in output."""
        result = validation_hints(format_checks=["No emoji in headings"])
        assert "No emoji in headings" in result

    def test_includes_validation_label(self):
        """Output always contains VALIDATION HINTS label."""
        result = validation_hints()
        assert "VALIDATION HINTS" in result
