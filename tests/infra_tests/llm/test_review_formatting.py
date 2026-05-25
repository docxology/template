"""Tests for infrastructure.llm.review.formatting module.

Tests review header building, combined review content, and metadata generation.
"""

from __future__ import annotations

from pathlib import Path


from infrastructure.llm.review.formatting import (
    _build_combined_review_content,
    _build_review_header,
    _build_review_metadata,
)
from infrastructure.llm.review.metrics import (
    ManuscriptInputMetrics,
    ReviewMetrics,
    SessionMetrics,
)


def _make_metrics(**kwargs) -> ReviewMetrics:
    return ReviewMetrics(
        output_chars=kwargs.get("output_chars", 500),
        output_words=kwargs.get("output_words", 100),
        generation_time_seconds=kwargs.get("generation_time_seconds", 2.0),
    )


def _make_session_metrics(
    review_names: list[str] | None = None,
    *,
    reviews: dict[str, ReviewMetrics] | None = None,
) -> SessionMetrics:
    """Create test SessionMetrics."""
    if reviews is not None:
        sm = SessionMetrics(
            manuscript=ManuscriptInputMetrics(
                total_chars=5000,
                total_words=800,
                total_tokens_est=1000,
                truncated=False,
            ),
            model_name="test-model",
            total_generation_time=30.0,
        )
        for name, metrics in reviews.items():
            sm.reviews[name] = metrics
        return sm

    sm = SessionMetrics(
        manuscript=ManuscriptInputMetrics(
            total_chars=5000,
            total_words=1000,
            total_tokens_est=1250,
        ),
        model_name="test-model",
        total_generation_time=30.0,
    )
    for name in review_names or ["executive_summary", "quality_review"]:
        sm.reviews[name] = ReviewMetrics(
            input_chars=5000,
            input_words=1000,
            output_chars=2000,
            output_words=400,
            generation_time_seconds=10.0,
        )
    return sm


class TestBuildReviewHeader:
    """Tests for _build_review_header."""

    def test_basic_header(self):
        metrics = ReviewMetrics(output_chars=500, output_words=100, generation_time_seconds=5.0)
        header = _build_review_header("executive_summary", "gemma3:4b", "2026-01-15", metrics)
        assert "Executive Summary" in header
        assert "gemma3:4b" in header
        assert "2026-01-15" in header
        assert "500" in header  # output chars
        assert "100" in header  # output words

    def test_header_formatting(self):
        metrics = ReviewMetrics()
        header = _build_review_header("quality_review", "model", "2026-01-01", metrics)
        assert header.startswith("#")
        assert "---" in header

    def test_translation_name_formatted(self):
        metrics = ReviewMetrics()
        header = _build_review_header("translation_zh", "model", "2026-01-01", metrics)
        assert "Translation Zh" in header


class TestBuildCombinedReviewContent:
    """Tests for _build_combined_review_content."""

    def test_basic_combined_content(self):
        reviews = {
            "executive_summary": "Executive summary content.",
            "quality_review": "Quality review content.",
        }
        metrics = _make_session_metrics(list(reviews.keys()))
        content = _build_combined_review_content(
            reviews, "test-model", Path("test.pdf"), metrics, "2026-01-15T10:00:00", "2026-01-15"
        )
        assert "LLM Manuscript Review" in content
        assert "test-model" in content
        assert "Executive Summary" in content
        assert "Quality Review" in content
        assert "executive_summary" in content.lower() or "Executive summary content" in content

    def test_combined_with_translations(self):
        reviews = {
            "executive_summary": "Summary.",
            "translation_zh": "Chinese translation.",
        }
        metrics = _make_session_metrics(list(reviews.keys()))
        content = _build_combined_review_content(
            reviews, "model", Path("test.pdf"), metrics, "2026-01-15T10:00:00", "2026-01-15"
        )
        assert "Translation" in content
        assert "Chinese" in content or "translation_zh" in content.lower()

    def test_combined_has_navigation(self):
        reviews = {"executive_summary": "Content."}
        metrics = _make_session_metrics(["executive_summary"])
        content = _build_combined_review_content(
            reviews, "model", Path("test.pdf"), metrics, "2026-01-15T10:00:00", "2026-01-15"
        )
        assert "Quick Navigation" in content
        assert "Action Items" in content

    def test_combined_has_metrics_section(self):
        reviews = {"executive_summary": "Content."}
        metrics = _make_session_metrics(["executive_summary"])
        content = _build_combined_review_content(
            reviews, "model", Path("test.pdf"), metrics, "2026-01-15T10:00:00", "2026-01-15"
        )
        assert "Generation Metrics" in content
        assert "Input Manuscript" in content


class TestBuildReviewMetadata:
    """Tests for _build_review_metadata."""

    def test_basic_metadata(self):
        reviews = {"executive_summary": "Content."}
        metrics = _make_session_metrics(["executive_summary"])
        metadata = _build_review_metadata(reviews, "test-model", Path("test.pdf"), metrics, "2026-01-15T10:00:00")
        assert metadata["model"] == "test-model"
        assert "executive_summary" in metadata["reviews_generated"]
        assert "manuscript_metrics" in metadata
        assert "review_metrics" in metadata
        assert "format_compliance" in metadata

    def test_metadata_has_config(self):
        reviews = {"executive_summary": "Content."}
        metrics = _make_session_metrics(["executive_summary"])
        metadata = _build_review_metadata(reviews, "model", Path("test.pdf"), metrics, "2026-01-15T10:00:00")
        assert "config" in metadata
        assert "timeout_seconds" in metadata["config"]

    def test_metadata_compliance_rate(self):
        reviews = {"executive_summary": "Content.", "quality_review": "Quality."}
        metrics = _make_session_metrics(list(reviews.keys()))
        metadata = _build_review_metadata(reviews, "model", Path("test.pdf"), metrics, "2026-01-15T10:00:00")
        assert "overall_rate" in metadata["format_compliance"]
        assert metadata["format_compliance"]["total_reviews"] == 2


class TestBuildReviewHeaderFromReviewFormatting:
    """Test _build_review_header."""

    def test_basic_header(self):
        metrics = _make_metrics()
        header = _build_review_header("executive_summary", "gemma3:4b", "2025-01-15", metrics)
        assert "Executive Summary" in header
        assert "gemma3:4b" in header
        assert "2025-01-15" in header
        assert "500" in header  # output_chars

    def test_translation_header(self):
        metrics = _make_metrics()
        header = _build_review_header("translation_zh", "llama3", "2025-03-01", metrics)
        assert "Translation Zh" in header


class TestBuildCombinedReviewContentFromReviewFormatting:
    """Test _build_combined_review_content."""

    def test_basic_combined(self):
        reviews = {
            "executive_summary": "## Overview\n\nGreat paper.",
            "quality_review": "## Quality\n\nWell written.",
        }
        metrics = _make_session_metrics()
        content = _build_combined_review_content(
            reviews,
            "gemma3:4b",
            Path("/fake/paper.pdf"),
            metrics,
            "2025-01-15T10:00:00",
            "2025-01-15",
        )
        assert "LLM Manuscript Review" in content
        assert "gemma3:4b" in content
        assert "paper.pdf" in content
        assert "Executive Summary" in content
        assert "Quality Review" in content

    def test_with_translations(self):
        reviews = {
            "executive_summary": "Summary.",
            "translation_zh": "Chinese content.",
            "translation_hi": "Hindi content.",
        }
        metrics = _make_session_metrics(
            reviews={
                "executive_summary": _make_metrics(),
                "translation_zh": _make_metrics(),
                "translation_hi": _make_metrics(),
            }
        )
        content = _build_combined_review_content(
            reviews,
            "model",
            Path("/paper.pdf"),
            metrics,
            "2025-01-15T10:00:00",
            "2025-01-15",
        )
        assert "Translation" in content
        assert "Chinese" in content

    def test_missing_reviews(self):
        reviews = {}
        metrics = _make_session_metrics(reviews={})
        content = _build_combined_review_content(
            reviews,
            "model",
            Path("/paper.pdf"),
            metrics,
            "2025-01-15T10:00:00",
            "2025-01-15",
        )
        assert "*Not generated*" in content


class TestBuildReviewMetadataFromReviewFormatting:
    """Test _build_review_metadata."""

    def test_basic_metadata(self):
        reviews = {
            "executive_summary": "## Overview\n\nContent.",
            "quality_review": "## Quality\n\nAssessment.",
        }
        metrics = _make_session_metrics()
        metadata = _build_review_metadata(
            reviews,
            "gemma3:4b",
            Path("/fake/paper.pdf"),
            metrics,
            "2025-01-15T10:00:00",
        )
        assert metadata["model"] == "gemma3:4b"
        assert "executive_summary" in metadata["reviews_generated"]
        assert "manuscript_metrics" in metadata
        assert "review_metrics" in metadata
        assert "format_compliance" in metadata

    def test_format_compliance_tracking(self):
        reviews = {
            "good_review": "## Overview\n\nProfessional text.",
            "bad_review": "I'd be happy to help you with this. Let me know if needed.",
        }
        metrics = _make_session_metrics(
            reviews={
                "good_review": _make_metrics(),
                "bad_review": _make_metrics(),
            }
        )
        metadata = _build_review_metadata(
            reviews,
            "model",
            Path("/paper.pdf"),
            metrics,
            "2025-01-15T10:00:00",
        )
        compliance = metadata["format_compliance"]
        assert "overall_rate" in compliance
        assert "per_review" in compliance

    def test_empty_reviews(self):
        reviews = {}
        metrics = _make_session_metrics(reviews={})
        metadata = _build_review_metadata(
            reviews,
            "model",
            Path("/paper.pdf"),
            metrics,
            "2025-01-15T10:00:00",
        )
        assert metadata["format_compliance"]["overall_rate"] == 100
