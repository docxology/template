"""Tests for infrastructure.llm.review.saving module.

Tests save_review_outputs, save_single_review, and generate_review_summary.
"""

from __future__ import annotations

import json
from pathlib import Path


from infrastructure.llm.review.metrics import (
    ManuscriptInputMetrics,
    ReviewMetrics,
    SessionMetrics,
)
from infrastructure.llm.review.saving import (
    generate_review_summary,
    save_review_outputs,
    save_single_review,
)


def _make_session_metrics(review_names: list[str] | None = None) -> SessionMetrics:
    """Create a SessionMetrics with reasonable defaults."""
    sm = SessionMetrics(
        manuscript=ManuscriptInputMetrics(
            total_chars=5000,
            total_words=1000,
            total_tokens_est=1250,
            truncated=False,
        ),
        model_name="test-model",
        total_generation_time=30.0,
    )
    for name in (review_names or ["executive_summary", "quality_review"]):
        sm.reviews[name] = ReviewMetrics(
            input_chars=5000,
            input_words=1000,
            output_chars=2000,
            output_words=400,
            generation_time_seconds=15.0,
        )
    return sm


class TestSaveReviewOutputs:
    """Tests for save_review_outputs."""

    def test_saves_individual_reviews(self, tmp_path: Path):
        reviews = {
            "executive_summary": "Summary content here.",
            "quality_review": "Quality review content.",
        }
        metrics = _make_session_metrics(list(reviews.keys()))
        result = save_review_outputs(
            reviews, tmp_path, "test-model", Path("test.pdf"), metrics
        )
        assert result is True
        assert (tmp_path / "executive_summary.md").exists()
        assert (tmp_path / "quality_review.md").exists()

    def test_saves_combined_review(self, tmp_path: Path):
        reviews = {"executive_summary": "Content."}
        metrics = _make_session_metrics(["executive_summary"])
        save_review_outputs(reviews, tmp_path, "test-model", Path("test.pdf"), metrics)
        assert (tmp_path / "combined_review.md").exists()

    def test_saves_metadata_json(self, tmp_path: Path):
        reviews = {"executive_summary": "Content."}
        metrics = _make_session_metrics(["executive_summary"])
        save_review_outputs(reviews, tmp_path, "test-model", Path("test.pdf"), metrics)
        metadata_path = tmp_path / "review_metadata.json"
        assert metadata_path.exists()
        data = json.loads(metadata_path.read_text())
        assert "model" in data
        assert data["model"] == "test-model"

    def test_creates_output_directory(self, tmp_path: Path):
        output_dir = tmp_path / "nested" / "output"
        reviews = {"executive_summary": "Content."}
        metrics = _make_session_metrics(["executive_summary"])
        save_review_outputs(reviews, output_dir, "model", Path("test.pdf"), metrics)
        assert output_dir.exists()

    def test_translation_review_saved(self, tmp_path: Path):
        reviews = {"translation_zh": "Chinese translation content."}
        metrics = _make_session_metrics(["translation_zh"])
        save_review_outputs(reviews, tmp_path, "model", Path("test.pdf"), metrics)
        assert (tmp_path / "translation_zh.md").exists()


class TestSaveSingleReview:
    """Tests for save_single_review."""

    def test_saves_file(self, tmp_path: Path):
        metrics = ReviewMetrics(output_chars=500, output_words=100)
        path = save_single_review(
            "executive_summary", "Review content here.", tmp_path, "model", metrics
        )
        assert path.exists()
        assert path.name == "executive_summary.md"

    def test_file_contains_header_and_content(self, tmp_path: Path):
        metrics = ReviewMetrics(output_chars=500, output_words=100, generation_time_seconds=5.0)
        path = save_single_review(
            "quality_review", "The review text.", tmp_path, "test-model", metrics
        )
        content = path.read_text()
        assert "Quality Review" in content  # header title
        assert "test-model" in content  # model name in header
        assert "The review text." in content

    def test_creates_directory(self, tmp_path: Path):
        output_dir = tmp_path / "new_dir"
        metrics = ReviewMetrics()
        save_single_review("test", "Content.", output_dir, "model", metrics)
        assert output_dir.exists()

    def test_translation_review_logging(self, tmp_path: Path):
        metrics = ReviewMetrics(output_chars=500, output_words=100)
        path = save_single_review(
            "translation_zh", "Chinese content.", tmp_path, "model", metrics
        )
        assert path.exists()
        assert "translation_zh" in path.name


class TestGenerateReviewSummary:
    """Tests for generate_review_summary."""

    def test_basic_summary(self, tmp_path: Path, caplog):
        """Should log summary without errors."""
        # Create some files in the output dir
        (tmp_path / "executive_summary.md").write_text("Summary content")
        (tmp_path / "quality_review.md").write_text("Quality content")

        reviews = {"executive_summary": "Summary", "quality_review": "Quality"}
        metrics = _make_session_metrics(list(reviews.keys()))

        with caplog.at_level("INFO"):
            generate_review_summary(reviews, tmp_path, metrics)
        assert "LLM Manuscript Review Summary" in caplog.text

    def test_summary_with_translations(self, tmp_path: Path, caplog):
        """Should handle translation files in summary."""
        (tmp_path / "translation_zh.md").write_text("Chinese")
        (tmp_path / "executive_summary.md").write_text("Summary")

        reviews = {"executive_summary": "Summary", "translation_zh": "Chinese"}
        metrics = _make_session_metrics(list(reviews.keys()))

        with caplog.at_level("INFO"):
            generate_review_summary(reviews, tmp_path, metrics)

    def test_summary_shows_manuscript_metrics(self, tmp_path: Path, caplog):
        """Should show input manuscript info."""
        reviews = {"executive_summary": "Content"}
        metrics = _make_session_metrics(["executive_summary"])
        metrics.manuscript.truncated = True
        metrics.manuscript.truncated_chars = 3000

        with caplog.at_level("INFO"):
            generate_review_summary(reviews, tmp_path, metrics)
        assert "Truncated" in caplog.text
