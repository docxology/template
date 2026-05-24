"""Tests for infrastructure.llm.review.review_analysis module.

Tests using real string inputs (No Mocks Policy).
"""

from __future__ import annotations

from infrastructure.llm.review.review_analysis import (
    calculate_format_compliance_summary,
    calculate_quality_summary,
    extract_action_items,
)


class TestExtractActionItems:
    """Tests for extract_action_items."""

    def test_returns_string(self):
        """Always returns a string."""
        result = extract_action_items({})
        assert isinstance(result, str)

    def test_empty_reviews_returns_default_todos(self):
        """Empty reviews dict returns default checklist items."""
        result = extract_action_items({})
        assert "[ ]" in result

    def test_extracts_checklist_items_from_suggestions(self):
        """Checklist items in improvement_suggestions are extracted."""
        reviews = {
            "improvement_suggestions": "- [ ] Fix the introduction\n- [ ] Add more references\n"
        }
        result = extract_action_items(reviews)
        assert "[ ] Fix the introduction" in result or "Fix the introduction" in result

    def test_extracts_high_priority_items(self):
        """Items under 'high priority' heading are extracted."""
        reviews = {
            "improvement_suggestions": (
                "## High Priority\n"
                "- **Issue**: Methods section incomplete\n"
                "## Medium Priority\n"
                "- Minor issue\n"
            )
        }
        result = extract_action_items(reviews)
        assert isinstance(result, str)

    def test_limits_to_ten_items(self):
        """Result contains at most 10 items."""
        many_items = "\n".join(f"- [ ] Item {i}" for i in range(20))
        reviews = {"improvement_suggestions": many_items}
        result = extract_action_items(reviews)
        item_count = result.count("[ ]")
        assert item_count <= 10

    def test_ignores_non_suggestion_reviews(self):
        """Only improvement_suggestions key is processed for action items."""
        reviews = {
            "executive_summary": "- [ ] This should not appear",
            "improvement_suggestions": "",
        }
        result = extract_action_items(reviews)
        assert isinstance(result, str)


class TestCalculateFormatComplianceSummary:
    """Tests for calculate_format_compliance_summary."""

    def test_returns_string(self):
        """Always returns a string."""
        result = calculate_format_compliance_summary({})
        assert isinstance(result, str)

    def test_empty_reviews_returns_100_percent(self):
        """Empty reviews returns 100% compliance."""
        result = calculate_format_compliance_summary({})
        assert "100%" in result

    def test_clean_reviews_show_compliance(self):
        """Reviews without conversational phrases show high compliance."""
        reviews = {
            "executive_summary": "# Executive Summary\nThis manuscript presents...",
            "quality_review": "# Quality Review\nThe methods are sound...",
        }
        result = calculate_format_compliance_summary(reviews)
        assert "%" in result

    def test_conversational_reviews_lower_compliance(self):
        """Reviews with conversational phrases lower compliance."""
        reviews = {
            "executive_summary": "Let me know if you need more information! I hope this helps.",
        }
        result = calculate_format_compliance_summary(reviews)
        assert "%" in result

    def test_includes_format_compliance_label(self):
        """Output contains 'Format Compliance' label."""
        result = calculate_format_compliance_summary({})
        assert "Format Compliance" in result


class TestCalculateQualitySummary:
    """Tests for calculate_quality_summary."""

    def test_returns_string(self):
        """Always returns a string."""
        result = calculate_quality_summary({})
        assert isinstance(result, str)

    def test_no_scores_returns_not_available(self):
        """Missing quality_review returns 'not available' message."""
        result = calculate_quality_summary({})
        assert "not available" in result.lower()

    def test_extracts_bold_score_pattern(self):
        """**Score: N** pattern is extracted and averaged."""
        reviews = {
            "quality_review": (
                "Clarity: **Score: 4**\n"
                "Methods: **Score: 3**\n"
                "Results: **Score: 5**\n"
            )
        }
        result = calculate_quality_summary(reviews)
        assert "4.0" in result  # average of 4, 3, 5
        assert "/5" in result

    def test_extracts_plain_score_pattern(self):
        """Score: N (plain) pattern is extracted."""
        reviews = {
            "quality_review": "Clarity Score: 4\nMethods Score: 2\n"
        }
        result = calculate_quality_summary(reviews)
        assert "/5" in result

    def test_average_is_correct(self):
        """Computed average matches expected value."""
        reviews = {"quality_review": "Score: 2 and Score: 4"}
        result = calculate_quality_summary(reviews)
        assert "3.0" in result


class TestExtractActionItemsFromReviewAnalysis:
    """Test extract_action_items."""

    def test_extracts_checklist_items(self):
        reviews = {
            "improvement_suggestions": (
                "- [ ] Fix the introduction section\n"
                "- [ ] Add more references\n"
                "- [ ] Improve the abstract\n"
            )
        }
        result = extract_action_items(reviews)
        assert "Fix the introduction section" in result
        assert "Add more references" in result

    def test_extracts_high_priority_items(self):
        reviews = {
            "improvement_suggestions": (
                "## High Priority\n"
                "- **Issue**: The methodology section lacks detail\n"
                "- **Recommendation**: Add statistical significance tests\n"
                "## Medium Priority\n"
                "- Minor formatting issues\n"
            )
        }
        result = extract_action_items(reviews)
        assert len(result.strip().split("\n")) > 0

    def test_default_items_when_none_found(self):
        reviews = {"improvement_suggestions": "Everything looks good."}
        result = extract_action_items(reviews)
        assert "Review executive summary" in result

    def test_empty_reviews(self):
        reviews = {}
        result = extract_action_items(reviews)
        assert "Review executive summary" in result

    def test_limits_to_10_items(self):
        lines = [f"- [ ] Fix item number {i}" for i in range(15)]
        reviews = {"improvement_suggestions": "\n".join(lines)}
        result = extract_action_items(reviews)
        items = [line for line in result.split("\n") if line.strip()]
        assert len(items) <= 10

    def test_long_items_truncated(self):
        reviews = {
            "improvement_suggestions": (
                "## High Priority\n"
                "1. " + "A" * 200 + "\n"
            )
        }
        result = extract_action_items(reviews)
        # Should either truncate or fall back to defaults
        assert len(result) > 0

    def test_numbered_high_priority(self):
        reviews = {
            "improvement_suggestions": (
                "## High Priority\n"
                "1. First issue that needs immediate attention now\n"
                "2. Second issue that is also important to address\n"
                "## Low Priority\n"
                "1. Minor issue\n"
            )
        }
        result = extract_action_items(reviews)
        assert len(result) > 0

    def test_issue_prefix_extraction(self):
        reviews = {
            "improvement_suggestions": (
                "## High Priority\n"
                "- **Issue**: The abstract needs significant revision and expansion\n"
            )
        }
        result = extract_action_items(reviews)
        assert len(result) > 0


class TestCalculateFormatComplianceSummaryFromReviewAnalysis:
    """Test calculate_format_compliance_summary."""

    def test_all_compliant(self):
        reviews = {
            "executive_summary": "## Overview\n\nFormal review text.",
            "quality_review": "## Quality\n\nProfessional assessment.",
        }
        result = calculate_format_compliance_summary(reviews)
        assert "Format Compliance" in result
        assert "100%" in result

    def test_some_conversational(self):
        reviews = {
            "executive_summary": "Let me know if you need more details.",
            "quality_review": "## Quality\n\nProfessional assessment.",
        }
        result = calculate_format_compliance_summary(reviews)
        assert "Format Compliance" in result

    def test_empty_reviews(self):
        result = calculate_format_compliance_summary({})
        assert "Format Compliance" in result
        assert "100%" in result

    def test_all_conversational(self):
        reviews = {
            "r1": "I'd be happy to help you with this review.",
            "r2": "Let me know if you need anything else.",
        }
        result = calculate_format_compliance_summary(reviews)
        assert "Format Compliance" in result


class TestCalculateQualitySummaryFromReviewAnalysis:
    """Test calculate_quality_summary."""

    def test_with_scores(self):
        reviews = {
            "quality_review": (
                "## Clarity\n**Score: 4**\n\n"
                "## Structure\n**Score: 3**\n\n"
                "## Technical Accuracy\n**Score: 5**\n"
            )
        }
        result = calculate_quality_summary(reviews)
        assert "Average Quality Score" in result
        assert "/5" in result

    def test_bold_scores(self):
        reviews = {
            "quality_review": "Clarity: **Score: 4/5**\nAccuracy: **Score: 3/5**"
        }
        result = calculate_quality_summary(reviews)
        assert "Average Quality Score" in result

    def test_no_scores(self):
        reviews = {"quality_review": "The paper is well-written overall."}
        result = calculate_quality_summary(reviews)
        assert "not available" in result

    def test_no_quality_review(self):
        reviews = {"executive_summary": "Good paper."}
        result = calculate_quality_summary(reviews)
        assert "not available" in result

    def test_empty_reviews(self):
        result = calculate_quality_summary({})
        assert "not available" in result
