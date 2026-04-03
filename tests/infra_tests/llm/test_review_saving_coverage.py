"""Tests for infrastructure.llm.review.saving — comprehensive coverage."""

from pathlib import Path

from infrastructure.llm.review.saving import (
    save_single_review,
    generate_review_summary,
    save_review_outputs,
)
from infrastructure.llm.review.metrics import (
    ReviewMetrics,
    SessionMetrics,
    ManuscriptInputMetrics,
)


def _make_session_metrics(**overrides):
    defaults = {
        "manuscript": ManuscriptInputMetrics(
            total_chars=5000,
            total_words=800,
            total_tokens_est=1250,
        ),
        "reviews": {},
        "total_generation_time": 10.0,
    }
    defaults.update(overrides)
    return SessionMetrics(**defaults)


class TestSaveSingleReview:
    def test_basic_save(self, tmp_path):
        metrics = ReviewMetrics(output_words=100, output_chars=500, generation_time_seconds=2.0)
        path = save_single_review(
            "executive_summary", "This is the review.", tmp_path, "llama3", metrics
        )
        assert path.exists()
        content = path.read_text()
        assert "This is the review." in content

    def test_translation_save(self, tmp_path):
        metrics = ReviewMetrics(output_words=50, output_chars=300, generation_time_seconds=1.5)
        path = save_single_review(
            "translation_zh", "Chinese translation content.", tmp_path, "llama3", metrics
        )
        assert path.exists()
        assert path.name == "translation_zh.md"

    def test_creates_output_dir(self, tmp_path):
        out = tmp_path / "deep" / "nested"
        metrics = ReviewMetrics()
        path = save_single_review("test", "content", out, "model", metrics)
        assert path.exists()


class TestSaveReviewOutputs:
    def test_saves_all_files(self, tmp_path):
        reviews = {
            "executive_summary": "Executive summary content.",
            "quality_review": "Quality review content.",
        }
        metrics = _make_session_metrics(
            reviews={
                "executive_summary": ReviewMetrics(output_words=50, output_chars=200),
                "quality_review": ReviewMetrics(output_words=40, output_chars=180),
            }
        )
        result = save_review_outputs(
            reviews, tmp_path, "llama3", Path("/tmp/paper.pdf"), metrics
        )
        assert result is True
        assert (tmp_path / "executive_summary.md").exists()
        assert (tmp_path / "quality_review.md").exists()
        assert (tmp_path / "combined_review.md").exists()
        assert (tmp_path / "review_metadata.json").exists()

    def test_translation_review(self, tmp_path):
        reviews = {"translation_zh": "Chinese translation."}
        metrics = _make_session_metrics(
            reviews={"translation_zh": ReviewMetrics(output_words=30)}
        )
        result = save_review_outputs(
            reviews, tmp_path, "llama3", Path("/tmp/paper.pdf"), metrics
        )
        assert result is True
        assert (tmp_path / "translation_zh.md").exists()

    def test_empty_reviews(self, tmp_path):
        metrics = _make_session_metrics()
        result = save_review_outputs(
            {}, tmp_path, "llama3", Path("/tmp/paper.pdf"), metrics
        )
        assert result is True


class TestGenerateReviewSummary:
    def test_basic_summary(self, tmp_path):
        # Create some review files
        (tmp_path / "executive_summary.md").write_text("Review content")
        (tmp_path / "translation_zh.md").write_text("Translation")

        reviews = {
            "executive_summary": "Review content",
            "translation_zh": "Translation",
        }
        metrics = _make_session_metrics(
            reviews={
                "executive_summary": ReviewMetrics(
                    output_chars=100, output_words=20, generation_time_seconds=1.0
                ),
                "translation_zh": ReviewMetrics(
                    output_chars=50, output_words=10, generation_time_seconds=0.5
                ),
            }
        )
        # Should not raise
        generate_review_summary(reviews, tmp_path, metrics)

    def test_truncated_manuscript(self, tmp_path):
        reviews = {"summary": "content"}
        metrics = _make_session_metrics(
            manuscript=ManuscriptInputMetrics(
                total_chars=100000,
                total_words=15000,
                total_tokens_est=25000,
                truncated=True,
                truncated_chars=50000,
            ),
            reviews={"summary": ReviewMetrics()},
        )
        (tmp_path / "summary.md").write_text("content")
        generate_review_summary(reviews, tmp_path, metrics)
