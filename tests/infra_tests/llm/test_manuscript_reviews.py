"""Tests for infrastructure.llm.templates.manuscript_reviews."""

import pytest

from infrastructure.core.exceptions import LLMTemplateError
from infrastructure.llm.templates.manuscript_reviews import (
    ManuscriptExecutiveSummary,
    ManuscriptQualityReview,
)


class TestManuscriptExecutiveSummary:
    def test_render_basic(self):
        t = ManuscriptExecutiveSummary()
        result = t.render(text="This is a test manuscript about quantum computing.")
        assert "MANUSCRIPT BEGIN" in result
        assert "quantum computing" in result
        assert "MANUSCRIPT END" in result
        assert "executive summary" in result.lower()

    def test_render_with_max_tokens(self):
        t = ManuscriptExecutiveSummary()
        result = t.render(text="Some manuscript text.", max_tokens=500)
        assert "MANUSCRIPT BEGIN" in result

    def test_render_text_as_kwarg(self):
        t = ManuscriptExecutiveSummary()
        result = t.render(text="Kwargs manuscript text.")
        assert "Kwargs manuscript text" in result

    def test_render_no_text_raises(self):
        t = ManuscriptExecutiveSummary()
        with pytest.raises(LLMTemplateError, match="Missing template variable"):
            t.render()

    def test_render_includes_sections(self):
        t = ManuscriptExecutiveSummary()
        result = t.render(text="Test manuscript content.")
        assert "Overview" in result
        assert "Key Contributions" in result
        assert "Methodology" in result
        assert "Principal Results" in result
        assert "Significance" in result


class TestManuscriptQualityReview:
    def test_render_basic(self):
        t = ManuscriptQualityReview()
        result = t.render(text="A manuscript about machine learning techniques.")
        assert "MANUSCRIPT BEGIN" in result
        assert "machine learning" in result
        assert "quality review" in result.lower()

    def test_render_with_max_tokens(self):
        t = ManuscriptQualityReview()
        result = t.render(text="Manuscript.", max_tokens=700)
        assert "MANUSCRIPT BEGIN" in result

    def test_render_no_text_raises(self):
        t = ManuscriptQualityReview()
        with pytest.raises(LLMTemplateError, match="Missing template variable"):
            t.render()

    def test_render_includes_quality_sections(self):
        t = ManuscriptQualityReview()
        result = t.render(text="Test manuscript.")
        assert "Overall Quality Score" in result
        assert "Clarity" in result
        assert "Structure" in result
        assert "Technical Accuracy" in result
        assert "Readability" in result
        assert "Specific Issues" in result
        assert "Recommendations" in result

    def test_render_text_as_kwarg(self):
        t = ManuscriptQualityReview()
        result = t.render(text="Kwargs text.")
        assert "Kwargs text" in result
