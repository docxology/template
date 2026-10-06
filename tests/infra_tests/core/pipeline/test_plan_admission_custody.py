"""Real declaration and pre-hook controls for exact stage admission."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.hitl import HitlController
from infrastructure.core.pipeline.outcomes import StageStatus
from infrastructure.core.pipeline.types import PipelineConfig, PipelineControlConfig, StagePolicy
from tests._support.projects import make_project

pytestmark = pytest.mark.timeout(120)


def _write_pipeline(project: Path, *, require_approval: bool, hook_code: str | None = None) -> None:
    stage: dict[str, object] = {
        "name": "Consume reviewed input",
        "key": "consume",
        "script": "scripts/consume.py",
        "contract": {
            "input_artifacts": ["output/data/reviewed.txt"],
            "output_artifacts": ["output/data/stage-marker.txt"],
            "definition_of_done": "The actual child consumes the originally admitted input.",
            "failure_code": "INPUT_CUSTODY_FAILED",
        },
    }
    if hook_code is not None:
        stage["hooks"] = {
            "pre_stage": [[sys.executable, "-I", "-c", hook_code]],
            "timeout_seconds": 30,
            "run_in_ci": True,
        }
    (project / "pipeline.yaml").write_text(
        yaml.safe_dump(
            {
                "stages": [stage],
                "telemetry": {"enabled": False},
                "control": {"stage_policies": {1: {"require_approval": require_approval}}},
            }
        ),
        encoding="utf-8",
    )


def _config(tmp_path: Path, *, require_approval: bool, hook_code: str | None = None) -> PipelineConfig:
    project = make_project(tmp_path, with_manuscript=True, with_output=True)
    (project / "output/data/reviewed.txt").write_text("reviewed", encoding="utf-8")
    script = tmp_path / "scripts/consume.py"
    script.parent.mkdir()
    script.write_text(
        "from pathlib import Path\n"
        "source = Path('projects/template_test/output/data/reviewed.txt')\n"
        "with source.with_name('stage-marker.txt').open('a') as marker:\n"
        "    marker.write(source.read_text())\n",
        encoding="utf-8",
    )
    _write_pipeline(project, require_approval=require_approval, hook_code=hook_code)
    return PipelineConfig("template_test", tmp_path, clean=False, run_timeout_seconds=90)


def test_executor_refreshes_new_source_approval_before_its_first_execution(tmp_path: Path) -> None:
    config = _config(tmp_path, require_approval=False)
    executor = PipelineExecutor(config)
    _write_pipeline(config.project_dir, require_approval=True)

    results = executor.execute_pipeline()

    assert executor.run_result(results).exit_code == 75
    assert results[0].outcome is not None and results[0].outcome.status is StageStatus.PAUSED
    assert results[0].outcome.child_exit_code is None
    assert not (config.project_dir / "output/data/stage-marker.txt").exists()
    assert (
        HitlController(project_output_dir=config.project_dir / "output").status()["waiting"]["reason"]
        == "approval_required"
    )


@pytest.mark.parametrize("authority", ["config", "executor"])
@pytest.mark.parametrize("require_approval", [False, True])
def test_deliberate_control_change_after_preview_refreshes_policy(
    tmp_path: Path,
    authority: str,
    require_approval: bool,
) -> None:
    config = _config(tmp_path, require_approval=not require_approval)
    executor = PipelineExecutor(config)
    assert executor.preview_stage_names() == ("Consume reviewed input",)
    original = executor.execution_plan
    assert original is not None and original.stages[0].policy.require_approval is not require_approval
    override = PipelineControlConfig(
        stage_policies={1: StagePolicy(require_approval=require_approval)},
        stage_policy_fields={1: frozenset({"require_approval"})},
    )
    if authority == "config":
        config.control = override
    else:
        executor.control_config = override

    results = executor.execute_pipeline()

    assert executor.execution_plan is not None and executor.execution_plan.digest != original.digest
    assert executor.execution_plan.stages[0].policy.require_approval is require_approval
    assert executor.run_result(results).exit_code == (75 if require_approval else 0)
    marker = config.project_dir / "output/data/stage-marker.txt"
    if require_approval:
        assert results[0].outcome is not None and results[0].outcome.child_exit_code is None
        assert not marker.exists()
    else:
        assert marker.read_text() == "reviewed"


def test_unchanged_preview_keeps_exact_plan_and_executes_the_admitted_child(tmp_path: Path) -> None:
    config = _config(tmp_path, require_approval=False)
    executor = PipelineExecutor(config)
    executor.preview_stage_names()
    original = executor.execution_plan

    results = executor.execute_pipeline()

    assert executor.execution_plan is not None and original is not None
    assert executor.execution_plan.digest == original.digest
    assert executor.execution_plan.to_dict() == original.to_dict()
    assert executor.run_result(results).complete
    assert (config.project_dir / "output/data/stage-marker.txt").read_text() == "reviewed"


@pytest.mark.parametrize("authority", ["config", "executor"])
@pytest.mark.parametrize("require_approval", [False, True])
def test_deliberate_control_overrides_retain_precedence_after_source_refresh(
    tmp_path: Path, authority: str, require_approval: bool
) -> None:
    config = _config(tmp_path, require_approval=not require_approval)
    control = PipelineControlConfig(
        stage_policies={1: StagePolicy(require_approval=require_approval)},
        stage_policy_fields={1: frozenset({"require_approval"})},
    )
    if authority == "config":
        config.control = control
    executor = PipelineExecutor(config)
    if authority == "executor":
        executor.control_config = control
    _write_pipeline(config.project_dir, require_approval=not require_approval)

    results = executor.execute_pipeline()

    assert executor.run_result(results).exit_code == (75 if require_approval else 0)
    marker = config.project_dir / "output/data/stage-marker.txt"
    if require_approval:
        assert results[0].outcome is not None and results[0].outcome.status is StageStatus.PAUSED
        assert not marker.exists()
    else:
        assert results[0].outcome is not None and results[0].outcome.status is StageStatus.SUCCEEDED
        assert results[0].outcome.child_exit_code == 0
        assert marker.read_text() == "reviewed"


@pytest.mark.parametrize("require_approval", [False, True])
def test_actual_pre_hook_input_substitution_blocks_stage_before_execution(
    tmp_path: Path, require_approval: bool
) -> None:
    hook_code = (
        "from pathlib import Path\n"
        "Path('data/reviewed.txt').write_text('unreviewed')\n"
        "Path('.pipeline/pre-hook-ran.txt').write_text('actual hook ran')\n"
    )
    config = _config(tmp_path, require_approval=require_approval, hook_code=hook_code)
    executor = PipelineExecutor(config)
    output = config.project_dir / "output"
    if require_approval:
        paused = executor.execute_pipeline()
        assert executor.run_result(paused).exit_code == 75
        assert not (output / ".pipeline/pre-hook-ran.txt").exists()
        assert not (output / "data/stage-marker.txt").exists()
        HitlController(project_output_dir=output).approve("Reviewed the exact original input bytes.")
        executor.config.resume = True

    results = executor.execute_pipeline()

    assert (output / ".pipeline/pre-hook-ran.txt").read_text() == "actual hook ran"
    assert (output / "data/reviewed.txt").read_text() == "unreviewed"
    assert executor.run_result(results).exit_code == 75
    assert results[0].outcome is not None and results[0].outcome.status is StageStatus.BLOCKED
    assert results[0].exit_code == 75
    assert results[0].outcome.child_exit_code is None
    assert results[0].error_message
    assert not (output / "data/stage-marker.txt").exists()


def test_unchanged_approved_input_and_actual_pre_hook_execute_child_once(tmp_path: Path) -> None:
    hook_code = "from pathlib import Path\nPath('.pipeline/pre-hook-ran.txt').write_text('actual hook ran')\n"
    config = _config(tmp_path, require_approval=True, hook_code=hook_code)
    executor = PipelineExecutor(config)
    output = config.project_dir / "output"
    paused = executor.execute_pipeline()
    assert executor.run_result(paused).exit_code == 75
    assert not (output / ".pipeline/pre-hook-ran.txt").exists()
    HitlController(project_output_dir=output).approve("The original consumed input is unchanged.")
    executor.config.resume = True

    results = executor.execute_pipeline()

    assert executor.run_result(results).complete
    assert results[0].outcome is not None and results[0].outcome.child_exit_code == 0
    assert (output / ".pipeline/pre-hook-ran.txt").read_text() == "actual hook ran"
    assert (output / "data/stage-marker.txt").read_text() == "reviewed"
    decisions = HitlController(project_output_dir=output).history()
    assert len([row for row in decisions if row["action"] == "approve"]) == 1
    assert len([row for row in decisions if row["action"] == "consume"]) == 1
    continuation = executor.execute_pipeline()
    assert executor.run_result(continuation).complete
    assert (output / "data/stage-marker.txt").read_text() == "reviewed", "a second child would append again"
