"""Tests for infrastructure/llm/templates/manuscript_suggestions.py.

Covers: ManuscriptMethodologyReview.render, ManuscriptImprovementSuggestions.render.

No mocks used -- all tests use real template rendering with string data.
"""

from __future__ import annotations

import pytest

from infrastructure.core.exceptions import LLMTemplateError
from infrastructure.llm.templates.manuscript_suggestions import (
    ManuscriptMethodologyReview,
    ManuscriptImprovementSuggestions,
)


class TestManuscriptMethodologyReview:
    """Test ManuscriptMethodologyReview template."""

    def test_basic_render(self):
        template = ManuscriptMethodologyReview()
        result = template.render(text="Our study used a randomized controlled trial design.")
        assert "randomized" in result.lower()
        assert "MANUSCRIPT" in result

    def test_render_with_max_tokens(self):
        template = ManuscriptMethodologyReview()
        result = template.render(text="Study methodology.", max_tokens=2000)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_no_text_raises(self):
        template = ManuscriptMethodologyReview()
        with pytest.raises(LLMTemplateError):
            template.render(text=None)


class TestManuscriptImprovementSuggestions:
    """Test ManuscriptImprovementSuggestions template."""

    def test_basic_render(self):
        template = ManuscriptImprovementSuggestions()
        result = template.render(text="This paper explores machine learning applications.")
        assert "machine learning" in result.lower()

    def test_render_with_max_tokens(self):
        template = ManuscriptImprovementSuggestions()
        result = template.render(text="Paper content.", max_tokens=3000)
        assert isinstance(result, str)

    def test_render_no_text_raises(self):
        template = ManuscriptImprovementSuggestions()
        with pytest.raises(LLMTemplateError):
            template.render(text=None)
