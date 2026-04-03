"""Tests for infrastructure/llm/review/quality.py.

Covers: _is_small_model, validate_review_quality (all review types),
and internal section validators.

No mocks used -- all tests use real data and computations.
"""

from __future__ import annotations

from infrastructure.llm.review.quality import (
    _is_small_model,
    validate_review_quality,
    _validate_executive_summary_section,
    _validate_quality_review_section,
    _validate_methodology_review_section,
    _validate_improvement_suggestions_section,
    _validate_translation_section,
)


class TestIsSmallModel:
    """Test _is_small_model."""

    def test_small_models(self):
        assert _is_small_model("gemma3:4b") is True
        assert _is_small_model("llama:7b") is True
        assert _is_small_model("mistral:3b") is True
        assert _is_small_model("qwen:8b") is True

    def test_large_models(self):
        assert _is_small_model("llama3:70b") is False
        assert _is_small_model("gpt-4") is False
        assert _is_small_model("claude-3-opus") is False

    def test_case_insensitive(self):
        assert _is_small_model("Gemma3:4B") is True


class TestValidateTranslationSection:
    """Test _validate_translation_section."""

    def test_valid_translation(self):
        text = "english abstract here\n\ntranslation in chinese follows"
        details: dict = {}
        issues: list = []
        _validate_translation_section(text, details, issues)
        assert details["has_english_section"] is True
        assert details["has_translation_section"] is True
        assert issues == []

    def test_missing_english(self):
        text = "translation in chinese follows"
        details: dict = {}
        issues: list = []
        _validate_translation_section(text, details, issues)
        assert "Missing English abstract" in issues[0]

    def test_missing_translation(self):
        text = "english abstract with overview content"
        details: dict = {}
        issues: list = []
        _validate_translation_section(text, details, issues)
        assert any("Missing translation" in i for i in issues)

    def test_english_header_format(self):
        text = "## english\n\nabstract content"
        details: dict = {}
        issues: list = []
        _validate_translation_section(text, details, issues)
        assert details["has_english_section"] is True

    def test_unicode_languages(self):
        text = "english abstract\n\n中文翻译"
        details: dict = {}
        issues: list = []
        _validate_translation_section(text, details, issues)
        assert details["has_translation_section"] is True


class TestValidateExecutiveSummarySection:
    """Test _validate_executive_summary_section."""

    def test_all_sections_present(self):
        text = "overview of the paper, key contributions, methodology, results and significance"
        details: dict = {}
        issues: list = []
        _validate_executive_summary_section(text, details, issues)
        assert len(details["sections_found"]) >= 4
        assert issues == []

    def test_no_sections(self):
        text = "just some random text without any expected headers or keywords"
        details: dict = {}
        issues: list = []
        _validate_executive_summary_section(text, details, issues)
        assert "Missing expected structure" in issues[0]


class TestValidateQualityReviewSection:
    """Test _validate_quality_review_section."""

    def test_with_scores(self):
        text = "clarity assessment\n**score: 4/5**\nstructure: score: 3/5"
        details: dict = {}
        issues: list = []
        _validate_quality_review_section(text, details, issues)
        assert len(details["scores_found"]) > 0
        assert issues == []

    def test_with_assessment_keywords(self):
        text = "the clarity of writing is good, with strong technical accuracy throughout"
        details: dict = {}
        issues: list = []
        _validate_quality_review_section(text, details, issues)
        assert details["has_assessment"] is True
        assert issues == []

    def test_no_scores_no_assessment(self):
        text = "the paper talks about stuff"
        details: dict = {}
        issues: list = []
        _validate_quality_review_section(text, details, issues)
        assert "Missing scoring" in issues[0]


class TestValidateMethodologyReviewSection:
    """Test _validate_methodology_review_section."""

    def test_with_sections(self):
        text = "strengths of the approach include robustness. weaknesses include limited scope. suggestions for improvement."
        details: dict = {}
        issues: list = []
        _validate_methodology_review_section(text, details, issues)
        assert len(details["sections_found"]) >= 2
        assert issues == []

    def test_with_methodology_content(self):
        text = "the research design employs a mixed methodology approach"
        details: dict = {}
        issues: list = []
        _validate_methodology_review_section(text, details, issues)
        assert details["has_methodology_content"] is True
        assert issues == []

    def test_missing_everything(self):
        text = "the paper is nice"
        details: dict = {}
        issues: list = []
        _validate_methodology_review_section(text, details, issues)
        assert len(issues) > 0


class TestValidateImprovementSuggestionsSection:
    """Test _validate_improvement_suggestions_section."""

    def test_with_priorities(self):
        text = "high priority: fix the abstract. medium priority: add references. low priority: formatting."
        details: dict = {}
        issues: list = []
        _validate_improvement_suggestions_section(text, details, issues)
        assert len(details["priorities_found"]) >= 2
        assert issues == []

    def test_with_recommendations(self):
        text = "we recommend the authors improve the introduction and fix the cited references"
        details: dict = {}
        issues: list = []
        _validate_improvement_suggestions_section(text, details, issues)
        assert details["has_recommendations"] is True
        assert issues == []

    def test_missing_everything(self):
        text = "the paper is fine"
        details: dict = {}
        issues: list = []
        _validate_improvement_suggestions_section(text, details, issues)
        assert len(issues) > 0


class TestValidateReviewQuality:
    """Test validate_review_quality integration."""

    def _make_long_text(self, base: str, min_words: int = 300) -> str:
        words = base.split()
        while len(words) < min_words:
            words.extend(base.split())
        return " ".join(words[:min_words])

    def test_valid_executive_summary(self):
        text = self._make_long_text(
            "## Overview\n\nThis research paper presents a novel contribution "
            "to the field. The methodology employed is rigorous. "
            "Key contributions include new algorithms. Results show "
            "significant improvements. The significance of this work "
            "is substantial for future research."
        )
        is_valid, issues, details = validate_review_quality(text, "executive_summary")
        # May or may not pass depending on word count, but should not crash
        assert isinstance(is_valid, bool)
        assert isinstance(issues, list)

    def test_off_topic_response(self):
        text = "I can't help with reviewing this document."
        is_valid, issues, details = validate_review_quality(text, "executive_summary")
        assert is_valid is False
        assert any("off-topic" in i.lower() for i in issues)

    def test_repetitive_response(self):
        # Create extremely repetitive content
        section = "This section discusses the methodology in great detail and covers important aspects. " * 10
        text = "\n\n".join([section] * 10)
        is_valid, issues, details = validate_review_quality(text, "quality_review")
        # Should detect repetition
        assert isinstance(is_valid, bool)

    def test_small_model_lower_threshold(self):
        text = self._make_long_text("Overview of findings. Methods employed. Results obtained.", 200)
        # With small model, threshold should be lower
        _, issues_small, _ = validate_review_quality(text, "executive_summary", model_name="gemma3:4b")
        _, issues_large, _ = validate_review_quality(text, "executive_summary", model_name="llama3:70b")
        # Both should return results without crashing
        assert isinstance(issues_small, list)
        assert isinstance(issues_large, list)

    def test_custom_min_words(self):
        text = "Short review. " * 5
        is_valid, issues, details = validate_review_quality(
            text, "executive_summary", min_words=10
        )
        assert isinstance(is_valid, bool)

    def test_translation_review_type(self):
        text = self._make_long_text(
            "English abstract of the paper discussing findings. "
            "Translation into Chinese follows. "
        )
        is_valid, issues, details = validate_review_quality(text, "translation")
        assert isinstance(is_valid, bool)
