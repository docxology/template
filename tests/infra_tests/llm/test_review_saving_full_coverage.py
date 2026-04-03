"""Tests for infrastructure/llm/review/saving.py.

Covers: save_review_outputs, save_single_review, generate_review_summary.

No mocks used -- all tests use real files and data structures.
"""

from __future__ import annotations

from pathlib import Path


from infrastructure.llm.review.metrics import (
    ManuscriptInputMetrics,
    ReviewMetrics,
    SessionMetrics,
)
from infrastructure.llm.review.saving import (
    save_review_outputs,
    save_single_review,
    generate_review_summary,
)


def _make_session_metrics(**overrides) -> SessionMetrics:
    """Create a SessionMetrics with sensible defaults."""
    m = SessionMetrics(
        model_name="test-model",
        manuscript=ManuscriptInputMetrics(
            total_chars=5000,
            total_words=800,
            total_tokens_est=1000,
            truncated=False,
            truncated_chars=0,
        ),
        reviews={
            "executive_summary": ReviewMetrics(
                output_chars=2000,
                output_words=300,
                generation_time_seconds=5.0,
            ),
        },
        total_generation_time=5.0,
    )
    for k, v in overrides.items():
        setattr(m, k, v)
    return m


class TestSaveReviewOutputs:
    """Test save_review_outputs."""

    def test_saves_individual_reviews(self, tmp_path):
        reviews = {
            "executive_summary": "## Overview\n\nGreat paper.",
            "quality_review": "## Quality\n\nWell written.",
        }
        metrics = _make_session_metrics(
            reviews={
                "executive_summary": ReviewMetrics(output_chars=100, output_words=10, generation_time_seconds=1.0),
                "quality_review": ReviewMetrics(output_chars=80, output_words=8, generation_time_seconds=0.5),
            }
        )
        result = save_review_outputs(
            reviews, tmp_path / "output", "test-model", Path("/fake/paper.pdf"), metrics
        )
        assert result is True
        assert (tmp_path / "output" / "executive_summary.md").exists()
        assert (tmp_path / "output" / "quality_review.md").exists()
        assert (tmp_path / "output" / "combined_review.md").exists()
        assert (tmp_path / "output" / "review_metadata.json").exists()

    def test_saves_translation(self, tmp_path):
        reviews = {
            "translation_zh": "Chinese translation content.",
        }
        metrics = _make_session_metrics(
            reviews={
                "translation_zh": ReviewMetrics(output_chars=200, output_words=50, generation_time_seconds=2.0),
            }
        )
        result = save_review_outputs(
            reviews, tmp_path / "output", "test-model", Path("/fake/paper.pdf"), metrics
        )
        assert result is True
        assert (tmp_path / "output" / "translation_zh.md").exists()


class TestSaveSingleReview:
    """Test save_single_review."""

    def test_basic_save(self, tmp_path):
        metrics = ReviewMetrics(output_chars=100, output_words=20, generation_time_seconds=1.0)
        path = save_single_review(
            "executive_summary", "## Overview\n\nContent.", tmp_path, "test-model", metrics
        )
        assert path.exists()
        assert path.name == "executive_summary.md"

    def test_translation_save(self, tmp_path):
        metrics = ReviewMetrics(output_chars=200, output_words=50, generation_time_seconds=2.0)
        path = save_single_review(
            "translation_zh", "Chinese content.", tmp_path, "test-model", metrics
        )
        assert path.exists()
        assert path.name == "translation_zh.md"

    def test_creates_directory(self, tmp_path):
        output_dir = tmp_path / "deep" / "nested" / "dir"
        metrics = ReviewMetrics(output_chars=50, output_words=10, generation_time_seconds=0.5)
        path = save_single_review(
            "test_review", "Content.", output_dir, "test-model", metrics
        )
        assert path.exists()


class TestGenerateReviewSummary:
    """Test generate_review_summary."""

    def test_basic_summary(self, tmp_path):
        # Create some files
        (tmp_path / "executive_summary.md").write_text("Summary content.")
        (tmp_path / "quality_review.md").write_text("Quality content.")

        reviews = {
            "executive_summary": "Summary content.",
            "quality_review": "Quality content.",
        }
        metrics = _make_session_metrics(
            reviews={
                "executive_summary": ReviewMetrics(output_chars=100, output_words=20, generation_time_seconds=1.0),
                "quality_review": ReviewMetrics(output_chars=80, output_words=15, generation_time_seconds=0.8),
            },
            total_generation_time=1.8,
        )
        # Should not raise
        generate_review_summary(reviews, tmp_path, metrics)

    def test_with_translations(self, tmp_path):
        (tmp_path / "translation_zh.md").write_text("Chinese translation.")
        (tmp_path / "executive_summary.md").write_text("Summary.")

        reviews = {
            "executive_summary": "Summary.",
            "translation_zh": "Chinese translation.",
        }
        metrics = _make_session_metrics(
            reviews={
                "executive_summary": ReviewMetrics(output_chars=50, output_words=10, generation_time_seconds=0.5),
                "translation_zh": ReviewMetrics(output_chars=100, output_words=30, generation_time_seconds=2.0),
            },
            total_generation_time=2.5,
        )
        generate_review_summary(reviews, tmp_path, metrics)

    def test_truncated_manuscript(self, tmp_path):
        (tmp_path / "review.md").write_text("Content.")

        reviews = {"review": "Content."}
        metrics = _make_session_metrics(
            manuscript=ManuscriptInputMetrics(
                total_chars=100000,
                total_words=15000,
                total_tokens_est=20000,
                truncated=True,
                truncated_chars=50000,
            ),
            reviews={"review": ReviewMetrics(output_chars=50, output_words=10, generation_time_seconds=0.5)},
        )
        generate_review_summary(reviews, tmp_path, metrics)

    def test_empty_reviews(self, tmp_path):
        generate_review_summary({}, tmp_path, _make_session_metrics(reviews={}, total_generation_time=0.0))
