"""Tests for adaptive pipeline control surfaces.

These tests cover the AutoResearchClaw-inspired additions without making the
template pipeline autonomous: stage contracts, explicit hooks, lightweight HITL,
and run lessons remain opt-in and reproducible.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from infrastructure.core.pipeline.dag import PipelineDAG
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.artifacts import (
    aggregate_artifact_manifests,
    validate_artifact_manifest,
    write_stage_artifact_manifest,
)
from infrastructure.core.pipeline.control import load_pipeline_control_config
from infrastructure.core.pipeline.hitl import HitlController, HitlMode, validate_agent_response_file
from infrastructure.core.pipeline.hooks import HookEvent, StageHookContext, run_stage_hooks
from infrastructure.core.pipeline.smart_pause import compute_pause_recommendations, write_pause_recommendations
from infrastructure.core.pipeline.snapshot import compare_snapshots, create_snapshot, snapshot_compare_to_markdown
from infrastructure.core.pipeline.types import (
    PipelineConfig,
    PipelineControlConfig,
    PipelineStageResult,
    StageContract,
    StageHooks,
    StageSpec,
    StagePolicy,
)
from infrastructure.reporting.run_lessons import collect_run_lessons, write_run_lessons


def test_dag_parses_contract_and_hooks_from_yaml(tmp_path: Path) -> None:
    yaml_path = tmp_path / "pipeline.yaml"
    yaml_path.write_text(
        """
stages:
  - name: Source Audit
    method: run_source_audit
    tags: [core, validation]
    contract:
      input_artifacts: ["manuscript/"]
      output_artifacts: ["output/reports/source_audit.json"]
      definition_of_done: "Source claims are grounded."
      failure_code: "SOURCE_AUDIT_FAILED"
      retry_policy: 1
      gate: "literature_source_quality"
      rollback_to: "Project Analysis"
    hooks:
      timeout_seconds: 7
      pre_stage:
        - ["python", "hooks/pre.py"]
      post_stage:
        - ["python", "hooks/post.py"]
""",
        encoding="utf-8",
    )

    dag = PipelineDAG.from_yaml(yaml_path)
    stage = dag.stages[0]

    assert stage.contract.input_artifacts == ("manuscript/",)
    assert stage.contract.output_artifacts == ("output/reports/source_audit.json",)
    assert stage.contract.definition_of_done == "Source claims are grounded."
    assert stage.contract.failure_code == "SOURCE_AUDIT_FAILED"
    assert stage.contract.retry_policy == 1
    assert stage.contract.gate == "literature_source_quality"
    assert stage.contract.rollback_to == "Project Analysis"
    assert stage.hooks.timeout_seconds == 7
    assert stage.hooks.pre_stage == (("python", "hooks/pre.py"),)
    assert stage.hooks.post_stage == (("python", "hooks/post.py"),)


def test_unknown_contract_key_raises(tmp_path: Path) -> None:
    yaml_path = tmp_path / "pipeline.yaml"
    yaml_path.write_text(
        """
stages:
  - name: Bad
    method: run_bad
    contract:
      unsupported: true
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported contract key"):
        PipelineDAG.from_yaml(yaml_path)


def test_control_config_merges_project_and_cli_precedence(tmp_path: Path) -> None:
    default_yaml = tmp_path / "default.yaml"
    project_yaml = tmp_path / "project.yaml"
    default_yaml.write_text(
        """
stages: []
control:
  hitl_mode: gate-only
  smart_pause_action: report
  custom_gate_stages: [4]
  stage_policies:
    "2":
      pause_after: true
      require_approval: true
""",
        encoding="utf-8",
    )
    project_yaml.write_text(
        """
stages: []
control:
  hitl_mode: checkpoint
  stage_policies:
    "2":
      pause_after: false
      allow_guidance: false
    "5":
      pause_before: true
""",
        encoding="utf-8",
    )

    config = load_pipeline_control_config(
        default_yaml,
        project_yaml=project_yaml,
        cli_hitl_mode="custom",
    )

    assert config.hitl_mode == "custom"
    assert config.smart_pause_action == "report"
    assert config.custom_gate_stages == (4,)
    assert config.stage_policies[2].pause_after is False
    assert config.stage_policies[2].require_approval is True
    assert config.stage_policies[2].allow_guidance is False
    assert config.stage_policies[5].pause_before is True


def test_unknown_control_key_raises(tmp_path: Path) -> None:
    yaml_path = tmp_path / "pipeline.yaml"
    yaml_path.write_text(
        """
stages: []
control:
  not_supported: true
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported control key"):
        load_pipeline_control_config(yaml_path)


def test_stage_spec_carries_contract_and_hooks() -> None:
    dag = PipelineDAG.from_dict(
        {
            "stages": [
                {
                    "name": "A",
                    "method": "run_a",
                    "contract": {
                        "output_artifacts": ["a.json"],
                        "gate": "publication_readiness",
                    },
                    "hooks": {"on_fail": [["python", "hooks/fail.py"]]},
                }
            ]
        }
    )

    class Executor:
        config = PipelineConfig(project_name="p", repo_root=Path("/tmp"))

        def run_a(self) -> bool:
            return True

    spec = dag.to_stage_specs(Executor())[0]

    assert spec.name == "A"
    assert spec.contract.output_artifacts == ("a.json",)
    assert spec.contract.gate == "publication_readiness"
    assert spec.hooks.on_fail == (("python", "hooks/fail.py"),)


def test_stage_hooks_receive_environment_and_context(tmp_path: Path) -> None:
    hook_script = tmp_path / "hook.py"
    log_path = tmp_path / "hook-log.json"
    hook_script.write_text(
        """
import json
import os
from pathlib import Path

context_path = Path(os.environ["TEMPLATE_STAGE_CONTEXT"])
payload = {
    "project": os.environ["TEMPLATE_PROJECT"],
    "stage": os.environ["TEMPLATE_STAGE_NAME"],
    "stage_num": os.environ["TEMPLATE_STAGE_NUM"],
    "run_dir": os.environ["TEMPLATE_RUN_DIR"],
    "context": json.loads(context_path.read_text(encoding="utf-8")),
}
Path(os.environ["HOOK_LOG"]).write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
""",
        encoding="utf-8",
    )

    hooks = StageHooks(pre_stage=((sys.executable, str(hook_script)),), timeout_seconds=5, run_in_ci=True)
    context = StageHookContext(
        project_name="template_code_project",
        stage_name="Source Audit",
        stage_num=3,
        run_dir=tmp_path,
        status="running",
    )
    env = {"HOOK_LOG": str(log_path)}

    results = run_stage_hooks(hooks, HookEvent.PRE_STAGE, context, extra_env=env)

    assert len(results) == 1
    assert results[0].success is True
    payload = json.loads(log_path.read_text(encoding="utf-8"))
    assert payload["project"] == "template_code_project"
    assert payload["stage"] == "Source Audit"
    assert payload["stage_num"] == "3"
    assert payload["context"]["status"] == "running"


def test_hooks_disabled_in_ci_unless_declared_run_in_ci(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    hook_script = tmp_path / "hook.py"
    hook_script.write_text("from pathlib import Path; Path('ran.txt').write_text('yes')\n", encoding="utf-8")
    monkeypatch.setenv("CI", "true")

    hooks = StageHooks(pre_stage=((sys.executable, str(hook_script)),), timeout_seconds=5)
    context = StageHookContext(
        project_name="template_code_project",
        stage_name="A",
        stage_num=1,
        run_dir=tmp_path,
        status="running",
    )

    results = run_stage_hooks(hooks, HookEvent.PRE_STAGE, context)

    assert results == []
    assert not (tmp_path / "ran.txt").exists()


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

    from scripts.execute_pipeline import PipelineArgs, handle_hitl_command

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


def test_stage_artifact_manifest_records_hashes_and_contract_issues(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_dir = repo_root / "projects" / "p"
    (project_dir / "output" / "data").mkdir(parents=True)
    (project_dir / "output" / "logs").mkdir()
    (project_dir / "output" / ".checkpoints").mkdir()
    (project_dir / "output" / "reports" / "snapshots").mkdir(parents=True)
    (project_dir / "output" / "data" / "result.json").write_text('{"ok": true}\n', encoding="utf-8")
    (project_dir / "output" / "data" / ".result.atomic.json").write_text("", encoding="utf-8")
    (project_dir / "output" / "logs" / "pipeline.log").write_text("ignore me\n", encoding="utf-8")
    (project_dir / "output" / ".checkpoints" / "pipeline_checkpoint.json").write_text("{}", encoding="utf-8")
    (project_dir / "output" / "reports" / "artifact_manifest.json").write_text("{}", encoding="utf-8")
    (project_dir / "output" / "reports" / "evidence_registry.json").write_text("{}", encoding="utf-8")
    (project_dir / "output" / "reports" / "snapshots" / "stage-01.json").write_text("{}", encoding="utf-8")
    (project_dir / "output" / "slides").mkdir()
    (project_dir / "output" / "slides" / "section_slides.aux").write_text("ignore me\n", encoding="utf-8")
    contract = StageContract(output_artifacts=("projects/{project}/output/data/", "projects/{project}/output/pdf/"))

    manifest = write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project_dir,
        stage_num=4,
        stage_name="Project Analysis",
        contract=contract,
    )
    aggregate = aggregate_artifact_manifests(project_dir / "output")
    validation = validate_artifact_manifest(aggregate)

    assert manifest.entries[0].sha256
    assert manifest.entries[0].contract_match is True
    assert all("logs/" not in entry.path for entry in manifest.entries)
    assert all(".checkpoints/" not in entry.path for entry in manifest.entries)
    assert all("artifact_manifest.json" not in entry.path for entry in manifest.entries)
    assert all("evidence_registry.json" not in entry.path for entry in manifest.entries)
    assert all("snapshots/" not in entry.path for entry in manifest.entries)
    assert all("/." not in entry.path for entry in manifest.entries)
    assert all(not entry.path.endswith(".aux") for entry in manifest.entries)
    assert any("missing declared output" in issue for issue in validation.issues)
    assert (project_dir / "output" / "reports" / "artifact_manifest.json").exists()


def test_stage_artifact_manifest_accepts_symlinked_private_project_contracts(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    private_root = tmp_path / "private" / "active"
    project_dir = private_root / "p"
    linked_project = repo_root / "projects" / "p"
    output_file = project_dir / "output" / "data" / "result.json"
    output_file.parent.mkdir(parents=True)
    linked_project.parent.mkdir(parents=True)
    linked_project.symlink_to(project_dir, target_is_directory=True)
    output_file.write_text('{"ok": true}\n', encoding="utf-8")

    manifest = write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project_dir,
        stage_num=4,
        stage_name="Project Analysis",
        contract=StageContract(output_artifacts=("projects/{project}/output/data/",)),
    )
    validation = validate_artifact_manifest(manifest, project_dir=project_dir)

    assert [entry.contract_match for entry in manifest.entries] == [True]
    assert validation.issues == ()


def test_stage_artifact_manifest_matches_nested_template_contracts(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_dir = repo_root / "projects" / "templates" / "template_demo"
    output_file = project_dir / "output" / "data" / "result.json"
    output_file.parent.mkdir(parents=True)
    (repo_root / "output" / "templates" / "template_demo").mkdir(parents=True)
    output_file.write_text('{"ok": true}\n', encoding="utf-8")

    manifest = write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project_dir,
        stage_num=4,
        stage_name="Project Analysis",
        contract=StageContract(output_artifacts=("projects/{project}/output/", "output/{project}/")),
    )
    validation = validate_artifact_manifest(manifest, project_dir=project_dir)

    assert [entry.contract_match for entry in manifest.entries] == [True]
    assert validation.issues == ()


def test_default_environment_setup_contract_allows_setup_hook_outputs() -> None:
    pipeline_path = Path(__file__).resolve().parents[3] / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
    dag = PipelineDAG.from_yaml(pipeline_path)
    setup = next(stage for stage in dag.stages if stage.name == "Environment Setup")

    assert "projects/{project}/output/" in setup.contract.output_artifacts


def test_default_test_stage_contracts_allow_generated_project_outputs() -> None:
    pipeline_path = Path(__file__).resolve().parents[3] / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
    dag = PipelineDAG.from_yaml(pipeline_path)
    test_stages = {stage.name: stage for stage in dag.stages if stage.name in {"Infrastructure Tests", "Project Tests"}}

    assert test_stages["Infrastructure Tests"].contract.output_artifacts == ("projects/{project}/output/",)
    assert test_stages["Project Tests"].contract.output_artifacts == ("projects/{project}/output/",)


def test_stage_artifact_manifest_detects_changed_hash(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_dir = repo_root / "projects" / "p"
    output_file = project_dir / "output" / "data" / "result.json"
    output_file.parent.mkdir(parents=True)
    output_file.write_text('{"ok": true}\n', encoding="utf-8")

    manifest = write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project_dir,
        stage_num=4,
        stage_name="Project Analysis",
        contract=StageContract(output_artifacts=("projects/{project}/output/data/",)),
    )
    output_file.write_text('{"ok": false}\n', encoding="utf-8")

    validation = validate_artifact_manifest(manifest, project_dir=project_dir)

    assert any("changed artifact" in issue for issue in validation.issues)


def test_stage_artifact_manifest_validates_latest_hash_per_path(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_dir = repo_root / "projects" / "p"
    output_file = project_dir / "output" / "data" / "result.json"
    output_file.parent.mkdir(parents=True)
    output_file.write_text('{"ok": true}\n', encoding="utf-8")

    write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project_dir,
        stage_num=4,
        stage_name="Project Analysis",
        contract=StageContract(output_artifacts=("projects/{project}/output/data/",)),
    )
    output_file.write_text('{"ok": false}\n', encoding="utf-8")
    write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project_dir,
        stage_num=5,
        stage_name="PDF Rendering",
        contract=StageContract(output_artifacts=("projects/{project}/output/data/",)),
    )

    aggregate = aggregate_artifact_manifests(project_dir / "output")
    validation = validate_artifact_manifest(aggregate, project_dir=project_dir)

    assert not any("changed artifact" in issue for issue in validation.issues)
