"""Real process regressions for truthful outcomes and content-bound reuse."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.types import PipelineConfig, StageContract, StagePolicy, PipelineControlConfig
from infrastructure.core.pipeline.types import StageSpec
from infrastructure.core.pipeline.hitl import HitlController
from infrastructure.core.pipeline.outcomes import RunResult, StageOutcome, StageStatus
from infrastructure.core.pipeline.fingerprints import paths_digest, source_fingerprint
from infrastructure.core.pipeline.incremental import IncrementalConfig, HashManifest, load_hash_manifest
from infrastructure.core.pipeline.plan import resolve_execution_plan

pytestmark = pytest.mark.timeout(120)


def _executor(
    tmp_path: Path, code: str, *, allow_skip: bool = False, timeout: float = 90.0, incremental: bool = False
) -> PipelineExecutor:
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    for name in ("src", "tests", "manuscript"):
        (project / name).mkdir()
    (project / "src/__init__.py").write_text("")
    (project / "tests/test_domain.py").write_text("def test_domain():\n    assert 3 * 3 == 9\n")
    (project / "manuscript/02_methods.md").write_text("# Methods\n\nThe declared child is executed.\n")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "child.py").write_text(code)
    pipeline = project / "pipeline.yaml"
    pipeline.write_text(
        yaml.safe_dump(
            {
                "stages": [
                    {
                        "name": "Child",
                        "key": "child",
                        "script": "scripts/child.py",
                        "allow_skip": allow_skip,
                        "contract": {
                            "output_artifacts": ["projects/{project}/output/data/value.txt"] if incremental else []
                        },
                    }
                ],
                "telemetry": {"enabled": False},
            }
        )
    )
    return PipelineExecutor(
        PipelineConfig(
            "demo", tmp_path, clean=False, run_timeout_seconds=timeout, incremental=IncrementalConfig(incremental)
        )
    )


@pytest.mark.parametrize("exit_code,expected", [(0, 0), (2, 1), (7, 1)])
def test_real_child_preserves_original_exit(tmp_path: Path, exit_code: int, expected: int) -> None:
    executor = _executor(tmp_path, f"raise SystemExit({exit_code})\n", allow_skip=True)
    results = executor.execute_pipeline()
    assert results[0].exit_code == exit_code
    assert executor.run_result(results).exit_code == expected


def test_real_child_timeout_is_not_generic_failure(tmp_path: Path) -> None:
    executor = _executor(tmp_path, "import time\ntime.sleep(10)\n", timeout=0.5)
    results = executor.execute_pipeline()
    assert results[0].outcome is not None
    assert results[0].outcome.status == StageStatus.TIMED_OUT
    assert executor.run_result(results).exit_code == 124


def test_successful_child_without_required_output_fails_completion(tmp_path: Path) -> None:
    executor = _executor(tmp_path, "pass\n", incremental=True)
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 1
    assert results[0].outcome is not None and results[0].outcome.child_exit_code == 0
    assert "Required output" in results[0].error_message
    assert not results[0].stage_completed


def test_missing_input_blocks_child_before_execution(tmp_path: Path) -> None:
    executor = _executor(tmp_path, "raise RuntimeError('must not execute')\n")
    path = executor.config.project_dir / "pipeline.yaml"
    declaration = yaml.safe_load(path.read_text())
    declaration["stages"][0]["contract"]["input_artifacts"] = ["output/data/required.csv"]
    path.write_text(yaml.safe_dump(declaration))
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 75
    assert results[0].outcome is not None and results[0].outcome.child_exit_code is None
    assert "Required input" in results[0].error_message


def test_consumed_output_data_mutation_blocks_success(tmp_path: Path) -> None:
    executor = _executor(
        tmp_path, "from pathlib import Path\nPath('projects/demo/output/data/input.csv').write_text('tampered')\n"
    )
    data = executor.config.project_dir / "output" / "data"
    data.mkdir(parents=True)
    (data / "input.csv").write_text("reviewed")
    path = executor.config.project_dir / "pipeline.yaml"
    declaration = yaml.safe_load(path.read_text())
    declaration["stages"][0]["contract"]["input_artifacts"] = ["output/data/input.csv"]
    path.write_text(yaml.safe_dump(declaration))
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 75
    assert results[0].outcome is not None and results[0].outcome.child_exit_code == 0
    assert "Consumed input" in results[0].error_message


@pytest.mark.parametrize("forged", [False, True])
def test_child_skip_receipt_must_match_current_command(tmp_path: Path, forged: bool) -> None:
    code = "from infrastructure.core.pipeline.skip_receipts import write_skip_receipt\n"
    if forged:
        code += "import os\nos.environ['PIPELINE_RUN_ID'] = 'wrong-run'\n"
    code += "write_skip_receipt('tool_unavailable', 'optional test tool absent')\nraise SystemExit(2)\n"
    executor = _executor(tmp_path, code, allow_skip=True)
    results = executor.execute_pipeline()
    assert results[0].exit_code == 2
    assert executor.run_result(results).exit_code == (1 if forged else 0)


@pytest.mark.parametrize("decision", ["approve", "reject"])
def test_pause_bound_decision_and_exactly_one_execution(tmp_path: Path, decision: str) -> None:
    code = "from pathlib import Path\np=Path('projects/demo/output/count')\np.write_text(str(int(p.read_text())+1) if p.exists() else '1')\n"
    executor = _executor(tmp_path, code)
    executor.control_config = PipelineControlConfig(stage_policies={1: StagePolicy(require_approval=True)})
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 75
    count = executor.config.project_dir / "output" / "count"
    assert not count.exists()
    controller = HitlController(project_output_dir=executor.config.project_dir / "output")
    getattr(controller, decision)("reviewed")
    executor.config.resume = True
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == (0 if decision == "approve" else 1)
    if decision == "approve":
        assert count.read_text() == "1"
        results = executor.execute_pipeline()
        assert executor.run_result(results).exit_code == 0
        assert count.read_text() == "1"
    else:
        assert not count.exists()


def test_pause_after_approval_advances_without_reexecution(tmp_path: Path) -> None:
    code = "from pathlib import Path\np=Path('projects/demo/output/count')\np.write_text(str(int(p.read_text())+1) if p.exists() else '1')\n"
    executor = _executor(tmp_path, code)
    pipeline = executor.config.project_dir / "pipeline.yaml"
    payload = yaml.safe_load(pipeline.read_text())
    payload["stages"].append({"name": "Second", "key": "second", "script": "scripts/child.py", "depends_on": ["Child"]})
    pipeline.write_text(yaml.safe_dump(payload))
    executor.control_config = PipelineControlConfig(stage_policies={1: StagePolicy(pause_after=True)})
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 75
    count = executor.config.project_dir / "output" / "count"
    assert count.read_text() == "1"
    executor.config.resume = True
    assert executor.run_result(executor.execute_pipeline()).exit_code == 75
    assert count.read_text() == "1"
    controller = HitlController(project_output_dir=executor.config.project_dir / "output")
    controller.approve("completed stage reviewed")
    assert executor.run_result(executor.execute_pipeline()).exit_code == 0
    assert count.read_text() == "2"


def test_cached_stage_rechecks_source_and_output_bytes(tmp_path: Path) -> None:
    code = "from pathlib import Path\np=Path('projects/demo/output/data/value.txt')\np.parent.mkdir(parents=True, exist_ok=True)\np.write_text('value')\n"
    executor = _executor(tmp_path, code, incremental=True)
    assert executor.run_result(executor.execute_pipeline()).complete
    results = executor.execute_pipeline()
    assert results[0].outcome is not None and results[0].outcome.status == StageStatus.CACHED
    output = executor.config.project_dir / "output" / "data" / "value.txt"
    output.write_text("tampered")
    results = executor.execute_pipeline()
    assert results[0].outcome is not None and results[0].outcome.status == StageStatus.SUCCEEDED
    assert output.read_text() == "value"
    (executor.config.repo_root / "scripts" / "child.py").write_text(code + "# changed implementation\n")
    results = executor.execute_pipeline()
    assert results[0].outcome is not None and results[0].outcome.status == StageStatus.SUCCEEDED


def test_source_edit_during_child_blocks_success(tmp_path: Path) -> None:
    executor = _executor(tmp_path, "from pathlib import Path\nPath(__file__).write_text('changed')\n")
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 75
    assert results[0].outcome is not None and results[0].outcome.status is StageStatus.BLOCKED
    assert results[0].outcome.child_exit_code == 0
    assert not executor.checkpoint_manager.checkpoint_exists()


def test_completed_resume_rechecks_frozen_source_before_reuse(tmp_path: Path) -> None:
    executor = _executor(tmp_path, "pass\n")
    executor.preview_stage_names()
    assert executor.run_result(executor.execute_pipeline()).complete
    (tmp_path / "scripts/child.py").write_text("raise RuntimeError('changed')\n")
    executor.config.resume = True
    assert executor.run_result(executor.execute_pipeline()).exit_code == 75


def test_validated_skip_retains_child_exit_and_reason_on_repeated_resume(tmp_path: Path) -> None:
    executor = _executor(
        tmp_path,
        "from infrastructure.core.pipeline.skip_receipts import write_skip_receipt\nwrite_skip_receipt('tool_unavailable', 'tool absent')\nraise SystemExit(2)\n",
        allow_skip=True,
    )
    assert executor.run_result(executor.execute_pipeline()).complete
    executor.config.resume = True
    for _ in range(2):
        results = executor.execute_pipeline()
        assert executor.run_result(results).complete
        assert results[0].outcome is not None
        assert results[0].outcome.status is StageStatus.SKIPPED
        assert results[0].outcome.child_exit_code == 2
        assert results[0].outcome.reason == "tool_unavailable"


def test_nonexecutable_internal_helper_is_refused_before_child_execution(tmp_path: Path) -> None:
    marker = tmp_path / "inadmissible-child-entered"
    executor = _executor(tmp_path, f"from pathlib import Path\nPath({str(marker)!r}).write_text('entered')\n")
    pipeline = executor.config.project_dir / "pipeline.yaml"
    pipeline.write_text(
        yaml.safe_dump({"stages": [{"key": "helper", "name": "Helper", "method": "_resolve_pipeline_yaml"}]})
    )
    with pytest.raises(ValueError, match="Unsupported canonical method target"):
        executor.execute_pipeline()
    assert not marker.exists()


def test_child_failure_hook_timeout_takes_precedence_and_preserves_child(tmp_path: Path) -> None:
    import sys

    executor = _executor(tmp_path, "raise SystemExit(2)\n")
    pipeline = executor.config.project_dir / "pipeline.yaml"
    payload = yaml.safe_load(pipeline.read_text())
    payload["stages"][0]["hooks"] = {
        "on_fail": [[sys.executable, "-c", "import time;time.sleep(20)"]],
        "timeout_seconds": 1,
        "run_in_ci": True,
    }
    pipeline.write_text(yaml.safe_dump(payload))
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 124
    assert results[0].outcome is not None and results[0].outcome.child_exit_code == 2
    assert "timed out" in results[0].outcome.diagnostic.lower()


def test_child_failure_hook_interruption_takes_precedence_and_preserves_child(tmp_path: Path) -> None:
    import sys

    executor = _executor(tmp_path, "raise SystemExit(2)\n")
    pipeline = executor.config.project_dir / "pipeline.yaml"
    payload = yaml.safe_load(pipeline.read_text())
    marker = tmp_path / "hook-after-interruption.txt"
    payload["stages"][0]["hooks"] = {
        "on_fail": [
            [sys.executable, "-c", "raise SystemExit(130)"],
            [sys.executable, "-c", f"from pathlib import Path;Path({str(marker)!r}).write_text('ran')"],
        ],
        "timeout_seconds": 60,
        "run_in_ci": True,
    }
    pipeline.write_text(yaml.safe_dump(payload))
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 130
    assert results[0].outcome is not None
    assert results[0].outcome.status is StageStatus.INTERRUPTED
    assert results[0].outcome.child_exit_code == 2
    assert results[0].outcome.attempt_exit_codes == (2,)
    assert "interrupted" in results[0].outcome.diagnostic.lower()
    assert not marker.exists()


@pytest.mark.parametrize("changed", ["run_id", "plan_digest", "stage_key", "artifact_digest"])
def test_expired_pause_cannot_auto_proceed_with_stale_identity(tmp_path: Path, changed: str) -> None:
    from datetime import datetime, timedelta, timezone

    controller = HitlController(
        project_output_dir=tmp_path / "output",
        run_id="run",
        plan_digest="a" * 64,
        control=PipelineControlConfig(
            stage_policies={1: StagePolicy(pause_before=True, auto_proceed_on_timeout=True, timeout_seconds=1)}
        ),
    )
    spec = StageSpec("Child", lambda: True, key="child")
    controller.pause(stage_num=1, stage_name="Child", reason="pause", stage_spec=spec)
    payload = json.loads(controller.waiting_path.read_text())
    payload["since"] = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
    payload[changed] = "different"
    controller.waiting_path.write_text(json.dumps(payload))
    assert controller.should_pause_before(1, spec)
    assert controller.waiting_path.exists()


def test_concurrent_human_approval_decides_waiting_state_once(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    root = tmp_path / "output"
    controller = HitlController(project_output_dir=root, run_id="run", plan_digest="a" * 64)
    controller.pause(stage_num=1, stage_name="Child", reason="review")

    def approve() -> bool:
        try:
            HitlController(project_output_dir=root).approve("reviewed")
            return True
        except ValueError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: approve(), range(2))) == [False, True]
    assert len([row for row in controller.history() if row["action"] == "approve"]) == 1


def test_human_state_symlink_cannot_read_or_write_external_content(tmp_path: Path) -> None:
    outside = tmp_path / "external"
    outside.mkdir()
    sentinel = outside / "decisions.jsonl"
    sentinel.write_text("private sentinel")
    root = tmp_path / "output"
    root.mkdir()
    (root / "hitl").symlink_to(outside, target_is_directory=True)
    controller = HitlController(project_output_dir=root)
    with pytest.raises((ValueError, OSError)):
        controller.pause(stage_num=1, stage_name="Child", reason="review")
    with pytest.raises((ValueError, OSError)):
        controller.history()
    assert sentinel.read_text() == "private sentinel"
    assert list(outside.iterdir()) == [sentinel]


def test_corrupt_consumption_history_refuses_approval_replay(tmp_path: Path) -> None:
    root = tmp_path / "output"
    controller = HitlController(project_output_dir=root, run_id="run", plan_digest="a" * 64)
    spec = StageSpec("Child", lambda: True, key="child")
    controller.pause(stage_num=1, stage_name="Child", reason="review", stage_spec=spec)
    controller.approve("reviewed")
    assert controller.decision_for_stage(spec) == "approve"
    rows = controller.decisions_path.read_text().splitlines()
    controller.decisions_path.write_text("\n".join(rows[:-1] + ["{corrupt consumed decision"]) + "\n")
    fresh = HitlController(project_output_dir=root, run_id="run", plan_digest="a" * 64)
    with pytest.raises(ValueError, match="authorization refused"):
        fresh.decision_for_stage(spec)


def test_resume_continues_non_approval_pause_once_and_keeps_approval_required(tmp_path: Path) -> None:
    import stat

    root = tmp_path / "output"
    controller = HitlController(
        project_output_dir=root,
        run_id="run",
        plan_digest="a" * 64,
        control=PipelineControlConfig(stage_policies={1: StagePolicy(pause_before=True)}),
    )
    spec = StageSpec("Child", lambda: True, key="child", policy=StagePolicy(pause_before=True))
    controller.pause(stage_num=1, stage_name="Child", reason="checkpoint", stage_spec=spec)
    assert stat.S_IMODE(controller.waiting_path.stat().st_mode) == 0o600
    controller.resume("continue")
    assert controller.decision_for_stage(spec) == "resume"
    assert not controller.should_pause_before(1, spec)
    assert HitlController(project_output_dir=root, run_id="run", plan_digest="a" * 64).decision_for_stage(spec) is None
    controller.pause(stage_num=1, stage_name="Child", reason="approval_required", stage_spec=spec)
    with pytest.raises(ValueError, match="requires explicit approval"):
        controller.resume("cannot waive approval")
    assert controller.waiting_path.exists()


def test_frozen_preview_refuses_changed_external_declaration(tmp_path: Path) -> None:
    executor = _executor(tmp_path, "from pathlib import Path\nPath('launched').touch()\n")
    original = executor.config.project_dir / "pipeline.yaml"
    external = tmp_path / "external.yaml"
    external.write_text(original.read_text())
    executor.config.pipeline_path = external
    assert executor.preview_stage_names() == ("Child",)
    external.write_text(external.read_text() + "# consumed declaration changed\n")
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 75
    assert not (tmp_path / "launched").exists()


def test_targeted_stage_cannot_drop_its_source_approval_policy(tmp_path: Path) -> None:
    executor = _executor(tmp_path, "from pathlib import Path\nPath('launched').touch()\n")
    pipeline = executor.config.project_dir / "pipeline.yaml"
    payload = yaml.safe_load(pipeline.read_text())
    payload["stages"].insert(0, {"name": "Shared", "key": "infra_tests", "script": "scripts/child.py"})
    payload["stages"][1]["depends_on"] = ["Shared"]
    pipeline.write_text(yaml.safe_dump(payload))
    executor.control_config = PipelineControlConfig(stage_policies={2: StagePolicy(require_approval=True)})
    plan = resolve_execution_plan(executor, skip_clean=True, target_stage="child")
    assert plan.stages[0].policy.require_approval
    results = executor.execute_plan(plan)
    assert executor.run_result(results).exit_code == 75
    assert not (tmp_path / "launched").exists()


@pytest.mark.parametrize(
    "status,context",
    [
        ("failed", {}),
        ("paused", {}),
        ("paused", {"hitl_pause": False}),
        ("cached", {"receipt_validated": False}),
        ("unknown", {}),
    ],
)
def test_checkpoint_cannot_reclassify_incomplete_state_as_cached(
    tmp_path: Path, status: str, context: dict[str, object]
) -> None:
    executor = _executor(tmp_path, "pass\n")
    assert executor.run_result(executor.execute_pipeline()).complete
    checkpoint = executor.checkpoint_manager.checkpoint_file
    payload = json.loads(checkpoint.read_text())
    payload["stage_results"][0]["status"] = status
    payload["stage_results"][0]["context"].update(context)
    checkpoint.write_text(json.dumps(payload))
    assert not executor.checkpoint_manager.validate_checkpoint()[0]
    executor.config.resume = True
    assert executor.run_result(executor.execute_pipeline()).exit_code == 75


def test_source_output_named_subdirectory_is_consumed(tmp_path: Path) -> None:
    executor = _executor(tmp_path, "pass\n")
    source = executor.config.project_dir / "src" / "output" / "producer.py"
    source.parent.mkdir(parents=True)
    source.write_text("original")
    before = source_fingerprint(tmp_path, executor.config.project_dir)
    source.write_text("changed")
    after = source_fingerprint(tmp_path, executor.config.project_dir)
    assert before != after
    working = executor.config.project_dir / "output" / "data" / "working.txt"
    working.parent.mkdir(parents=True, exist_ok=True)
    working.write_text("generated")
    assert source_fingerprint(tmp_path, executor.config.project_dir) == after


@pytest.mark.parametrize("changed_binding", ["run_id", "plan_digest", "stage_key", "artifact_digest"])
def test_detached_decision_cannot_inherit_later_pause(tmp_path: Path, changed_binding: str) -> None:
    controller = HitlController(project_output_dir=tmp_path / "output", run_id="run-one", plan_digest="a" * 64)
    waiting = controller.pause(stage_num=1, stage_name="Stage", reason="review")
    original = {key: getattr(waiting, key) for key in ("run_id", "plan_digest", "stage_key", "artifact_digest")}
    response = tmp_path / "decision.json"
    response.write_text(json.dumps({"action": "approve", **original}))
    if changed_binding == "run_id":
        controller.run_id = "run-two"
    elif changed_binding == "plan_digest":
        controller.plan_digest = "b" * 64
    elif changed_binding == "artifact_digest":
        (controller.project_output_dir / "result.txt").write_text("new result")
    controller.pause(
        stage_num=1, stage_name="Different" if changed_binding == "stage_key" else "Stage", reason="review"
    )
    with pytest.raises(ValueError, match="identity differs"):
        controller.respond_from_file(response)
    assert controller.waiting_path.is_file()
    assert not any(row["action"] == "approve" for row in controller.history())


@pytest.mark.parametrize("version,reason", [(True, "tool_unavailable"), (1.0, "tool_unavailable"), (1, []), (1, {})])
def test_malformed_skip_receipt_cannot_authorize_completion(tmp_path: Path, version: object, reason: object) -> None:
    code = "import json, os\nfrom pathlib import Path\n"
    code += "payload={key:os.environ[env] for key,env in {'run_id':'PIPELINE_RUN_ID','stage_key':'PIPELINE_STAGE_KEY','command_digest':'PIPELINE_COMMAND_DIGEST','plan_digest':'PIPELINE_PLAN_DIGEST'}.items()}\n"
    code += f"payload.update(schema_version={version!r},reason={reason!r},diagnostic='unavailable')\n"
    code += "Path(os.environ['PIPELINE_SKIP_RECEIPT_PATH']).write_text(json.dumps(payload))\nraise SystemExit(2)\n"
    executor = _executor(tmp_path, code, allow_skip=True)
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 1
    assert results[0].outcome is not None and results[0].outcome.child_exit_code == 2


def test_directory_changes_and_control_separation(tmp_path: Path) -> None:
    root = tmp_path / "output"
    root.mkdir()
    initial = paths_digest((root,), control_output=True)
    (root / "a.txt").write_text("A")
    added = paths_digest((root,), control_output=True)
    assert initial != added
    (root / "a.txt").rename(root / "b.txt")
    assert paths_digest((root,), control_output=True) != added
    stable = paths_digest((root,), control_output=True)
    (root / "hitl").mkdir()
    (root / "hitl" / "decision.json").write_text("approved")
    assert paths_digest((root,), control_output=True) == stable
    (root / "b.txt").unlink()
    assert paths_digest((root,), control_output=True) == initial


def test_symlink_cannot_authorize_content(tmp_path: Path) -> None:
    (tmp_path / "real").write_text("payload")
    (tmp_path / "link").symlink_to(tmp_path / "real")
    with pytest.raises(ValueError, match="symlink"):
        paths_digest((tmp_path / "link",))


def test_cache_schema_miss(tmp_path: Path) -> None:
    path = tmp_path / ".pipeline" / "incremental.json"
    path.parent.mkdir()
    path.write_text(json.dumps({"version": 1, "stages": {"x": {"input_hash": "a", "output_hash": "b"}}}))
    assert load_hash_manifest(tmp_path).to_dict() == HashManifest().to_dict()


def test_completion_and_exit_precedence() -> None:
    success = StageOutcome("a", StageStatus.SUCCEEDED)
    paused = StageOutcome("b", StageStatus.PAUSED)
    assert RunResult(("a", "b"), (success,)).exit_code == 1
    assert RunResult(("a", "b"), (success, paused)).exit_code == 75
    assert RunResult(("a",), (StageOutcome("a", StageStatus.SKIPPED, 2),)).exit_code == 1
    assert RunResult(("a",), (StageOutcome("a", StageStatus.CACHED),)).exit_code == 1
    assert (
        RunResult(
            ("a", "b"), (StageOutcome("a", StageStatus.TIMED_OUT), StageOutcome("b", StageStatus.INTERRUPTED))
        ).exit_code
        == 130
    )


def test_in_process_completion_never_invents_child_exit() -> None:
    incomplete = StageOutcome("clean", StageStatus.SUCCEEDED, None)
    verified = StageOutcome("clean", StageStatus.SUCCEEDED, None, in_process_completed=True)
    assert not incomplete.complete and verified.complete
    assert RunResult(("clean",), (verified,)).complete
    with pytest.raises(ValueError, match="invent child"):
        StageOutcome("clean", StageStatus.SUCCEEDED, 0, in_process_completed=True)
    with pytest.raises(ValueError, match="invent child"):
        StageOutcome("clean", StageStatus.SUCCEEDED, None, attempt_exit_codes=(0,), in_process_completed=True)


@pytest.mark.parametrize("pause_after", [False, True])
def test_canonical_cleanup_is_complete_and_resumable_without_a_child(tmp_path: Path, pause_after: bool) -> None:
    executor = _executor(tmp_path, "raise RuntimeError('cleanup must not dispatch this child')\n")
    declaration = executor.config.project_dir / "pipeline.yaml"
    declaration.write_text(
        yaml.safe_dump(
            {
                "telemetry": {"enabled": False},
                "stages": [{"name": "Actual Cleanup", "key": "custom-clean", "method": "_run_clean_outputs"}],
                "control": {"stage_policies": {1: {"pause_after": pause_after}}},
            }
        )
    )
    executor.config.clean = True
    executor = PipelineExecutor(executor.config)
    residue = executor.config.project_dir / "output/data/old-result.txt"
    residue.parent.mkdir(parents=True, exist_ok=True)
    residue.write_text("old result must be removed by the actual implementation")
    results = executor.execute_pipeline()
    outcome = results[0].outcome
    assert outcome is not None and outcome.child_exit_code is None and outcome.in_process_completed
    assert not outcome.attempt_exit_codes and not residue.exists()
    assert executor.run_result(results).exit_code == (75 if pause_after else 0)
    assert executor.checkpoint_manager.load_validated_checkpoint()[0] is not None
    if pause_after:
        HitlController(project_output_dir=executor.config.project_dir / "output").approve(
            "Reviewed actual cleanup result."
        )
    executor.config.resume = True
    resumed = PipelineExecutor(executor.config)
    continuation = resumed.execute_pipeline()
    assert resumed.run_result(continuation).complete
    assert continuation[0].outcome is not None and continuation[0].outcome.child_exit_code is None
    assert continuation[0].outcome.in_process_completed


def test_invalid_resume_preserves_checkpoint_without_execution(tmp_path: Path) -> None:
    executor = _executor(tmp_path, "raise RuntimeError('must not launch')\n")
    checkpoint = executor.checkpoint_manager.checkpoint_file
    checkpoint.parent.mkdir(parents=True)
    original = '{"schema_version":1}'
    checkpoint.write_text(original)
    executor.config.resume = True
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 75
    assert checkpoint.read_text() == original


def test_stage_contract_inputs_remain_immutable() -> None:
    contract = StageContract(input_artifacts=("data",))
    with pytest.raises(AttributeError):
        contract.retry_policy = 3  # type: ignore[misc]
