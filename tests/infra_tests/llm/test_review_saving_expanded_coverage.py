"""Tests for infrastructure.llm.review.saving — expanded coverage."""


from infrastructure.llm.review.saving import (
    save_review_outputs,
    save_single_review,
    generate_review_summary,
)
from infrastructure.llm.review.metrics import ReviewMetrics, SessionMetrics, ManuscriptInputMetrics


def _make_session_metrics(**overrides):
    defaults = {
        "manuscript": ManuscriptInputMetrics(
            total_chars=10000,
            total_words=2000,
            total_tokens_est=3000,
            truncated=False,
            truncated_chars=10000,
        ),
        "total_generation_time": 30.0,
        "reviews": {
            "executive_summary": ReviewMetrics(
                input_chars=10000,
                input_words=2000,
                input_tokens_est=3000,
                output_chars=3000,
                output_words=500,
                output_tokens_est=700,
                generation_time_seconds=10.0,
            ),
        },
    }
    defaults.update(overrides)
    return SessionMetrics(**defaults)


class TestSaveReviewOutputs:
    def test_saves_individual_reviews(self, tmp_path):
        reviews = {"executive_summary": "# Executive Summary\nContent here"}
        session = _make_session_metrics()
        result = save_review_outputs(
            reviews, tmp_path, "gemma3:4b", tmp_path / "paper.pdf", session
        )
        assert result is True
        assert (tmp_path / "executive_summary.md").exists()

    def test_saves_combined_review(self, tmp_path):
        reviews = {"executive_summary": "Content"}
        session = _make_session_metrics()
        save_review_outputs(reviews, tmp_path, "gemma3:4b", tmp_path / "paper.pdf", session)
        assert (tmp_path / "combined_review.md").exists()

    def test_saves_metadata(self, tmp_path):
        reviews = {"executive_summary": "Content"}
        session = _make_session_metrics()
        save_review_outputs(reviews, tmp_path, "gemma3:4b", tmp_path / "paper.pdf", session)
        assert (tmp_path / "review_metadata.json").exists()

    def test_translation_review(self, tmp_path):
        reviews = {"translation_zh": "Chinese translation content"}
        metrics = ReviewMetrics(
            output_chars=2000, output_words=300, generation_time_seconds=5.0
        )
        session = _make_session_metrics(reviews={"translation_zh": metrics})
        result = save_review_outputs(
            reviews, tmp_path, "gemma3:4b", tmp_path / "paper.pdf", session
        )
        assert result is True
        assert (tmp_path / "translation_zh.md").exists()

    def test_multiple_reviews(self, tmp_path):
        reviews = {
            "executive_summary": "Executive content",
            "quality_review": "Quality content",
        }
        session = _make_session_metrics(
            reviews={
                "executive_summary": ReviewMetrics(
                    output_chars=1000, output_words=200, generation_time_seconds=5.0
                ),
                "quality_review": ReviewMetrics(
                    output_chars=1500, output_words=300, generation_time_seconds=8.0
                ),
            }
        )
        result = save_review_outputs(
            reviews, tmp_path, "gemma3:4b", tmp_path / "paper.pdf", session
        )
        assert result is True

    def test_creates_directory(self, tmp_path):
        reviews = {"summary": "Content"}
        session = _make_session_metrics(reviews={"summary": ReviewMetrics()})
        out = tmp_path / "nested" / "reviews"
        save_review_outputs(reviews, out, "model", tmp_path / "paper.pdf", session)
        assert out.exists()


class TestSaveSingleReview:
    def test_saves_file(self, tmp_path):
        metrics = ReviewMetrics(
            output_chars=500, output_words=100, generation_time_seconds=3.0
        )
        path = save_single_review(
            "executive_summary", "Review content here", tmp_path, "gemma3:4b", metrics
        )
        assert path.exists()
        assert path.name == "executive_summary.md"
        content = path.read_text()
        assert "Review content here" in content

    def test_translation_review(self, tmp_path):
        metrics = ReviewMetrics(
            output_chars=800, output_words=150, generation_time_seconds=5.0
        )
        path = save_single_review(
            "translation_zh", "Chinese content", tmp_path, "gemma3:4b", metrics
        )
        assert path.exists()

    def test_creates_directory(self, tmp_path):
        out = tmp_path / "new" / "dir"
        metrics = ReviewMetrics()
        path = save_single_review("test", "content", out, "model", metrics)
        assert path.exists()


class TestGenerateReviewSummary:
    def test_basic(self, tmp_path):
        # Create some review files
        (tmp_path / "executive_summary.md").write_text("Summary content " * 50)
        (tmp_path / "quality_review.md").write_text("Quality content " * 50)

        reviews = {
            "executive_summary": "Summary content " * 50,
            "quality_review": "Quality content " * 50,
        }
        session = _make_session_metrics(
            reviews={
                "executive_summary": ReviewMetrics(
                    output_chars=1000, output_words=200, generation_time_seconds=5.0
                ),
                "quality_review": ReviewMetrics(
                    output_chars=1500, output_words=300, generation_time_seconds=8.0
                ),
            }
        )
        # Should not raise
        generate_review_summary(reviews, tmp_path, session)

    def test_with_translations(self, tmp_path):
        (tmp_path / "translation_zh.md").write_text("Chinese " * 100)
        (tmp_path / "translation_hi.md").write_text("Hindi " * 100)
        (tmp_path / "executive_summary.md").write_text("English " * 100)

        reviews = {
            "translation_zh": "Chinese " * 100,
            "translation_hi": "Hindi " * 100,
            "executive_summary": "English " * 100,
        }
        session = _make_session_metrics(
            reviews={
                "translation_zh": ReviewMetrics(
                    output_chars=500, output_words=100, generation_time_seconds=3.0
                ),
                "translation_hi": ReviewMetrics(
                    output_chars=500, output_words=100, generation_time_seconds=3.0
                ),
                "executive_summary": ReviewMetrics(
                    output_chars=600, output_words=100, generation_time_seconds=5.0
                ),
            }
        )
        generate_review_summary(reviews, tmp_path, session)

    def test_truncated_manuscript(self, tmp_path):
        reviews = {"summary": "Content"}
        (tmp_path / "summary.md").write_text("Content")
        session = _make_session_metrics(
            manuscript=ManuscriptInputMetrics(
                total_chars=1000000,
                total_words=200000,
                total_tokens_est=300000,
                truncated=True,
                truncated_chars=500000,
            ),
            reviews={"summary": ReviewMetrics(
                output_chars=100, output_words=20, generation_time_seconds=1.0
            )},
        )
        generate_review_summary(reviews, tmp_path, session)
