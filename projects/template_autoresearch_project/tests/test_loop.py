"""Tests for the deterministic AutoResearch loop."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.config import build_loop_config, load_manuscript_loop_settings
from src.loop import build_claims, run_autoresearch_loop


def test_run_autoresearch_loop_writes_artifacts_and_valid_readiness(project_root: Path, repo_root: Path) -> None:
    result = run_autoresearch_loop(project_root, repo_root)

    assert result.readiness_valid is True
    assert len(result.stage_results) == 6
    assert result.supported_claim_count >= 2
    assert all(stage.status == "declared" for stage in result.stage_results)
    for rel_path in result.config.required_artifacts:
        assert (project_root / rel_path).exists()

    readiness = json.loads((project_root / "output" / "reports" / "autoresearch_readiness.json").read_text())
    assert readiness["valid"] is True
    assert readiness["summary"]["errors"] == 0


def test_loop_payload_contains_claims_metrics_and_output_paths(project_root: Path, repo_root: Path) -> None:
    run_autoresearch_loop(project_root, repo_root)
    payload = json.loads((project_root / "output" / "data" / "autoresearch_loop.json").read_text())

    assert payload["metrics"]["stage_count"] == 6
    assert payload["metrics"]["supported_claim_count"] >= 2
    assert payload["metrics"]["readiness_valid"] is True
    assert "output/reports/autoresearch_loop.md" in payload["output_paths"]


def test_run_autoresearch_loop_writes_review_packet_and_stage_matrix(
    project_root: Path,
    repo_root: Path,
) -> None:
    result = run_autoresearch_loop(project_root, repo_root)

    expected_paths = {
        "output/data/autoresearch_stage_matrix.csv",
        "output/data/autoresearch_review_packet.json",
        "output/reports/autoresearch_review_packet.md",
        "output/reports/autoresearch_summary.md",
    }
    assert expected_paths <= set(result.output_paths)

    stage_matrix = (project_root / "output" / "data" / "autoresearch_stage_matrix.csv").read_text(
        encoding="utf-8"
    )
    assert "stage,status,evidence,suggested_action" in stage_matrix
    assert "readiness,declared" in stage_matrix

    review_packet = json.loads((project_root / "output" / "data" / "autoresearch_review_packet.json").read_text())
    assert review_packet["human_review"]["policy"] == "human_review_required"
    assert review_packet["human_review"]["ready_for_review"] == (
        result.readiness_valid and result.supported_claim_count == len(result.claims)
    )


def test_run_autoresearch_loop_writes_stage_matrix_figure(project_root: Path, repo_root: Path) -> None:
    run_autoresearch_loop(project_root, repo_root)

    figure_path = project_root / "output" / "figures" / "autoresearch_stage_matrix.png"
    registry_path = project_root / "output" / "figures" / "figure_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    assert figure_path.exists()
    assert figure_path.stat().st_size > 1000
    assert registry["fig:autoresearch_stage_matrix"]["filename"] == "autoresearch_stage_matrix.png"


def test_build_claims_only_supports_existing_files(project_root: Path, repo_root: Path) -> None:
    plan_settings = load_manuscript_loop_settings(project_root)
    from infrastructure.autoresearch import build_autoresearch_plan

    plan = build_autoresearch_plan(repo_root, project_root.name)
    config = build_loop_config(plan, plan_settings)
    missing_path = project_root / "output" / "reports" / "missing_evidence.json"

    claims = build_claims(config, project_root)
    supported_paths = {claim.evidence_path for claim in claims if claim.supported}
    assert "output/reports/missing_evidence.json" not in supported_paths
    assert missing_path.exists() is False


def test_run_autoresearch_loop_on_clean_scaffold(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    project = tmp_path / "template_autoresearch_project"
    source = Path(__file__).resolve().parents[1]
    shutil.copytree(
        source,
        project,
        ignore=shutil.ignore_patterns("output", ".pytest_cache", "__pycache__"),
    )

    result = run_autoresearch_loop(project, repo_root)

    assert len(result.stage_results) == 6
    assert all(stage.status == "declared" for stage in result.stage_results)
    assert (project / "output" / "data" / "autoresearch_loop.json").exists()
    assert (project / "output" / "reports" / "artifact_manifest.json").exists()
