"""Tests for infrastructure/llm/templates/manuscript.py.

Tests render happy-path for ManuscriptExecutiveSummary, ManuscriptQualityReview,
ManuscriptMethodologyReview, ManuscriptImprovementSuggestions, and
ManuscriptTranslationAbstract with a stub text string. No Ollama required.
"""

from __future__ import annotations

import pytest

from infrastructure.core.exceptions import LLMTemplateError
from infrastructure.llm.templates.manuscript import (
    ManuscriptExecutiveSummary,
    ManuscriptImprovementSuggestions,
    ManuscriptMethodologyReview,
    ManuscriptQualityReview,
    ManuscriptTranslationAbstract,
)

STUB_TEXT = "This is a sample research manuscript abstract for unit testing."


class TestManuscriptExecutiveSummary:
    def test_render_contains_stub_text(self):
        result = ManuscriptExecutiveSummary().render(text=STUB_TEXT)
        assert STUB_TEXT in result

    def test_render_contains_manuscript_delimiters(self):
        result = ManuscriptExecutiveSummary().render(text=STUB_TEXT)
        assert "MANUSCRIPT BEGIN" in result
        assert "MANUSCRIPT END" in result

    def test_render_missing_text_raises(self):
        with pytest.raises(LLMTemplateError, match="Missing template variable"):
            ManuscriptExecutiveSummary().render()


class TestManuscriptQualityReview:
    def test_render_contains_stub_text(self):
        result = ManuscriptQualityReview().render(text=STUB_TEXT)
        assert STUB_TEXT in result

    def test_render_contains_manuscript_delimiters(self):
        result = ManuscriptQualityReview().render(text=STUB_TEXT)
        assert "MANUSCRIPT BEGIN" in result
        assert "MANUSCRIPT END" in result

    def test_render_missing_text_raises(self):
        with pytest.raises(LLMTemplateError, match="Missing template variable"):
            ManuscriptQualityReview().render()


class TestManuscriptMethodologyReview:
    def test_render_contains_stub_text(self):
        result = ManuscriptMethodologyReview().render(text=STUB_TEXT)
        assert STUB_TEXT in result

    def test_render_contains_manuscript_delimiters(self):
        result = ManuscriptMethodologyReview().render(text=STUB_TEXT)
        assert "MANUSCRIPT BEGIN" in result
        assert "MANUSCRIPT END" in result

    def test_render_missing_text_raises(self):
        with pytest.raises(LLMTemplateError, match="Missing template variable"):
            ManuscriptMethodologyReview().render()


class TestManuscriptImprovementSuggestions:
    def test_render_contains_stub_text(self):
        result = ManuscriptImprovementSuggestions().render(text=STUB_TEXT)
        assert STUB_TEXT in result

    def test_render_missing_text_raises(self):
        with pytest.raises(LLMTemplateError, match="Missing template variable"):
            ManuscriptImprovementSuggestions().render()


class TestManuscriptTranslationAbstract:
    def test_template_str_non_empty(self):
        assert ManuscriptTranslationAbstract.template_str != ""

    def test_render_missing_target_language_raises(self):
        with pytest.raises(LLMTemplateError, match="Missing template variable"):
            ManuscriptTranslationAbstract().render()
