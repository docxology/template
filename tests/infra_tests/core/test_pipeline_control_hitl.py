"""Tests for adaptive pipeline control surfaces.

These tests cover the AutoResearchClaw-inspired additions without making the
template pipeline autonomous: stage contracts, explicit hooks, lightweight HITL,
and run lessons remain opt-in and reproducible.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.hitl import HitlController, HitlMode, validate_agent_response_file
from infrastructure.core.pipeline.smart_pause import compute_pause_recommendations, write_pause_recommendations
from infrastructure.core.pipeline.snapshot import compare_snapshots, create_snapshot, snapshot_compare_to_markdown
from infrastructure.core.pipeline.types import (
    PipelineConfig,
    PipelineControlConfig,
    PipelineStageResult,
    StageContract,
    StageSpec,
    StagePolicy,
)
from infrastructure.reporting.run_lessons import collect_run_lessons, write_run_lessons


def test_hitl_controller_records_gate_pause_and_commands(tmp_path: Path) -> None:
    controller = HitlController(project_output_dir=tmp_path, mode=HitlMode.GATE_ONLY)

    waiting = controller.pause(
        stage_num=6,
        stage_name="Output Validation",
        reason="publication_readiness",
        context_summary="Validation report needs review.",
    )
    status = controller.status()

    assert waiting.stage_num == 6
    assert status["waiting"]["reason"] == "publication_readiness"

    controller.guide(stage_num=6, message="Review citations before resuming.")
    controller.approve(message="Looks grounded.")
    controller.resume(message="Resume from checkpoint.")

    assert controller.status()["waiting"] is None
    decisions = (tmp_path / "hitl" / "decisions.jsonl").read_text(encoding="utf-8")
    assert '"action": "approve"' in decisions
    assert '"action": "resume"' in decisions
    assert (tmp_path / "hitl" / "guidance" / "stage-06.md").read_text(encoding="utf-8") == (
        "Review citations before resuming.\n"
    )


def test_hitl_cli_commands_status_guide_and_validate_response(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "projects" / "demo" / "output").mkdir(parents=True)
    response_path = tmp_path / "response.json"
    response_path.write_text('{"action": "guide", "message": "Add a benchmark.", "stage_num": 6}', encoding="utf-8")

    from scripts.runner.execute_pipeline import PipelineArgs, handle_hitl_command

    status_rc = handle_hitl_command(
        PipelineArgs(project="demo", hitl_command="status"),
        repo_root,
    )
    status = json.loads(capsys.readouterr().out)

    guide_rc = handle_hitl_command(
        PipelineArgs(
            project="demo",
            hitl_command="guide",
            hitl_stage=6,
            message="Check citations before release.",
        ),
        repo_root,
    )
    capsys.readouterr()

    validate_rc = handle_hitl_command(
        PipelineArgs(
            project="demo",
            hitl_command="validate-response",
            response_file=str(response_path),
        ),
        repo_root,
    )
    validation = json.loads(capsys.readouterr().out)

    assert status_rc == 0
    assert status["mode"] == "full-auto"
    assert guide_rc == 0
    assert (repo_root / "projects" / "demo" / "output" / "hitl" / "guidance" / "stage-06.md").read_text(
        encoding="utf-8"
    ) == "Check citations before release.\n"
    assert validate_rc == 0
    assert validation["valid"] is True


def test_hitl_history_returns_structured_decisions(tmp_path: Path) -> None:
    controller = HitlController(project_output_dir=tmp_path, mode=HitlMode.GATE_ONLY)
    controller.guide(stage_num=4, message="Inspect source tiers.")
    controller.reject(message="Not grounded enough.")

    history = controller.history()

    assert [row["action"] for row in history] == ["guide", "reject"]
    assert history[0]["stage_num"] == 4


def test_stage_policy_pause_before_does_not_checkpoint_stage(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    output_dir = repo_root / "projects" / "p" / "output"
    output_dir.mkdir(parents=True)
    control = PipelineControlConfig(
        hitl_mode="custom",
        stage_policies={1: StagePolicy(pause_before=True, require_approval=True)},
    )
    executor = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root, control=control))
    ran = {"value": False}

    def stage() -> bool:
        ran["value"] = True
        return True

    result = executor._execute_stage(1, "Policy Stage", stage)

    assert result.success is True
    assert result.hitl_pause is True
    assert result.stage_completed is False
    assert ran["value"] is False
    assert json.loads((output_dir / "hitl" / "waiting.json").read_text(encoding="utf-8"))["reason"] == (
        "approval_required"
    )


def test_hitl_pause_writes_agent_context_and_response_schema(tmp_path: Path) -> None:
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "validation_report.json").write_text(
        '{"checks": {"Evidence registry": false}, "summary": {"all_passed": false}}',
        encoding="utf-8",
    )
    declared = tmp_path / "reports" / "validation_report.json"
    controller = HitlController(project_output_dir=tmp_path, mode=HitlMode.GATE_ONLY)
    spec = StageSpec(
        "Output Validation",
        lambda: True,
        contract=StageContract(
            output_artifacts=("output/reports/validation_report.json",),
            definition_of_done="Validation report reviewed.",
            gate="publication_readiness",
        ),
    )

    controller.pause(
        stage_num=6,
        stage_name=spec.name,
        reason="publication_readiness",
        context_summary="Review evidence.",
        stage_spec=spec,
    )

    context = json.loads((tmp_path / "hitl" / "agent_context.json").read_text(encoding="utf-8"))
    schema = json.loads((tmp_path / "hitl" / "agent_response.schema.json").read_text(encoding="utf-8"))
    assert context["stage"]["num"] == 6
    assert context["stage"]["contract"]["gate"] == "publication_readiness"
    assert context["declared_artifacts"][0]["path"] == str(declared.relative_to(tmp_path))
    assert context["validation_status"]["checks"]["Evidence registry"] is False
    assert "approve" in context["permitted_actions"]
    assert schema["properties"]["action"]["enum"] == ["approve", "reject", "guide", "resume", "abort"]


def test_hitl_agent_response_validation_and_recording(tmp_path: Path) -> None:
    controller = HitlController(project_output_dir=tmp_path, mode=HitlMode.GATE_ONLY)
    controller.pause(stage_num=4, stage_name="Project Analysis", reason="experiment_method_design")
    response_path = tmp_path / "response.json"
    response_path.write_text('{"action": "guide", "message": "Add an ablation.", "stage_num": 4}', encoding="utf-8")

    validation = validate_agent_response_file(response_path)
    recorded = controller.respond_from_file(response_path)

    assert validation.valid is True
    assert recorded["action"] == "guide"
    assert (tmp_path / "hitl" / "guidance" / "stage-04.md").read_text(encoding="utf-8") == "Add an ablation.\n"
    assert '"action": "guide"' in (tmp_path / "hitl" / "decisions.jsonl").read_text(encoding="utf-8")


def test_hitl_agent_response_rejects_unknown_action(tmp_path: Path) -> None:
    response_path = tmp_path / "response.json"
    response_path.write_text('{"action": "edit", "message": "Open editor"}', encoding="utf-8")

    validation = validate_agent_response_file(response_path)

    assert validation.valid is False
    assert any("unsupported action" in issue for issue in validation.issues)


def test_smart_pause_scores_validation_artifact_telemetry_and_rejections(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    hitl = tmp_path / "hitl"
    reports.mkdir()
    hitl.mkdir()
    (reports / "validation_report.json").write_text(
        '{"checks": {"Evidence registry": false}, "output_statistics": {"design_validation_issues": ["missing baseline"]}}',
        encoding="utf-8",
    )
    (reports / "artifact_manifest.json").write_text(
        '{"issues": ["changed artifact: output/data/result.json"]}',
        encoding="utf-8",
    )
    (reports / "telemetry.json").write_text(
        '{"warnings": [{"warning_type": "slow_stage", "stage_name": "PDF Rendering", "message": "slow"}]}',
        encoding="utf-8",
    )
    (reports / "autoresearch_readiness.json").write_text(
        json.dumps(
            {
                "valid": False,
                "issues": [
                    {
                        "severity": "error",
                        "code": "AUTORESEARCH.ARTIFACT_MISSING",
                        "message": "missing artifact",
                        "source_path": "output/data/result.csv",
                        "suggested_action": "regenerate",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (hitl / "decisions.jsonl").write_text(
        '{"action":"reject","stage_num":6,"stage_name":"Output Validation","message":"not grounded"}\n',
        encoding="utf-8",
    )

    recommendations = compute_pause_recommendations(tmp_path)
    output_path = write_pause_recommendations(tmp_path, recommendations)

    reason_codes = {reason for rec in recommendations for reason in rec.reason_codes}
    assert {
        "validation_failed",
        "artifact_drift",
        "slow_telemetry",
        "human_rejection",
        "design_validation",
        "autoresearch_readiness",
    }.issubset(reason_codes)
    assert recommendations[0].score > 0
    assert output_path == tmp_path / "reports" / "pause_recommendations.json"


def test_snapshot_creation_and_comparison_reports_artifact_and_evidence_deltas(tmp_path: Path) -> None:
    output_a = tmp_path / "a"
    output_b = tmp_path / "b"
    for output, digest, evidence_count in ((output_a, "aaa", 1), (output_b, "bbb", 2)):
        (output / "reports").mkdir(parents=True)
        (output / "reports" / "artifact_manifest.json").write_text(
            json.dumps({"entries": [{"path": "output/pdf/paper.pdf", "sha256": digest}], "issues": []}),
            encoding="utf-8",
        )
        (output / "reports" / "evidence_registry.json").write_text(
            json.dumps({"facts": [{"kind": "number", "value": str(i)} for i in range(evidence_count)]}),
            encoding="utf-8",
        )
        (output / "reports" / "validation_report.json").write_text(
            '{"summary": {"all_passed": true}, "checks": {"PDF validation": true}}',
            encoding="utf-8",
        )

    snap_a = create_snapshot(output_a, stage_num=6, stage_name="Output Validation")
    snap_b = create_snapshot(output_b, stage_num=6, stage_name="Output Validation")
    comparison = compare_snapshots(snap_a.path, snap_b.path)
    markdown = snapshot_compare_to_markdown(comparison)

    assert snap_a.path.exists()
    assert str(tmp_path) not in snap_a.to_dict()["path"]
    assert str(tmp_path) not in comparison.to_dict()["left"]
    assert str(tmp_path) not in comparison.to_dict()["right"]
    assert comparison.artifact_deltas
    assert comparison.evidence_delta == 1
    assert "output/pdf/paper.pdf" in markdown


def test_run_lessons_capture_failures_and_hitl_decisions(tmp_path: Path) -> None:
    hitl_dir = tmp_path / "hitl"
    hitl_dir.mkdir()
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (hitl_dir / "decisions.jsonl").write_text(
        '{"action":"reject","stage_num":6,"stage_name":"Output Validation","message":"citation drift"}\n',
        encoding="utf-8",
    )
    (reports_dir / "artifact_manifest.json").write_text(
        '{"issues": ["missing declared output: output/pdf"]}\n',
        encoding="utf-8",
    )
    (reports_dir / "pause_recommendations.json").write_text(
        '{"recommendations": [{"stage_num": 6, "stage_name": "Output Validation", "reason": "low confidence"}]}\n',
        encoding="utf-8",
    )
    (reports_dir / "validation_report.json").write_text(
        '{"checks": {"Evidence registry": false}, "output_statistics": {"evidence_issues": ["unsupported 43"]}}\n',
        encoding="utf-8",
    )
    results = [
        PipelineStageResult(1, "Environment Setup", True, 0.2),
        PipelineStageResult(6, "Output Validation", False, 0.4, exit_code=1, error_message="bad citation"),
    ]

    lessons = collect_run_lessons(results, project_output_dir=tmp_path)
    written = write_run_lessons(tmp_path, lessons)

    assert "pipeline_failure" in [lesson.category for lesson in lessons]
    assert "human_intervention" in [lesson.category for lesson in lessons]
    assert "artifact_drift" in [lesson.category for lesson in lessons]
    assert "validation_defect" in [lesson.category for lesson in lessons]
    assert "pause_recommendation" in [lesson.category for lesson in lessons]
    assert all(str(tmp_path) not in lesson.source for lesson in lessons)
    assert written.jsonl_path.exists()
    assert written.markdown_path.exists()
    assert written.next_run_context_path.exists()
    assert "bad citation" in written.markdown_path.read_text(encoding="utf-8")
    assert "not automatically consumed" in written.next_run_context_path.read_text(encoding="utf-8")


def test_executor_honors_stage_retry_policy(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "projects" / "p" / "output").mkdir(parents=True)
    executor = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root))
    attempts = {"count": 0}

    def flaky_stage() -> bool:
        attempts["count"] += 1
        return attempts["count"] == 2

    spec = StageSpec(
        "Retry Stage",
        flaky_stage,
        contract=StageContract(retry_policy=1),
    )

    result = executor._execute_stage(1, spec.name, spec.func, stage_spec=spec)

    assert result.success is True
    assert attempts["count"] == 2


def test_executor_retries_stage_exceptions_when_policy_allows(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "projects" / "p" / "output").mkdir(parents=True)
    executor = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root))
    attempts = {"count": 0}

    def flaky_stage() -> bool:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary failure")
        return True

    spec = StageSpec(
        "Retry Exception Stage",
        flaky_stage,
        contract=StageContract(retry_policy=1),
    )

    result = executor._execute_stage(1, spec.name, spec.func, stage_spec=spec)

    assert result.success is True
    assert attempts["count"] == 2


def test_executor_gate_only_mode_pauses_after_gated_stage(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    output_dir = repo_root / "projects" / "p" / "output"
    output_dir.mkdir(parents=True)
    executor = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root, hitl_mode="gate-only"))
    spec = StageSpec(
        "Output Validation",
        lambda: True,
        contract=StageContract(
            definition_of_done="Validation report reviewed.",
            gate="publication_readiness",
        ),
    )

    result = executor._execute_stage(6, spec.name, spec.func, stage_spec=spec)

    assert result.success is True
    assert result.hitl_pause is True
    waiting = json.loads((output_dir / "hitl" / "waiting.json").read_text(encoding="utf-8"))
    assert waiting["reason"] == "publication_readiness"
