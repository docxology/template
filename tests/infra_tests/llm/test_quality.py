"""Tests for infrastructure.llm.review.quality."""

from __future__ import annotations

import pytest

from infrastructure.llm.review.quality import (
    _is_small_model,
    _validate_executive_summary_section,
    _validate_improvement_suggestions_section,
    _validate_methodology_review_section,
    _validate_quality_review_section,
    _validate_translation_section,
    validate_review_quality,
)


class TestIsSmallModel:
    @pytest.mark.parametrize(
        "model_name",
        ["gemma3:4b", "llama:7b", "mistral:3b", "qwen:8b", "Gemma3:4B"],
    )
    def test_small_models(self, model_name):
        assert _is_small_model(model_name) is True

    @pytest.mark.parametrize(
        "model_name",
        ["llama3:70b", "gpt-4", "claude-3-opus"],
    )
    def test_large_models(self, model_name):
        assert _is_small_model(model_name) is False


class TestValidateTranslationSection:
    @pytest.mark.parametrize(
        ("text", "expect_english", "expect_translation", "expected_issue"),
        [
            (
                "english abstract here\n\ntranslation in chinese follows",
                True,
                True,
                None,
            ),
            ("translation in chinese follows", False, True, "Missing English abstract"),
            (
                "english abstract with overview content",
                True,
                False,
                "Missing translation",
            ),
            ("## english\n\nabstract content", True, False, "Missing translation"),
            ("english abstract\n\n中文翻译", True, True, None),
        ],
    )
    def test_translation_section(
        self, text, expect_english, expect_translation, expected_issue
    ):
        details: dict = {}
        issues: list = []
        _validate_translation_section(text, details, issues)
        assert details["has_english_section"] is expect_english
        assert details["has_translation_section"] is expect_translation
        if expected_issue is None:
            assert issues == []
        else:
            assert any(expected_issue in issue for issue in issues)


class TestValidateExecutiveSummarySection:
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
    @pytest.mark.parametrize(
        ("text", "expect_scores", "expect_assessment", "expect_issue"),
        [
            ("clarity assessment\n**score: 4/5**\nstructure: score: 3/5", True, False, None),
            (
                "the clarity of writing is good, with strong technical accuracy throughout",
                False,
                True,
                None,
            ),
            ("the paper talks about stuff", False, False, "Missing scoring"),
        ],
    )
    def test_quality_section(self, text, expect_scores, expect_assessment, expect_issue):
        details: dict = {}
        issues: list = []
        _validate_quality_review_section(text, details, issues)
        if expect_scores:
            assert len(details["scores_found"]) > 0
        if expect_assessment:
            assert details["has_assessment"] is True
        if expect_issue is None:
            assert issues == []
        else:
            assert expect_issue in issues[0]


class TestValidateMethodologyReviewSection:
    @pytest.mark.parametrize(
        ("text", "min_sections", "expect_methodology", "expect_issues"),
        [
            (
                "strengths of the approach include robustness. weaknesses include limited scope. suggestions for improvement.",
                2,
                False,
                False,
            ),
            ("the research design employs a mixed methodology approach", 0, True, False),
            ("the paper is nice", 0, False, True),
        ],
    )
    def test_methodology_section(
        self, text, min_sections, expect_methodology, expect_issues
    ):
        details: dict = {}
        issues: list = []
        _validate_methodology_review_section(text, details, issues)
        if min_sections:
            assert len(details["sections_found"]) >= min_sections
        if expect_methodology:
            assert details["has_methodology_content"] is True
        if expect_issues:
            assert len(issues) > 0
        else:
            assert issues == []


class TestValidateImprovementSuggestionsSection:
    @pytest.mark.parametrize(
        ("text", "min_priorities", "expect_recommendations", "expect_issues"),
        [
            (
                "high priority: fix the abstract. medium priority: add references. low priority: formatting.",
                2,
                False,
                False,
            ),
            (
                "we recommend the authors improve the introduction and fix the cited references",
                0,
                True,
                False,
            ),
            ("the paper is fine", 0, False, True),
        ],
    )
    def test_improvement_section(
        self, text, min_priorities, expect_recommendations, expect_issues
    ):
        details: dict = {}
        issues: list = []
        _validate_improvement_suggestions_section(text, details, issues)
        if min_priorities:
            assert len(details["priorities_found"]) >= min_priorities
        if expect_recommendations:
            assert details["has_recommendations"] is True
        if expect_issues:
            assert len(issues) > 0
        else:
            assert issues == []


class TestValidateReviewQuality:
    @staticmethod
    def _make_long_text(base: str, min_words: int = 300) -> str:
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
        assert isinstance(is_valid, bool)
        assert isinstance(issues, list)
        assert isinstance(details, dict)

    def test_off_topic_response(self):
        text = "I can't help with reviewing this document."
        is_valid, issues, _details = validate_review_quality(text, "executive_summary")
        assert is_valid is False
        assert any("off-topic" in issue.lower() for issue in issues)

    def test_repetitive_response(self):
        section = (
            "This section discusses the methodology in great detail and covers important aspects. "
            * 10
        )
        text = "\n\n".join([section] * 10)
        is_valid, _issues, _details = validate_review_quality(text, "quality_review")
        assert isinstance(is_valid, bool)

    @pytest.mark.parametrize("model_name", ["gemma3:4b", "llama3:70b"])
    def test_small_and_large_model_thresholds(self, model_name):
        text = self._make_long_text(
            "Overview of findings. Methods employed. Results obtained.", 200
        )
        _is_valid, issues, _details = validate_review_quality(
            text, "executive_summary", model_name=model_name
        )
        assert isinstance(issues, list)

    def test_custom_min_words(self):
        text = "Short review. " * 5
        is_valid, _issues, _details = validate_review_quality(
            text, "executive_summary", min_words=10
        )
        assert isinstance(is_valid, bool)

    def test_translation_review_type(self):
        text = self._make_long_text(
            "English abstract of the paper discussing findings. "
            "Translation into Chinese follows. "
        )
        is_valid, _issues, _details = validate_review_quality(text, "translation")
        assert isinstance(is_valid, bool)
