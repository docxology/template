"""Negative-control tests for SIA artifact validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.sia.evaluation_runner import read_results_json
from infrastructure.sia.task_layout import validate_task_dir
from src.artifact_manifest import write_artifact_manifest


def test_read_results_json_rejects_hollow_object(tmp_path: Path) -> None:
    path = tmp_path / "results.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(Exception):
        read_results_json(path)


def test_read_results_json_rejects_wrong_types(tmp_path: Path) -> None:
    path = tmp_path / "results.json"
    path.write_text(
        json.dumps({"metric_name": "accuracy", "metric_value": "not-a-number", "n_samples": 6}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        read_results_json(path)


def test_artifact_manifest_omits_missing_paths(tmp_path: Path) -> None:
    present = tmp_path / "output" / "data" / "manuscript_variables.json"
    present.parent.mkdir(parents=True)
    present.write_text("{}", encoding="utf-8")
    missing = tmp_path / "output" / "missing.json"
    manifest_path = write_artifact_manifest(tmp_path, [present, missing])
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths = {entry["path"] for entry in payload["entries"]}
    assert "output/data/manuscript_variables.json" in paths
    assert "output/missing.json" not in paths


def test_validate_task_dir_rejects_nonexistent(tmp_path: Path) -> None:
    """validate_task_dir must raise ValidationError for a non-existent path."""
    from infrastructure.core.exceptions import ValidationError

    with pytest.raises(ValidationError, match="(?i)does not exist"):
        validate_task_dir(tmp_path / "no_such_task")


def test_validate_task_dir_rejects_missing_directories(tmp_path: Path) -> None:
    """A task dir missing required sub-directories must fail with ValidationError."""
    from infrastructure.core.exceptions import ValidationError

    # Create task root with no children
    task_dir = tmp_path / "bad_task"
    task_dir.mkdir()
    with pytest.raises(ValidationError, match="(?i)missing required directories"):
        validate_task_dir(task_dir)


def test_validate_task_dir_rejects_missing_public_file(tmp_path: Path) -> None:
    """A task dir with correct directories but no task.md must fail closed."""
    from infrastructure.core.exceptions import ValidationError

    task_dir = tmp_path / "bad_task"
    (task_dir / "data" / "public").mkdir(parents=True)
    (task_dir / "data" / "private").mkdir(parents=True)
    (task_dir / "reference").mkdir(parents=True)
    # No task.md in data/public
    with pytest.raises(ValidationError, match="(?i)missing required public file"):
        validate_task_dir(task_dir)


def test_validate_task_dir_rejects_missing_reference_agent(tmp_path: Path) -> None:
    """A task dir with task.md but no reference_target_agent.py must fail closed."""
    from infrastructure.core.exceptions import ValidationError

    task_dir = tmp_path / "bad_task"
    (task_dir / "data" / "public").mkdir(parents=True)
    (task_dir / "data" / "private").mkdir(parents=True)
    (task_dir / "reference").mkdir(parents=True)
    (task_dir / "data" / "public" / "task.md").write_text("# task", encoding="utf-8")
    # No reference_target_agent.py
    with pytest.raises(ValidationError, match="(?i)missing reference"):
        validate_task_dir(task_dir)
