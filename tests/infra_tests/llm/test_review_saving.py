"""Tests for infrastructure.llm.review.saving."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

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


def _make_session_metrics(
    review_names: list[str] | None = None,
    *,
    reviews: dict[str, ReviewMetrics] | None = None,
    manuscript: ManuscriptInputMetrics | None = None,
    truncated: bool = False,
    truncated_chars: int = 0,
) -> SessionMetrics:
    if reviews is not None:
        sm = SessionMetrics(
            manuscript=manuscript
            or ManuscriptInputMetrics(
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
        manuscript=manuscript
        or ManuscriptInputMetrics(
            total_chars=5000 if not truncated else 1000000,
            total_words=1000 if not truncated else 200000,
            total_tokens_est=1250 if not truncated else 300000,
            truncated=truncated,
            truncated_chars=truncated_chars,
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
            generation_time_seconds=15.0,
        )
    return sm


class TestSaveReviewOutputs:
    @pytest.mark.parametrize(
        "reviews",
        [
            {"executive_summary": "Summary content here.", "quality_review": "Quality review content."},
            {"executive_summary": "Content"},
            {"translation_zh": "Chinese translation content"},
            {"executive_summary": "Executive content", "quality_review": "Quality content"},
            {"summary": "Content"},
        ],
    )
    def test_saves_review_files(self, tmp_path: Path, reviews):
        metrics = _make_session_metrics(list(reviews.keys()))
        output_dir = tmp_path / "nested" / "reviews" if "summary" in reviews else tmp_path / "output"
        result = save_review_outputs(reviews, output_dir, "test-model", Path("test.pdf"), metrics)
        assert result is True
        for review_name in reviews:
            assert (output_dir / f"{review_name}.md").exists()
        if "summary" not in reviews or len(reviews) > 1:
            assert (output_dir / "combined_review.md").exists()
        assert (output_dir / "review_metadata.json").exists()

    def test_saves_metadata_json(self, tmp_path: Path):
        reviews = {"executive_summary": "Content."}
        metrics = _make_session_metrics(["executive_summary"])
        save_review_outputs(reviews, tmp_path, "test-model", Path("test.pdf"), metrics)
        data = json.loads((tmp_path / "review_metadata.json").read_text())
        assert data["model"] == "test-model"


class TestSaveSingleReview:
    @pytest.mark.parametrize(
        ("review_type", "content"),
        [
            ("executive_summary", "Review content here."),
            ("quality_review", "The review text."),
            ("translation_zh", "Chinese content"),
            ("test", "content"),
        ],
    )
    def test_saves_file(self, tmp_path: Path, review_type, content):
        metrics = ReviewMetrics(
            output_chars=500,
            output_words=100,
            generation_time_seconds=3.0,
        )
        output_dir = tmp_path / "new" / "dir" if review_type == "test" else tmp_path
        path = save_single_review(review_type, content, output_dir, "test-model", metrics)
        assert path.exists()
        assert path.name == f"{review_type}.md"
        assert content in path.read_text()

    def test_file_contains_header_and_content(self, tmp_path: Path):
        metrics = ReviewMetrics(output_chars=500, output_words=100, generation_time_seconds=5.0)
        path = save_single_review("quality_review", "The review text.", tmp_path, "test-model", metrics)
        body = path.read_text()
        assert "Quality Review" in body
        assert "test-model" in body
        assert "The review text." in body


class TestGenerateReviewSummary:
    @pytest.mark.parametrize(
        ("reviews", "truncated"),
        [
            (
                {"executive_summary": "Summary content " * 50, "quality_review": "Quality content " * 50},
                False,
            ),
            (
                {
                    "translation_zh": "Chinese " * 100,
                    "translation_hi": "Hindi " * 100,
                    "executive_summary": "English " * 100,
                },
                False,
            ),
            ({"summary": "Content"}, True),
            ({}, False),
        ],
    )
    def test_generate_summary(self, tmp_path: Path, caplog, reviews, truncated):
        for name in reviews:
            (tmp_path / f"{name}.md").write_text(reviews[name])
        metrics = _make_session_metrics(
            list(reviews.keys()) or None,
            truncated=truncated,
            truncated_chars=500000 if truncated else 0,
        )
        if not reviews:
            metrics = SessionMetrics(
                manuscript=ManuscriptInputMetrics(
                    total_chars=5000,
                    total_words=1000,
                    total_tokens_est=1250,
                    truncated=False,
                    truncated_chars=0,
                ),
                model_name="test-model",
                total_generation_time=0.0,
                reviews={},
            )

        with caplog.at_level("INFO"):
            generate_review_summary(reviews, tmp_path, metrics)
        if reviews and not truncated:
            assert "LLM Manuscript Review Summary" in caplog.text or reviews
        if truncated:
            assert "Truncated" in caplog.text


class TestSaveSingleReviewFromReviewSaving:
    def test_basic_save(self, tmp_path):
        metrics = ReviewMetrics(output_words=100, output_chars=500, generation_time_seconds=2.0)
        path = save_single_review("executive_summary", "This is the review.", tmp_path, "llama3", metrics)
        assert path.exists()
        content = path.read_text()
        assert "This is the review." in content

    def test_translation_save(self, tmp_path):
        metrics = ReviewMetrics(output_words=50, output_chars=300, generation_time_seconds=1.5)
        path = save_single_review("translation_zh", "Chinese translation content.", tmp_path, "llama3", metrics)
        assert path.exists()
        assert path.name == "translation_zh.md"

    def test_creates_output_dir(self, tmp_path):
        out = tmp_path / "deep" / "nested"
        metrics = ReviewMetrics()
        path = save_single_review("test", "content", out, "model", metrics)
        assert path.exists()


class TestSaveReviewOutputsFromReviewSaving:
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
        result = save_review_outputs(reviews, tmp_path, "llama3", Path("/tmp/paper.pdf"), metrics)
        assert result is True
        assert (tmp_path / "executive_summary.md").exists()
        assert (tmp_path / "quality_review.md").exists()
        assert (tmp_path / "combined_review.md").exists()
        assert (tmp_path / "review_metadata.json").exists()

    def test_translation_review(self, tmp_path):
        reviews = {"translation_zh": "Chinese translation."}
        metrics = _make_session_metrics(reviews={"translation_zh": ReviewMetrics(output_words=30)})
        result = save_review_outputs(reviews, tmp_path, "llama3", Path("/tmp/paper.pdf"), metrics)
        assert result is True
        assert (tmp_path / "translation_zh.md").exists()

    def test_empty_reviews(self, tmp_path):
        metrics = _make_session_metrics()
        result = save_review_outputs({}, tmp_path, "llama3", Path("/tmp/paper.pdf"), metrics)
        assert result is True


class TestGenerateReviewSummaryFromReviewSaving:
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
                "executive_summary": ReviewMetrics(output_chars=100, output_words=20, generation_time_seconds=1.0),
                "translation_zh": ReviewMetrics(output_chars=50, output_words=10, generation_time_seconds=0.5),
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
