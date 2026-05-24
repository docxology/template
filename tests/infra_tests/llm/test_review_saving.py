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
    truncated: bool = False,
    truncated_chars: int = 0,
) -> SessionMetrics:
    sm = SessionMetrics(
        manuscript=ManuscriptInputMetrics(
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
        result = save_review_outputs(
            reviews, output_dir, "test-model", Path("test.pdf"), metrics
        )
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
        path = save_single_review(
            "quality_review", "The review text.", tmp_path, "test-model", metrics
        )
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
