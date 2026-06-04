"""Tests for SIA task directory validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.exceptions import ValidationError
from infrastructure.sia.task_layout import validate_task_dir


def _write_min_task(root: Path) -> Path:
    (root / "data" / "public").mkdir(parents=True)
    (root / "data" / "private").mkdir(parents=True)
    (root / "reference").mkdir(parents=True)
    (root / "data" / "public" / "task.md").write_text("# Task\n", encoding="utf-8")
    (root / "reference" / "reference_target_agent.py").write_text("# agent\n", encoding="utf-8")
    return root


def test_validate_task_dir_accepts_min_layout(tmp_path: Path) -> None:
    task = _write_min_task(tmp_path / "mini")
    layout = validate_task_dir(task)
    assert layout.task_md.name == "task.md"
    assert layout.evaluate_script is None


def test_validate_task_dir_detects_evaluate_script(tmp_path: Path) -> None:
    task = _write_min_task(tmp_path / "with_eval")
    (task / "data" / "public" / "evaluate.py").write_text("print('ok')\n", encoding="utf-8")
    layout = validate_task_dir(task)
    assert layout.evaluate_script is not None


def test_validate_task_dir_rejects_missing_reference(tmp_path: Path) -> None:
    task = tmp_path / "bad"
    (task / "data" / "public").mkdir(parents=True)
    (task / "data" / "private").mkdir(parents=True)
    (task / "reference").mkdir(parents=True)
    (task / "data" / "public" / "task.md").write_text("# Task\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="reference_target_agent"):
        validate_task_dir(task)
