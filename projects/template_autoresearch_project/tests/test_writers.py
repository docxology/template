"""Tests for loop writer helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from src.config import AutoResearchLoopConfig
from src.models import AutoResearchLoopResult, LoopStageResult
from src.writers import write_loop_payloads


def test_write_loop_payloads_writes_core_and_finalize_artifacts(tmp_path: Path) -> None:
    config = AutoResearchLoopConfig(
        topic="Demo",
        review_policy="human_review_required",
        research_questions=(),
        loop_stages=("plan", "readiness"),
        required_artifacts=(),
        quality_checks=(),
    )
    stage_results = (
        LoopStageResult(
            name="plan",
            status="declared",
            evidence="Declared one stage.",
            suggested_action="review",
        ),
        LoopStageResult(
            name="readiness",
            status="declared",
            evidence="Scheduled checks.",
            suggested_action="review",
        ),
    )
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    result = AutoResearchLoopResult(
        project_name="demo",
        generated_at=generated_at,
        config=config,
        stage_results=stage_results,
        claims=(),
        readiness_valid=False,
        output_paths=(),
    )

    paths = write_loop_payloads(
        tmp_path,
        {"project_name": "demo", "stages": []},
        config,
        stage_results,
        result,
    )

    expected = {
        tmp_path / "output/data/autoresearch_plan.json",
        tmp_path / "output/data/autoresearch_loop.json",
        tmp_path / "output/data/autoresearch_claims.json",
        tmp_path / "output/data/autoresearch_stage_matrix.csv",
        tmp_path / "output/data/autoresearch_review_packet.json",
        tmp_path / "output/data/manuscript_variables.json",
        tmp_path / "output/reports/autoresearch_loop.json",
        tmp_path / "output/reports/autoresearch_loop.md",
        tmp_path / "output/reports/autoresearch_review_packet.md",
        tmp_path / "output/reports/autoresearch_summary.md",
        tmp_path / "output/figures/autoresearch_stage_matrix.png",
        tmp_path / "output/figures/figure_registry.json",
    }
    assert expected <= {path.resolve() for path in paths}
    loop_payload = (tmp_path / "output/data/autoresearch_loop.json").read_text(encoding="utf-8")
    assert '"readiness_valid": false' in loop_payload
