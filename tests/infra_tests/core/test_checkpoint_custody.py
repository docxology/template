"""Checkpoint control state is confined, bounded, and observed once for resume."""

from pathlib import Path
import json

import pytest

from infrastructure.core.runtime.checkpoint import CheckpointManager, StageResult


def _manager(root: Path) -> CheckpointManager:
    output = root / "output"
    output.mkdir()
    (output / "result.txt").write_text("stable domain output")
    manager = CheckpointManager(checkpoint_dir=output / ".checkpoints")
    manager.expected_plan_digest = "a" * 64
    manager.expected_source_digest = "b" * 64
    manager.run_id = "actual-run"
    assert manager.save_checkpoint(1.0, 1, [StageResult("Child", 0, 0.1, context={"stage_key": "child"})], 1)
    assert manager.validate_checkpoint()[0]
    return manager


@pytest.mark.parametrize("component", ["file", "directory"])
def test_valid_external_checkpoint_cannot_grant_reuse_through_symlink(tmp_path: Path, component: str) -> None:
    manager = _manager(tmp_path)
    content = manager.checkpoint_file.read_bytes()
    outside = tmp_path / "external"
    outside.mkdir()
    sentinel = outside / "pipeline_checkpoint.json"
    sentinel.write_bytes(content)
    manager.checkpoint_file.unlink()
    if component == "file":
        manager.checkpoint_file.symlink_to(sentinel)
    else:
        manager.checkpoint_dir.rmdir()
        manager.checkpoint_dir.symlink_to(outside, target_is_directory=True)
    assert manager.load_checkpoint() is None
    assert manager.load_validated_checkpoint()[0] is None
    assert manager.validate_checkpoint()[0] is False
    manager.clear_checkpoint()
    assert sentinel.read_bytes() == content


def test_oversized_control_record_refuses_resume_without_deletion(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    content = b" " * (8 * 1024 * 1024 + 1)
    manager.checkpoint_file.write_bytes(content)
    assert manager.load_validated_checkpoint()[0] is None
    assert manager.checkpoint_file.read_bytes() == content


@pytest.mark.parametrize(
    "key,value",
    [
        ("child_exit_code", True),
        ("attempt_count", "bad"),
        ("attempt_count", 0),
        ("attempt_exit_codes", [True]),
        ("attempt_exit_codes", "0"),
        ("reason", []),
        ("in_process_completed", 1),
    ],
)
def test_malformed_context_is_refused_at_snapshot_boundary(tmp_path: Path, key: str, value: object) -> None:
    manager = _manager(tmp_path)
    payload = json.loads(manager.checkpoint_file.read_text())
    payload["stage_results"][0]["context"][key] = value
    manager.checkpoint_file.write_text(json.dumps(payload))
    assert manager.load_validated_checkpoint()[0] is None


def test_in_process_completion_requires_no_invented_child_evidence(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    payload = json.loads(manager.checkpoint_file.read_text())
    context = payload["stage_results"][0]["context"]
    context.update(child_exit_code=None, in_process_completed=True, attempt_exit_codes=[])
    manager.checkpoint_file.write_text(json.dumps(payload))
    assert manager.load_validated_checkpoint()[0] is not None
    context["child_exit_code"] = 0
    manager.checkpoint_file.write_text(json.dumps(payload))
    assert manager.load_validated_checkpoint()[0] is None
    context.update(child_exit_code=None, attempt_exit_codes=[0])
    manager.checkpoint_file.write_text(json.dumps(payload))
    assert manager.load_validated_checkpoint()[0] is None


def test_retired_checkpoint_schema_requires_fresh_run(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    payload = json.loads(manager.checkpoint_file.read_text())
    payload["schema_version"] = 3
    manager.checkpoint_file.write_text(json.dumps(payload))
    preserved = manager.checkpoint_file.read_bytes()
    assert manager.load_validated_checkpoint()[0] is None
    assert manager.checkpoint_file.read_bytes() == preserved
