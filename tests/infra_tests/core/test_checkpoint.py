"""Tests for infrastructure.core.runtime.checkpoint module.

Comprehensive tests for pipeline checkpoint system including save, load, resume,
and error handling scenarios.
"""

import json
import tempfile

import pytest
from pathlib import Path


from infrastructure.core.runtime.checkpoint import (
    CHECKPOINT_SCHEMA_VERSION,
    CheckpointManager,
    PipelineCheckpoint,
    StageResult,
)


class TestStageResult:
    """Test StageResult dataclass."""

    def test_stage_result_creation(self):
        """Test creating a StageResult."""
        result = StageResult(
            name="test_stage",
            exit_code=0,
            duration=1.5,
            timestamp="2024-01-01 12:00:00",
            completed=True,
        )

        assert result.name == "test_stage"
        assert result.exit_code == 0
        assert result.duration == 1.5
        assert result.timestamp == "2024-01-01 12:00:00"
        assert result.completed is True

    def test_stage_result_default_completed(self):
        """Test StageResult with default completed value."""
        result = StageResult(name="test", exit_code=0, duration=1.0, timestamp="2024-01-01 12:00:00")

        assert result.completed is True  # Default value

    def test_stage_result_default_context(self):
        result = StageResult(name="test", exit_code=0, duration=1.0, timestamp="2024-01-01 12:00:00")

        assert result.context == {}


class TestPipelineCheckpoint:
    """Test PipelineCheckpoint dataclass."""

    def test_checkpoint_creation(self):
        """Test creating a PipelineCheckpoint."""
        stage_results = [
            StageResult(
                name="stage_1",
                exit_code=0,
                duration=1.0,
                timestamp="2024-01-01 12:00:00",
            )
        ]

        checkpoint = PipelineCheckpoint(
            pipeline_start_time=1000.0,
            last_stage_completed=1,
            stage_results=stage_results,
            total_stages=5,
            checkpoint_time=1001.0,
        )

        assert checkpoint.pipeline_start_time == 1000.0
        assert checkpoint.last_stage_completed == 1
        assert len(checkpoint.stage_results) == 1
        assert checkpoint.total_stages == 5
        assert checkpoint.checkpoint_time == 1001.0

    def test_checkpoint_to_dict(self):
        """Test converting checkpoint to dictionary."""
        stage_results = [
            StageResult(
                name="stage_1",
                exit_code=0,
                duration=1.0,
                timestamp="2024-01-01 12:00:00",
            )
        ]

        checkpoint = PipelineCheckpoint(
            pipeline_start_time=1000.0,
            last_stage_completed=1,
            stage_results=stage_results,
            total_stages=5,
            checkpoint_time=1001.0,
        )

        data = checkpoint.to_dict()

        assert isinstance(data, dict)
        assert data["pipeline_start_time"] == 1000.0
        assert data["last_stage_completed"] == 1
        assert len(data["stage_results"]) == 1
        assert data["total_stages"] == 5
        assert data["checkpoint_time"] == 1001.0

    def test_checkpoint_from_dict(self):
        """Test creating checkpoint from dictionary."""
        data = {
            "schema_version": CHECKPOINT_SCHEMA_VERSION,
            "pipeline_start_time": 1000.0,
            "last_stage_completed": 1,
            "stage_results": [
                {
                    "name": "stage_1",
                    "exit_code": 0,
                    "duration": 1.0,
                    "timestamp": "2024-01-01 12:00:00",
                    "completed": True,
                }
            ],
            "total_stages": 5,
            "checkpoint_time": 1001.0,
        }

        checkpoint = PipelineCheckpoint.from_dict(data)

        assert checkpoint.pipeline_start_time == 1000.0
        assert checkpoint.last_stage_completed == 1
        assert len(checkpoint.stage_results) == 1
        assert checkpoint.stage_results[0].name == "stage_1"
        assert checkpoint.total_stages == 5
        assert checkpoint.checkpoint_time == 1001.0

    def test_checkpoint_from_dict_refuses_previous_schema(self):
        """A checkpoint written by an earlier schema is never resumed."""
        with pytest.raises(ValueError, match="Unsupported checkpoint schema"):
            PipelineCheckpoint.from_dict(
                {
                    "schema_version": CHECKPOINT_SCHEMA_VERSION - 1,
                    "pipeline_start_time": 1000.0,
                    "last_stage_completed": 1,
                    "stage_results": [],
                    "total_stages": 5,
                    "checkpoint_time": 1001.0,
                }
            )

    def test_checkpoint_round_trip(self):
        """Test checkpoint serialization round trip."""
        stage_results = [
            StageResult(
                name="stage_1",
                exit_code=0,
                duration=1.0,
                timestamp="2024-01-01 12:00:00",
                context={"stage_num": 1},
            ),
            StageResult(
                name="stage_2",
                exit_code=0,
                duration=2.0,
                timestamp="2024-01-01 12:01:00",
                context={"stage_num": 2},
            ),
        ]

        original = PipelineCheckpoint(
            pipeline_start_time=1000.0,
            last_stage_completed=2,
            stage_results=stage_results,
            total_stages=5,
            checkpoint_time=1003.0,
        )

        # Convert to dict and back
        data = original.to_dict()
        restored = PipelineCheckpoint.from_dict(data)

        assert restored.pipeline_start_time == original.pipeline_start_time
        assert restored.last_stage_completed == original.last_stage_completed
        assert len(restored.stage_results) == len(original.stage_results)
        assert restored.stage_results[0].name == original.stage_results[0].name
        assert restored.total_stages == original.total_stages
        assert restored.checkpoint_time == original.checkpoint_time

    def test_checkpoint_round_trip_preserves_context(self):
        stage_results = [
            StageResult(
                name="stage_1",
                exit_code=0,
                duration=1.0,
                timestamp="2024-01-01 12:00:00",
                context={"stage_num": 1, "lessons": ["keep state"]},
            )
        ]

        original = PipelineCheckpoint(
            pipeline_start_time=1000.0,
            last_stage_completed=1,
            stage_results=stage_results,
            total_stages=5,
            checkpoint_time=1001.0,
        )

        restored = PipelineCheckpoint.from_dict(original.to_dict())

        assert restored.stage_results[0].context == {"stage_num": 1, "lessons": ["keep state"]}


class TestCheckpointManager:
    """Test CheckpointManager functionality."""

    def test_manager_initialization_default(self):
        """Test CheckpointManager with default directory."""
        manager = CheckpointManager()

        # Directory is created lazily on first save, not on initialization
        assert not manager.checkpoint_dir.exists()
        assert manager.checkpoint_dir.name == ".checkpoints"
        assert manager.checkpoint_file.name == "pipeline_checkpoint.json"

    def test_manager_initialization_custom(self, tmp_path):
        """Test CheckpointManager with custom directory."""
        custom_dir = tmp_path / "custom_checkpoints"
        manager = CheckpointManager(checkpoint_dir=custom_dir)

        assert manager.checkpoint_dir == custom_dir
        # Directory doesn't exist until save_checkpoint is called
        assert not manager.checkpoint_dir.exists()
        assert manager.checkpoint_file == custom_dir / "pipeline_checkpoint.json"

    def test_save_checkpoint(self, tmp_path):
        """Test saving a checkpoint."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir=checkpoint_dir)

        stage_results = [
            StageResult(
                name="stage_1",
                exit_code=0,
                duration=1.0,
                timestamp="2024-01-01 12:00:00",
            )
        ]

        manager.save_checkpoint(
            pipeline_start_time=1000.0,
            last_stage_completed=1,
            stage_results=stage_results,
            total_stages=5,
        )

        assert manager.checkpoint_file.exists()

        # Verify file contents
        with open(manager.checkpoint_file, "r") as f:
            data = json.load(f)

        assert data["pipeline_start_time"] == 1000.0
        assert data["last_stage_completed"] == 1
        assert len(data["stage_results"]) == 1
        assert data["total_stages"] == 5
        assert "checkpoint_time" in data

    def test_load_checkpoint_exists(self, tmp_path):
        """Test loading an existing checkpoint."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir=checkpoint_dir)

        # Save a checkpoint first
        stage_results = [
            StageResult(
                name="stage_1",
                exit_code=0,
                duration=1.0,
                timestamp="2024-01-01 12:00:00",
            )
        ]

        manager.save_checkpoint(
            pipeline_start_time=1000.0,
            last_stage_completed=1,
            stage_results=stage_results,
            total_stages=5,
        )

        # Load it back
        checkpoint = manager.load_checkpoint()

        assert checkpoint is not None
        assert checkpoint.pipeline_start_time == 1000.0
        assert checkpoint.last_stage_completed == 1
        assert len(checkpoint.stage_results) == 1
        assert checkpoint.total_stages == 5

    def test_load_checkpoint_not_exists(self, tmp_path):
        """Test loading when checkpoint doesn't exist."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir=checkpoint_dir)

        checkpoint = manager.load_checkpoint()

        assert checkpoint is None

    def test_load_checkpoint_corrupted(self, tmp_path):
        """Test loading a corrupted checkpoint file."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir=checkpoint_dir)

        # Create a corrupted checkpoint file
        manager.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        manager.checkpoint_file.write_text("invalid json content {")

        # Should return None and log warning
        checkpoint = manager.load_checkpoint()

        assert checkpoint is None

    def test_clear_checkpoint(self, tmp_path):
        """Test clearing a checkpoint."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir=checkpoint_dir)

        # Save a checkpoint
        stage_results = [
            StageResult(
                name="stage_1",
                exit_code=0,
                duration=1.0,
                timestamp="2024-01-01 12:00:00",
            )
        ]

        manager.save_checkpoint(
            pipeline_start_time=1000.0,
            last_stage_completed=1,
            stage_results=stage_results,
            total_stages=5,
        )

        assert manager.checkpoint_file.exists()

        # Clear it
        manager.clear_checkpoint()

        assert not manager.checkpoint_file.exists()

    def test_clear_checkpoint_not_exists(self, tmp_path):
        """Test clearing when checkpoint doesn't exist."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir=checkpoint_dir)

        # Should not raise error
        manager.clear_checkpoint()

    def test_checkpoint_exists_true(self, tmp_path):
        """Test checkpoint_exists when checkpoint exists."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir=checkpoint_dir)

        # Save a checkpoint
        stage_results = [
            StageResult(
                name="stage_1",
                exit_code=0,
                duration=1.0,
                timestamp="2024-01-01 12:00:00",
            )
        ]

        manager.save_checkpoint(
            pipeline_start_time=1000.0,
            last_stage_completed=1,
            stage_results=stage_results,
            total_stages=5,
        )

        assert manager.checkpoint_exists() is True

    def test_checkpoint_exists_false(self, tmp_path):
        """Test checkpoint_exists when checkpoint doesn't exist."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir=checkpoint_dir)

        assert manager.checkpoint_exists() is False

    def test_checkpoint_exists_corrupted(self, tmp_path):
        """Test checkpoint_exists with corrupted file."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir=checkpoint_dir)

        # Create corrupted file
        manager.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        manager.checkpoint_file.write_text("invalid json")

        assert manager.checkpoint_exists() is False

    def test_save_checkpoint_multiple_stages(self, tmp_path):
        """Test saving checkpoint with multiple stage results."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir=checkpoint_dir)

        stage_results = [
            StageResult(
                name="stage_1",
                exit_code=0,
                duration=1.0,
                timestamp="2024-01-01 12:00:00",
            ),
            StageResult(
                name="stage_2",
                exit_code=0,
                duration=2.0,
                timestamp="2024-01-01 12:01:00",
            ),
            StageResult(
                name="stage_3",
                exit_code=0,
                duration=1.5,
                timestamp="2024-01-01 12:02:00",
            ),
        ]

        manager.save_checkpoint(
            pipeline_start_time=1000.0,
            last_stage_completed=3,
            stage_results=stage_results,
            total_stages=5,
        )

        checkpoint = manager.load_checkpoint()

        assert checkpoint is not None
        assert len(checkpoint.stage_results) == 3
        assert checkpoint.last_stage_completed == 3

    def test_save_checkpoint_failure_handling(self, tmp_path):
        """Test handling of save checkpoint failures."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir=checkpoint_dir)

        # Create directory first, then make it read-only to cause save failure
        manager._ensure_checkpoint_dir()
        checkpoint_dir.chmod(0o444)

        try:
            stage_results = [
                StageResult(
                    name="stage_1",
                    exit_code=0,
                    duration=1.0,
                    timestamp="2024-01-01 12:00:00",
                )
            ]

            # Should not raise exception, just log warning
            manager.save_checkpoint(
                pipeline_start_time=1000.0,
                last_stage_completed=1,
                stage_results=stage_results,
                total_stages=5,
            )
        finally:
            # Restore permissions
            checkpoint_dir.chmod(0o755)


def test_validate_checkpoint_rejects_swapped_outputs(tmp_path):
    """A structurally valid checkpoint must not resume after output files change."""
    from infrastructure.core.runtime.checkpoint import CheckpointManager, StageResult

    output = tmp_path / "output"
    output.mkdir()
    (output / "result.txt").write_text("original", encoding="utf-8")
    manager = CheckpointManager(checkpoint_dir=output / ".checkpoints")
    manager.expected_plan_digest = "a" * 64
    manager.expected_source_digest = "b" * 64
    manager.run_id = "test-run"
    assert manager.save_checkpoint(
        pipeline_start_time=1.0,
        last_stage_completed=1,
        stage_results=[
            StageResult(name="Analysis", exit_code=0, duration=0.1, completed=True, context={"stage_key": "analysis"})
        ],
        total_stages=3,
    )
    ok, _err = manager.validate_checkpoint()
    assert ok is True

    (output / "result.txt").write_text("TAMPERED", encoding="utf-8")
    ok, err = manager.validate_checkpoint()
    assert ok is False
    assert err is not None
    assert "digest" in err.lower()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("last_stage_completed", "1"),
        ("last_stage_completed", True),
        ("total_stages", "3"),
        ("pipeline_start_time", float("nan")),
        ("checkpoint_time", float("inf")),
        ("output_digest", 123),
    ],
)
def test_checkpoint_rejects_malformed_fields(tmp_path, field, value):
    """Well-formed JSON with corrupt field types cannot escape resume recovery."""
    manager = CheckpointManager(checkpoint_dir=tmp_path / ".checkpoints")
    manager.checkpoint_dir.mkdir()
    payload = PipelineCheckpoint(1.0, 1, [StageResult("Analysis", 0, 0.1)], 3, 2.0).to_dict()
    payload[field] = value
    manager.checkpoint_file.write_text(json.dumps(payload), encoding="utf-8")
    assert manager.load_checkpoint() is None
    assert manager.validate_checkpoint()[0] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [("name", []), ("exit_code", False), ("duration", float("nan")), ("completed", "false"), ("context", [])],
)
def test_checkpoint_rejects_malformed_stage_fields(tmp_path, field, value):
    """Persisted stages must have the types consumed by resume and reporting."""
    manager = CheckpointManager(checkpoint_dir=tmp_path / ".checkpoints")
    manager.checkpoint_dir.mkdir()
    payload = PipelineCheckpoint(1.0, 1, [StageResult("Analysis", 0, 0.1)], 3, 2.0).to_dict()
    payload["stage_results"][0][field] = value
    manager.checkpoint_file.write_text(json.dumps(payload), encoding="utf-8")
    assert manager.load_checkpoint() is None
    assert manager.validate_checkpoint()[0] is False


def test_default_checkpoint_uses_repository_root():
    """Moving runtime helpers must not change the implicit repository root."""
    from infrastructure.core.project_paths import find_repo_root

    assert CheckpointManager().checkpoint_dir == find_repo_root() / "projects/project/output/.checkpoints"


def test_failed_checkpoint_serialization_preserves_prior_checkpoint(tmp_path):
    """A failed replacement keeps the last recoverable successful checkpoint."""
    manager = CheckpointManager(checkpoint_dir=tmp_path / ".checkpoints")
    manager.expected_plan_digest = "a" * 64
    manager.expected_source_digest = "b" * 64
    manager.run_id = "test-run"
    assert manager.save_checkpoint(1.0, 1, [StageResult("Analysis", 0, 0.1, context={"stage_key": "analysis"})], 3)
    previous = manager.checkpoint_file.read_bytes()
    invalid = StageResult("Analysis", 0, 0.1, context={"unsupported": object()})
    assert manager.save_checkpoint(1.0, 1, [invalid], 3) is False
    assert manager.checkpoint_file.read_bytes() == previous
    assert manager.validate_checkpoint()[0] is True


def test_checkpoint_digest_failure_is_nonfatal(tmp_path):
    """An unreadable output cannot turn best-effort checkpointing into a crash."""
    import os

    if hasattr(os, "geteuid") and os.geteuid() == 0:
        pytest.skip("root bypasses file read permissions")
    manager = CheckpointManager(checkpoint_dir=tmp_path / ".checkpoints")
    result = tmp_path / "result.txt"
    result.write_bytes(b"result")
    result.chmod(0)
    try:
        assert manager.save_checkpoint(1.0, 1, [StageResult("Analysis", 0, 0.1)], 3) is False
    finally:
        result.chmod(0o600)


def test_checkpoint_does_not_follow_existing_file_symlink(tmp_path):
    """A checkpoint-path symlink cannot overwrite an unrelated file."""
    manager = CheckpointManager(checkpoint_dir=tmp_path / ".checkpoints")
    manager.checkpoint_dir.mkdir()
    target = tmp_path / "unrelated.json"
    target.write_bytes(b"untouched")
    manager.checkpoint_file.symlink_to(target)
    assert manager.save_checkpoint(1.0, 1, [StageResult("Analysis", 0, 0.1)], 3) is False
    assert target.read_bytes() == b"untouched"


def test_output_digest_refuses_symlinked_ancestor_until_caller_canonicalizes(tmp_path):
    """A symlinked ancestor (macOS ``/var`` -> ``/private/var``) is refused, not followed.

    The fingerprint boundary must be nominated as a canonical path; callers
    resolve platform aliases deliberately, as pytest's ``tmp_path`` does.
    """
    real = tmp_path / "real"
    (real / "run").mkdir(parents=True)
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    results = [StageResult("Analysis", 0, 0.1)]

    aliased = CheckpointManager(checkpoint_dir=alias / "run" / ".checkpoints")
    assert aliased.save_checkpoint(1.0, 1, results, 3) is False
    assert not (real / "run" / ".checkpoints" / "pipeline_checkpoint.json").exists()

    canonical = CheckpointManager(checkpoint_dir=(alias / "run").resolve() / ".checkpoints")
    assert canonical.save_checkpoint(1.0, 1, results, 3) is True
    restored = canonical.load_checkpoint()
    assert restored is not None and len(restored.output_digest) == 64


@pytest.mark.parametrize("exit_code", [0, 1])
def test_checkpoint_cannot_skip_incomplete_stage(tmp_path, exit_code):
    """Resume must rerun a stage whose persisted result is not complete."""
    manager = CheckpointManager(checkpoint_dir=tmp_path / ".checkpoints")
    assert manager.save_checkpoint(1.0, 1, [StageResult("Analysis", exit_code, 0.1, completed=False)], 3)
    assert manager.validate_checkpoint()[0] is False


def test_output_tree_digest_refuses_planted_file_symlinks(tmp_path):
    """A planted file symlink cannot authorize a resume."""
    with tempfile.TemporaryDirectory() as outside_dir:
        manager = CheckpointManager(checkpoint_dir=tmp_path / ".checkpoints")
        (tmp_path / "anchor.txt").write_bytes(b"anchor bytes")
        anchored = manager._output_tree_digest()
        target = tmp_path / "output.txt"
        target.write_bytes(b"stable bytes")
        assert manager._output_tree_digest() != anchored
        outside_file = Path(outside_dir) / "external.bin"
        outside_file.write_bytes(b"external payload")
        target.unlink()
        target.symlink_to(outside_file)
        with pytest.raises(ValueError, match="symlink"):
            manager._output_tree_digest()
