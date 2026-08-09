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
from infrastructure.core.pipeline.control import load_pipeline_control_config
from infrastructure.core.pipeline.hooks import HookEvent, StageHookContext, run_stage_hooks
from infrastructure.core.pipeline.types import (
    PipelineConfig,
    StageHooks,
)


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


def test_timed_out_hook_normalizes_partial_output_to_text(tmp_path: Path) -> None:
    """TimeoutExpired may expose bytes even when subprocess text mode is enabled."""
    hook_script = tmp_path / "slow_hook.py"
    hook_script.write_text(
        "import time\nprint('partial output', flush=True)\ntime.sleep(2)\n",
        encoding="utf-8",
    )
    hooks = StageHooks(
        pre_stage=((sys.executable, str(hook_script)),),
        timeout_seconds=1,
        run_in_ci=True,
    )
    context = StageHookContext(
        project_name="template_code_project",
        stage_name="Slow Hook",
        stage_num=1,
        run_dir=tmp_path,
        status="running",
    )

    results = run_stage_hooks(hooks, HookEvent.PRE_STAGE, context)

    assert len(results) == 1
    assert results[0].exit_code == 124
    assert results[0].stdout == "partial output\n"
    assert isinstance(results[0].stderr, str)
