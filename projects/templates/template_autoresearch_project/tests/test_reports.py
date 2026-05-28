"""Tests for loop report and writer helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from infrastructure.autoresearch import BudgetPolicy

from src.config import AutoResearchLoopConfig, HumanReviewState
from src.ml_task import run_bounded_ml_task
from src.models import AutoResearchLoopResult, LoopStageResult
from src.reports import (
    build_review_packet,
    render_loop_markdown,
    render_ml_experiment_report,
    render_review_packet_markdown,
    render_stage_matrix_csv,
)
from src.writers import write_json, write_text


def test_render_loop_markdown_includes_declared_stage_status() -> None:
    config = AutoResearchLoopConfig(
        topic="Demo",
        review_policy="human_review_required",
        research_questions=(),
        loop_stages=("plan",),
        required_artifacts=(),
        quality_checks=(),
    )
    result = AutoResearchLoopResult(
        project_name="demo",
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        config=config,
        stage_results=(
            LoopStageResult(
                name="plan",
                status="declared",
                evidence="Declared one stage.",
                suggested_action="review",
            ),
        ),
        claims=(),
        readiness_valid=True,
        output_paths=(),
    )

    markdown = render_loop_markdown(result)
    assert "declared" in markdown
    assert "plan" in markdown


def test_render_stage_matrix_csv_header() -> None:
    config = AutoResearchLoopConfig(
        topic="Demo",
        review_policy="human_review_required",
        research_questions=(),
        loop_stages=("readiness",),
        required_artifacts=(),
        quality_checks=(),
    )
    result = AutoResearchLoopResult(
        project_name="demo",
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        config=config,
        stage_results=(
            LoopStageResult(
                name="readiness",
                status="declared",
                evidence="Scheduled checks.",
                suggested_action="review",
            ),
        ),
        claims=(),
        readiness_valid=False,
        output_paths=(),
    )

    csv_text = render_stage_matrix_csv(result)
    assert "readiness,declared" in csv_text


def test_review_packet_distinguishes_ready_from_publication_approval() -> None:
    config = AutoResearchLoopConfig(
        topic="Demo",
        review_policy="human_review_required",
        research_questions=(),
        loop_stages=("readiness",),
        required_artifacts=(),
        quality_checks=(),
    )
    result = AutoResearchLoopResult(
        project_name="demo",
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        config=config,
        stage_results=(
            LoopStageResult(
                name="readiness",
                status="declared",
                evidence="Scheduled checks.",
                suggested_action="review",
            ),
        ),
        claims=(),
        readiness_valid=True,
        output_paths=(),
    )

    packet = build_review_packet(result)
    human_review = packet["human_review"]
    assert isinstance(human_review, dict)
    assert packet["schema"] == "template-autoresearch-review-packet-v1"
    assert human_review["ready_for_review"] is True
    assert human_review["publication_approved"] is False
    assert human_review["decision_source"] == "human_review.yaml"

    markdown = render_review_packet_markdown(result)
    assert "Ready for review: `true`" in markdown
    assert "Publication approved: `false`" in markdown


def test_review_packet_copies_only_manual_publication_approval() -> None:
    config = AutoResearchLoopConfig(
        topic="Demo",
        review_policy="human_review_required",
        research_questions=(),
        loop_stages=("readiness",),
        required_artifacts=(),
        quality_checks=(),
        human_review=HumanReviewState(
            publication_approved=True,
            reviewer="Human Reviewer",
            reviewed_at="2026-05-26",
            decisions={"proposal_review": "approved"},
            source_exists=True,
        ),
    )
    result = AutoResearchLoopResult(
        project_name="demo",
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        config=config,
        stage_results=(),
        claims=(),
        readiness_valid=True,
        output_paths=(),
    )

    packet = build_review_packet(result)

    human_review = packet["human_review"]
    assert isinstance(human_review, dict)
    assert human_review["ready_for_review"] is True
    assert human_review["publication_approved"] is True
    assert human_review["reviewer"] == "Human Reviewer"


def test_write_json_and_text_create_files(tmp_path: Path) -> None:
    json_path = write_json(tmp_path / "data" / "sample.json", {"ok": True})
    text_path = write_text(tmp_path / "reports" / "sample.md", "# Demo")

    assert json_path.exists()
    assert text_path.read_text(encoding="utf-8") == "# Demo"


def test_render_ml_experiment_report_includes_candidate_ledger(project_root: Path) -> None:
    result = run_bounded_ml_task(project_root, BudgetPolicy(max_iterations=4))

    markdown = render_ml_experiment_report(result)

    assert "Deterministic ML-Loop Experiment" in markdown
    assert result.accepted_candidate_id in markdown
    assert "tiny_patch_transformer" in markdown
    assert "LLM calls used: 0" in markdown
