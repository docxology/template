"""Tests for infrastructure.llm.templates.manuscript_reviews — expanded coverage."""

import pytest

from infrastructure.core.exceptions import LLMTemplateError
from infrastructure.llm.templates.manuscript_reviews import (
    ManuscriptExecutiveSummary,
    ManuscriptQualityReview,
)


class TestManuscriptExecutiveSummary:
    def test_render_basic(self):
        template = ManuscriptExecutiveSummary()
        result = template.render(text="This is a test manuscript about quantum computing.")
        assert "MANUSCRIPT BEGIN" in result
        assert "quantum computing" in result
        assert "executive summary" in result.lower() or "TASK" in result

    def test_render_with_max_tokens(self):
        template = ManuscriptExecutiveSummary()
        result = template.render(text="Test manuscript content.", max_tokens=2000)
        assert "MANUSCRIPT BEGIN" in result
        assert "Test manuscript content" in result

    def test_render_missing_text_raises(self):
        template = ManuscriptExecutiveSummary()
        with pytest.raises(LLMTemplateError):
            template.render()

    def test_render_with_no_max_tokens(self):
        template = ManuscriptExecutiveSummary()
        result = template.render(text="Content with no token limit")
        assert "Content with no token limit" in result
        # Should still have section guidance
        assert "Overview" in result or "Contributions" in result

    def test_render_none_text_raises(self):
        template = ManuscriptExecutiveSummary()
        with pytest.raises(LLMTemplateError):
            template.render(text=None)

    def test_render_contains_format_requirements(self):
        template = ManuscriptExecutiveSummary()
        result = template.render(text="Test content for review.")
        # Should contain section structure hints
        assert "Overview" in result or "Key Contributions" in result

    def test_render_contains_validation_hints(self):
        template = ManuscriptExecutiveSummary()
        result = template.render(text="A test.", max_tokens=1000)
        # Should contain some validation guidance
        assert "word" in result.lower() or "section" in result.lower()


class TestManuscriptQualityReview:
    def test_render_basic(self):
        template = ManuscriptQualityReview()
        result = template.render(text="This manuscript discusses novel methods.")
        assert "MANUSCRIPT BEGIN" in result
        assert "novel methods" in result
        assert "quality review" in result.lower() or "TASK" in result

    def test_render_with_max_tokens(self):
        template = ManuscriptQualityReview()
        result = template.render(text="Test content.", max_tokens=3000)
        assert "Test content" in result

    def test_render_missing_text_raises(self):
        template = ManuscriptQualityReview()
        with pytest.raises(LLMTemplateError):
            template.render()

    def test_render_contains_scoring_sections(self):
        template = ManuscriptQualityReview()
        result = template.render(text="Content to review.")
        # Should reference quality scoring sections
        assert "Quality" in result or "Score" in result or "Clarity" in result

    def test_render_contains_section_structure(self):
        template = ManuscriptQualityReview()
        result = template.render(text="Content.", max_tokens=2000)
        # Should contain required section names
        assert "Recommendations" in result or "Issues" in result

    def test_render_no_max_tokens(self):
        template = ManuscriptQualityReview()
        result = template.render(text="Quality review content.")
        # Should contain task description
        assert "quality review" in result.lower() or "TASK" in result
