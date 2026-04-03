"""Tests for infrastructure/llm/templates/manuscript_reviews.py.

Covers: ManuscriptExecutiveSummary.render, ManuscriptQualityReview.render.

No mocks used -- all tests use real template rendering with string data.
"""

from __future__ import annotations

import pytest

from infrastructure.core.exceptions import LLMTemplateError
from infrastructure.llm.templates.manuscript_reviews import (
    ManuscriptExecutiveSummary,
    ManuscriptQualityReview,
)


class TestManuscriptExecutiveSummary:
    """Test ManuscriptExecutiveSummary template."""

    def test_basic_render(self):
        template = ManuscriptExecutiveSummary()
        result = template.render(text="This is a test manuscript about climate science.")
        assert "test manuscript" in result
        assert "MANUSCRIPT BEGIN" in result

    def test_render_with_max_tokens(self):
        template = ManuscriptExecutiveSummary()
        result = template.render(text="Test manuscript content.", max_tokens=2000)
        assert "test manuscript" in result.lower()

    def test_render_no_text_raises(self):
        template = ManuscriptExecutiveSummary()
        with pytest.raises(LLMTemplateError):
            template.render(text=None)

    def test_render_text_in_kwargs_raises(self):
        template = ManuscriptExecutiveSummary()
        with pytest.raises(LLMTemplateError):
            template.render(text=None, text_kwarg="This is text")

    def test_format_requirements_in_output(self):
        template = ManuscriptExecutiveSummary()
        result = template.render(text="Manuscript content here.")
        assert "FORMAT REQUIREMENTS" in result or "SECTION STRUCTURE" in result


class TestManuscriptQualityReview:
    """Test ManuscriptQualityReview template."""

    def test_basic_render(self):
        template = ManuscriptQualityReview()
        result = template.render(text="This manuscript presents novel findings in biology.")
        assert "manuscript" in result.lower()
        assert "MANUSCRIPT BEGIN" in result

    def test_render_with_max_tokens(self):
        template = ManuscriptQualityReview()
        result = template.render(text="Test content.", max_tokens=3000)
        assert "test content" in result.lower()

    def test_render_no_text_raises(self):
        template = ManuscriptQualityReview()
        with pytest.raises(LLMTemplateError):
            template.render(text=None)

    def test_includes_scoring_structure(self):
        template = ManuscriptQualityReview()
        result = template.render(text="Paper content.")
        # Should include section headers for quality review
        assert "Quality Score" in result or "SECTION STRUCTURE" in result
