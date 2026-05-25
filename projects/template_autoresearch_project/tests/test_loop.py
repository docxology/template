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
    assert len(result.stage_results) == 7
    assert result.supported_claim_count == len(result.claims)
    assert all(stage.status == "declared" for stage in result.stage_results)
    assert result.ml_task["accepted_candidate_id"] == "exp-quadratic-alpha-0p1"
    for rel_path in result.config.required_artifacts:
        assert (project_root / rel_path).exists()

    readiness = json.loads((project_root / "output" / "reports" / "autoresearch_readiness.json").read_text())
    assert readiness["valid"] is True
    assert readiness["summary"]["errors"] == 0


def test_loop_payload_contains_claims_metrics_and_output_paths(project_root: Path, repo_root: Path) -> None:
    run_autoresearch_loop(project_root, repo_root)
    payload = json.loads((project_root / "output" / "data" / "autoresearch_loop.json").read_text())

    assert payload["metrics"]["stage_count"] == 7
    assert payload["metrics"]["supported_claim_count"] == 5
    assert payload["metrics"]["readiness_valid"] is True
    assert payload["ml_task"]["best_accuracy"] > payload["ml_task"]["baseline_accuracy"]
    assert "output/reports/autoresearch_loop.md" in payload["output_paths"]
    assert "output/data/research_program.json" in payload["output_paths"]
    assert "output/data/idea_ledger.json" in payload["output_paths"]
    assert "output/data/run_ledger.json" in payload["output_paths"]
    assert "output/data/review_decisions.json" in payload["output_paths"]
    assert "output/data/benchmark_scores.json" in payload["output_paths"]
    assert "output/data/ml_task_results.json" in payload["output_paths"]
    assert "output/data/ml_candidate_ledger.json" in payload["output_paths"]


def test_run_autoresearch_loop_writes_bounded_method_ledgers(project_root: Path, repo_root: Path) -> None:
    result = run_autoresearch_loop(project_root, repo_root)

    research_program = json.loads((project_root / "output" / "data" / "research_program.json").read_text())
    idea_ledger = json.loads((project_root / "output" / "data" / "idea_ledger.json").read_text())
    run_ledger = json.loads((project_root / "output" / "data" / "run_ledger.json").read_text())
    review_decisions = json.loads((project_root / "output" / "data" / "review_decisions.json").read_text())
    benchmark_scores = json.loads((project_root / "output" / "data" / "benchmark_scores.json").read_text())

    assert result.readiness_valid is True
    assert research_program["path"] == "program.md"
    assert research_program["autonomy_level"] == "proposal_only"
    assert research_program["budget_policy"]["max_iterations"] == 3
    assert "projects/template_autoresearch_project/src/" in research_program["edit_allowlist"]
    assert {idea["status"] for idea in idea_ledger["ideas"]} >= {"accepted", "rejected", "deferred"}
    accepted = [idea for idea in idea_ledger["ideas"] if idea["status"] == "accepted"]
    assert accepted and all(idea["evidence_links"] for idea in accepted)
    assert run_ledger["iterations_used"] == 3
    assert run_ledger["llm_calls_used"] == 0
    assert run_ledger["cost_usd_used"] == 0.0
    assert run_ledger["budget_exhausted"] is True
    assert run_ledger["exhaustion_reason"] == "candidate iteration budget reached"
    assert {row["decision"] for row in review_decisions["decisions"]} == {"deferred"}
    assert {task["id"] for task in benchmark_scores["tasks"]} == {"readiness-smoke", "ml-loop-score"}
    assert all(task["status"] == "graded" for task in benchmark_scores["tasks"])


def test_run_autoresearch_loop_writes_review_packet_and_stage_matrix(
    project_root: Path,
    repo_root: Path,
) -> None:
    result = run_autoresearch_loop(project_root, repo_root)

    expected_paths = {
        "output/data/autoresearch_stage_matrix.csv",
        "output/data/autoresearch_review_packet.json",
        "output/data/research_program.json",
        "output/data/idea_ledger.json",
        "output/data/run_ledger.json",
        "output/data/review_decisions.json",
        "output/data/benchmark_scores.json",
        "output/data/ml_task_results.json",
        "output/data/ml_candidate_ledger.json",
        "output/reports/autoresearch_review_packet.md",
        "output/reports/autoresearch_summary.md",
        "output/reports/ml_experiment_report.md",
        "output/reports/ml_benchmark_score.json",
    }
    assert expected_paths <= set(result.output_paths)

    stage_matrix = (project_root / "output" / "data" / "autoresearch_stage_matrix.csv").read_text(encoding="utf-8")
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
    assert (project_root / "output" / "figures" / "ml_candidate_scores.png").exists()
    assert registry["fig:autoresearch_stage_matrix"]["filename"] == "autoresearch_stage_matrix.png"
    assert registry["fig:ml_candidate_scores"]["filename"] == "ml_candidate_scores.png"


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

    assert len(result.stage_results) == 7
    assert all(stage.status == "declared" for stage in result.stage_results)
    assert (project / "output" / "data" / "autoresearch_loop.json").exists()
    assert (project / "output" / "data" / "ml_task_results.json").exists()
    assert (project / "output" / "reports" / "artifact_manifest.json").exists()
