"""Tests for infrastructure.llm.templates.manuscript_reviews."""

from __future__ import annotations

import pytest

from infrastructure.core.exceptions import LLMTemplateError
from infrastructure.llm.templates.manuscript_reviews import (
    ManuscriptExecutiveSummary,
    ManuscriptQualityReview,
)


@pytest.mark.parametrize(
    "template_cls",
    [ManuscriptExecutiveSummary, ManuscriptQualityReview],
)
class TestManuscriptReviewTemplates:
    def test_render_basic(self, template_cls):
        template = template_cls()
        text = (
            "This is a test manuscript about quantum computing."
            if template_cls is ManuscriptExecutiveSummary
            else "This manuscript discusses novel methods."
        )
        result = template.render(text=text)
        assert "MANUSCRIPT BEGIN" in result
        assert text.split()[0] in result
        if template_cls is ManuscriptExecutiveSummary:
            assert "MANUSCRIPT END" in result
            assert "executive summary" in result.lower()
        else:
            assert "quality review" in result.lower() or "TASK" in result

    def test_render_with_max_tokens(self, template_cls):
        template = template_cls()
        result = template.render(text="Test manuscript content.", max_tokens=2000)
        assert "MANUSCRIPT BEGIN" in result
        assert "Test manuscript content" in result

    def test_render_missing_text_raises(self, template_cls):
        template = template_cls()
        with pytest.raises(LLMTemplateError):
            template.render()

    def test_render_none_text_raises(self, template_cls):
        if template_cls is not ManuscriptExecutiveSummary:
            pytest.skip("Quality review expanded suite did not cover None text")
        template = template_cls()
        with pytest.raises(LLMTemplateError):
            template.render(text=None)


class TestManuscriptExecutiveSummary:
    def test_render_text_as_kwarg(self):
        t = ManuscriptExecutiveSummary()
        result = t.render(text="Kwargs manuscript text.")
        assert "Kwargs manuscript text" in result

    def test_render_includes_sections(self):
        t = ManuscriptExecutiveSummary()
        result = t.render(text="Test manuscript content.")
        for section in (
            "Overview",
            "Key Contributions",
            "Methodology",
            "Principal Results",
            "Significance",
        ):
            assert section in result

    def test_render_contains_validation_hints(self):
        result = ManuscriptExecutiveSummary().render(text="A test.", max_tokens=1000)
        assert "word" in result.lower() or "section" in result.lower()


class TestManuscriptQualityReview:
    def test_render_text_as_kwarg(self):
        t = ManuscriptQualityReview()
        result = t.render(text="Kwargs text.")
        assert "Kwargs text" in result

    def test_render_includes_quality_sections(self):
        t = ManuscriptQualityReview()
        result = t.render(text="Test manuscript.")
        for section in (
            "Overall Quality Score",
            "Clarity",
            "Structure",
            "Technical Accuracy",
            "Readability",
            "Specific Issues",
            "Recommendations",
        ):
            assert section in result

    def test_render_contains_scoring_sections(self):
        result = ManuscriptQualityReview().render(text="Content to review.")
        assert "Quality" in result or "Score" in result or "Clarity" in result

    def test_render_no_max_tokens(self):
        result = ManuscriptQualityReview().render(text="Quality review content.")
        assert "quality review" in result.lower() or "TASK" in result
