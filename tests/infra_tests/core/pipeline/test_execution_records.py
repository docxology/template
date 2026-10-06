"""Actual execution records preserve custody, original outcomes, and refusal."""

from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest
import yaml

from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.execution_records import write_execution_record
from infrastructure.core.pipeline.outcomes import StageStatus
from infrastructure.core.pipeline.types import PipelineConfig
from infrastructure.core.pipeline.incremental import IncrementalConfig
from infrastructure.core.pipeline.hitl import HitlController

# Each case supervises real children and repeatedly revalidates source custody.
# This outer test budget includes the guardian's finite startup/reaping grace.
pytestmark = pytest.mark.timeout(90)


def _executor(root: Path, *, code: int = 0, incremental: bool = False) -> PipelineExecutor:
    project = root / "projects" / "demo"
    project.mkdir(parents=True)
    scripts = root / "scripts"
    scripts.mkdir()
    (scripts / "child.py").write_text(
        "from pathlib import Path\n"
        "value = Path('projects/demo/output/data/value.txt')\n"
        "value.parent.mkdir(parents=True, exist_ok=True)\n"
        "value.write_text('actual child output')\n"
        f"raise SystemExit({code})\n"
    )
    (project / "pipeline.yaml").write_text(
        yaml.safe_dump(
            {
                "telemetry": {"enabled": False},
                "stages": [
                    {
                        "name": "Child",
                        "key": "child",
                        "script": "scripts/child.py",
                        "contract": {"output_artifacts": ["output/data/value.txt"]},
                    }
                ],
            }
        )
    )
    return PipelineExecutor(
        PipelineConfig("demo", root, clean=False, run_timeout_seconds=90, incremental=IncrementalConfig(incremental))
    )


@pytest.mark.parametrize("code,aggregate", [(0, 0), (2, 1), (7, 1)])
def test_record_matches_real_child_and_resolved_plan(tmp_path: Path, code: int, aggregate: int) -> None:
    executor = _executor(tmp_path, code=code)
    results = executor.execute_pipeline()
    path = executor.config.project_dir / "output" / ".pipeline" / "execution.json"
    record = json.loads(path.read_text())
    assert record["exit_code"] == executor.run_result(results).exit_code == aggregate
    assert record["complete"] is (code == 0)
    assert record["schema_version"] == "template-execution-record/1"
    assert executor.execution_plan is not None
    assert record["plan"] == json.loads(json.dumps(executor.execution_plan.to_dict()))
    assert record["plan_digest"] == executor.execution_plan.digest
    assert record["expected_stage_keys"] == ["child"]
    assert record["outcomes"][0]["child_exit_code"] == code
    assert record["outcomes"][0]["attempt_exit_codes"] == [code]
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_cached_record_and_resume_keep_input_output_identity(tmp_path: Path) -> None:
    executor = _executor(tmp_path, incremental=True)
    assert executor.run_result(executor.execute_pipeline()).complete
    results = executor.execute_pipeline()
    assert results[0].outcome is not None and results[0].outcome.status is StageStatus.CACHED
    assert len(results[0].input_digest) == len(results[0].output_digest) == 64
    executor.config.resume = True
    assert executor.run_result(executor.execute_pipeline()).complete


def test_resume_checks_consumed_repository_document_bytes(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    document = tmp_path / "docs" / "input.md"
    document.parent.mkdir()
    document.write_text("consumed first version")
    declaration = executor.config.project_dir / "pipeline.yaml"
    payload = yaml.safe_load(declaration.read_text())
    payload["stages"][0]["contract"]["input_artifacts"] = ["docs/input.md"]
    declaration.write_text(yaml.safe_dump(payload))
    assert executor.run_result(executor.execute_pipeline()).complete
    checkpoint = executor.checkpoint_manager.checkpoint_file
    preserved = checkpoint.read_bytes()
    document.write_text("changed after completed checkpoint")
    executor.config.resume = True
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 75
    assert "Consumed input identity changed" in results[0].error_message
    assert results[0].outcome is not None and results[0].outcome.child_exit_code is None
    assert checkpoint.read_bytes() == preserved


def test_record_symlink_refusal_prevents_complete_result(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    results = executor.execute_pipeline()
    assert executor.run_result(results).complete
    path = executor.config.project_dir / "output" / ".pipeline" / "execution.json"
    path.unlink()
    sentinel = tmp_path / "outside.json"
    sentinel.write_text("unaltered external content")
    path.symlink_to(sentinel)
    results = write_execution_record(executor, results)
    assert executor.run_result(results).exit_code == 1
    assert results[-1].outcome is not None and results[-1].outcome.child_exit_code is None
    assert sentinel.read_text() == "unaltered external content"


def test_out_of_order_checkpoint_cannot_execute_missing_prefix(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    child = tmp_path / "scripts" / "child.py"
    child.write_text("from pathlib import Path\nPath('launched').touch()\n")
    (tmp_path / "scripts" / "second.py").write_text("pass\n")
    declaration = executor.config.project_dir / "pipeline.yaml"
    declaration.write_text(
        yaml.safe_dump(
            {
                "telemetry": {"enabled": False},
                "stages": [
                    {"name": "First", "key": "first", "script": "scripts/child.py"},
                    {"name": "Second", "key": "second", "script": "scripts/second.py", "depends_on": ["First"]},
                ],
            }
        )
    )
    assert executor.run_result(executor.execute_pipeline()).complete
    (tmp_path / "launched").unlink()
    checkpoint = executor.checkpoint_manager.checkpoint_file
    payload = json.loads(checkpoint.read_text())
    payload["stage_results"] = payload["stage_results"][1:]
    payload["last_stage_completed"] = 1
    checkpoint.write_text(json.dumps(payload))
    executor.config.resume = True
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 75
    assert "exact current plan prefix" in results[0].error_message
    assert not (tmp_path / "launched").exists()


def _paused_analysis(root: Path, *, prefix: bool) -> PipelineExecutor:
    executor = _executor(root)
    stage = root / "scripts/pipeline/stage_02_analysis.py"
    stage.parent.mkdir()
    stage.write_text(
        "from pathlib import Path\n"
        "target=Path('projects/demo/output/data/analysis-count.txt')\n"
        "target.parent.mkdir(parents=True,exist_ok=True)\n"
        "count=int(target.read_text()) if target.exists() else 0\n"
        "target.write_text(str(count+1))\n"
    )
    stages = [{"name": "Prefix", "key": "prefix", "script": "scripts/child.py"}] if prefix else []
    stages.append(
        {
            "name": "Scientific Work",
            "key": "scientific-work",
            "script": "scripts/pipeline/stage_02_analysis.py",
            "contract": {"output_artifacts": ["output/data/analysis-count.txt"]},
            **({"depends_on": ["Prefix"]} if prefix else {}),
        }
    )
    (executor.config.project_dir / "pipeline.yaml").write_text(
        yaml.safe_dump(
            {
                "telemetry": {"enabled": False},
                "stages": stages,
                "control": {"stage_policies": {len(stages): {"require_approval": True, "pause_before": True}}},
            }
        )
    )
    # The executor reads controls when constructed; use the finished declaration.
    return PipelineExecutor(executor.config)


@pytest.mark.timeout(240)
@pytest.mark.parametrize("prefix", [False, True])
def test_resume_approval_executes_unexecuted_analysis_once(tmp_path: Path, prefix: bool) -> None:
    executor = _paused_analysis(tmp_path, prefix=prefix)
    first = executor.execute_pipeline()
    assert executor.run_result(first).exit_code == 75
    target = executor.config.project_dir / "output/data/analysis-count.txt"
    assert not target.exists()
    checkpoint = executor.checkpoint_manager.checkpoint_file
    stored = json.loads(checkpoint.read_text())
    assert stored["last_stage_completed"] == int(prefix)
    controller = HitlController(project_output_dir=executor.config.project_dir / "output", mode="gate-only")
    controller.approve("Reviewed the exact current source and selected inputs.")
    executor.config.resume = True
    resumed = PipelineExecutor(executor.config)
    results = resumed.execute_pipeline()
    assert resumed.run_result(results).complete
    assert target.read_text() == "1"
    assert results[-1].outcome is not None and results[-1].outcome.status is StageStatus.SUCCEEDED
    assert results[-1].outcome.child_exit_code == 0
    decisions = [json.loads(line) for line in controller.decisions_path.read_text().splitlines()]
    assert [row["action"] for row in decisions].count("approve") == 1
    assert [row["action"] for row in decisions].count("consume") == 1
    completed_checkpoint = checkpoint.read_bytes()
    again = PipelineExecutor(executor.config)
    refused = again.execute_pipeline()
    assert again.run_result(refused).exit_code == 75
    assert "declaration identity only" in refused[0].error_message
    assert checkpoint.read_bytes() == completed_checkpoint
    assert target.read_text() == "1"


@pytest.mark.timeout(180)
def test_resume_rejection_preserves_unexecuted_analysis_and_checkpoint(tmp_path: Path) -> None:
    executor = _paused_analysis(tmp_path, prefix=True)
    assert executor.run_result(executor.execute_pipeline()).exit_code == 75
    checkpoint = executor.checkpoint_manager.checkpoint_file
    preserved = checkpoint.read_bytes()
    controller = HitlController(project_output_dir=executor.config.project_dir / "output", mode="gate-only")
    controller.reject("The proposed analysis is not accepted.")
    executor.config.resume = True
    resumed = PipelineExecutor(executor.config)
    results = resumed.execute_pipeline()
    assert resumed.run_result(results).exit_code == 1
    assert results[-1].outcome is not None and results[-1].outcome.status is StageStatus.REJECTED
    assert not (executor.config.project_dir / "output/data/analysis-count.txt").exists()
    assert checkpoint.read_bytes() == preserved


@pytest.mark.timeout(240)
def test_failed_resume_cannot_rebind_checkpoint_to_changed_output(tmp_path: Path) -> None:
    executor = _paused_analysis(tmp_path, prefix=True)
    (tmp_path / "scripts/pipeline/stage_02_analysis.py").write_text(
        "from pathlib import Path\n"
        "Path('projects/demo/output/data/value.txt').write_text('failed attempt output')\n"
        "raise SystemExit(7)\n"
    )
    executor = PipelineExecutor(executor.config)
    assert executor.run_result(executor.execute_pipeline()).exit_code == 75
    checkpoint = executor.checkpoint_manager.checkpoint_file
    preserved = checkpoint.read_bytes()
    HitlController(project_output_dir=executor.config.project_dir / "output", mode="gate-only").approve(
        "Reviewed the exact proposed failing analysis."
    )
    executor.config.resume = True
    resumed = PipelineExecutor(executor.config)
    results = resumed.execute_pipeline()
    assert resumed.run_result(results).exit_code == 1
    assert results[-1].outcome is not None and results[-1].outcome.child_exit_code == 7
    assert checkpoint.read_bytes() == preserved
    assert (executor.config.project_dir / "output/data/value.txt").read_text() == "failed attempt output"
    again = PipelineExecutor(executor.config)
    refused = again.execute_pipeline()
    assert again.run_result(refused).exit_code == 75
    assert "output" in refused[0].error_message.lower()
    assert checkpoint.read_bytes() == preserved


@pytest.mark.timeout(180)
def test_failed_fresh_run_cannot_rebind_checkpoint_to_changed_output(tmp_path: Path) -> None:
    executor = _paused_analysis(tmp_path, prefix=True)
    declaration = executor.config.project_dir / "pipeline.yaml"
    payload = yaml.safe_load(declaration.read_text())
    payload.pop("control")
    declaration.write_text(yaml.safe_dump(payload))
    (tmp_path / "scripts/pipeline/stage_02_analysis.py").write_text(
        "from pathlib import Path\n"
        "checkpoint=Path('projects/demo/output/.checkpoints/pipeline_checkpoint.json')\n"
        "Path('checkpoint-before-failure.json').write_bytes(checkpoint.read_bytes())\n"
        "Path('projects/demo/output/data/value.txt').write_text('failed fresh output')\n"
        "raise SystemExit(7)\n"
    )
    executor = PipelineExecutor(executor.config)
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 1
    assert results[-1].outcome is not None and results[-1].outcome.child_exit_code == 7
    checkpoint = executor.checkpoint_manager.checkpoint_file
    preserved = (tmp_path / "checkpoint-before-failure.json").read_bytes()
    assert checkpoint.read_bytes() == preserved
    executor.config.resume = True
    resumed = PipelineExecutor(executor.config)
    refused = resumed.execute_pipeline()
    assert resumed.run_result(refused).exit_code == 75
    assert "output" in refused[0].error_message.lower()
    assert checkpoint.read_bytes() == preserved
    assert (executor.config.project_dir / "output/data/value.txt").read_text() == "failed fresh output"
