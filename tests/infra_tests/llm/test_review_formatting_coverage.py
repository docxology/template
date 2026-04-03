"""Tests for infrastructure/llm/review/formatting.py.

Covers: _build_review_header, _build_combined_review_content, _build_review_metadata.

No mocks used -- all tests use real data structures.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.llm.review.formatting import (
    _build_review_header,
    _build_combined_review_content,
    _build_review_metadata,
)
from infrastructure.llm.review.metrics import ReviewMetrics, SessionMetrics, ManuscriptInputMetrics


def _make_metrics(**kwargs) -> ReviewMetrics:
    return ReviewMetrics(
        output_chars=kwargs.get("output_chars", 500),
        output_words=kwargs.get("output_words", 100),
        generation_time_seconds=kwargs.get("generation_time_seconds", 2.0),
    )


def _make_session_metrics(reviews: dict[str, ReviewMetrics] | None = None) -> SessionMetrics:
    if reviews is None:
        reviews = {
            "executive_summary": _make_metrics(),
            "quality_review": _make_metrics(output_chars=300, output_words=60),
        }
    return SessionMetrics(
        model_name="test-model",
        manuscript=ManuscriptInputMetrics(
            total_chars=5000,
            total_words=800,
            total_tokens_est=1000,
            truncated=False,
            truncated_chars=0,
        ),
        reviews=reviews,
        total_generation_time=4.0,
    )


class TestBuildReviewHeader:
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


class TestBuildCombinedReviewContent:
    """Test _build_combined_review_content."""

    def test_basic_combined(self):
        reviews = {
            "executive_summary": "## Overview\n\nGreat paper.",
            "quality_review": "## Quality\n\nWell written.",
        }
        metrics = _make_session_metrics()
        content = _build_combined_review_content(
            reviews, "gemma3:4b", Path("/fake/paper.pdf"), metrics,
            "2025-01-15T10:00:00", "2025-01-15",
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
        metrics = _make_session_metrics(reviews={
            "executive_summary": _make_metrics(),
            "translation_zh": _make_metrics(),
            "translation_hi": _make_metrics(),
        })
        content = _build_combined_review_content(
            reviews, "model", Path("/paper.pdf"), metrics,
            "2025-01-15T10:00:00", "2025-01-15",
        )
        assert "Translation" in content
        assert "Chinese" in content

    def test_missing_reviews(self):
        reviews = {}
        metrics = _make_session_metrics(reviews={})
        content = _build_combined_review_content(
            reviews, "model", Path("/paper.pdf"), metrics,
            "2025-01-15T10:00:00", "2025-01-15",
        )
        assert "*Not generated*" in content


class TestBuildReviewMetadata:
    """Test _build_review_metadata."""

    def test_basic_metadata(self):
        reviews = {
            "executive_summary": "## Overview\n\nContent.",
            "quality_review": "## Quality\n\nAssessment.",
        }
        metrics = _make_session_metrics()
        metadata = _build_review_metadata(
            reviews, "gemma3:4b", Path("/fake/paper.pdf"), metrics,
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
        metrics = _make_session_metrics(reviews={
            "good_review": _make_metrics(),
            "bad_review": _make_metrics(),
        })
        metadata = _build_review_metadata(
            reviews, "model", Path("/paper.pdf"), metrics,
            "2025-01-15T10:00:00",
        )
        compliance = metadata["format_compliance"]
        assert "overall_rate" in compliance
        assert "per_review" in compliance

    def test_empty_reviews(self):
        reviews = {}
        metrics = _make_session_metrics(reviews={})
        metadata = _build_review_metadata(
            reviews, "model", Path("/paper.pdf"), metrics,
            "2025-01-15T10:00:00",
        )
        assert metadata["format_compliance"]["overall_rate"] == 100
