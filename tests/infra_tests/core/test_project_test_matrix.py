"""Tests for the bounded cross-project subprocess matrix."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

from infrastructure.core.project_test_matrix import ProjectTestTask, run_project_test_matrix


def _task(tmp_path: Path, index: int, name: str, body: str, timeout: int = 5) -> ProjectTestTask:
    return ProjectTestTask(
        index=index,
        project_name=name,
        command=(sys.executable, "-c", body),
        cwd=tmp_path,
        env={"PATH": "/usr/bin:/bin"},
        timeout_seconds=timeout,
        capture_output=True,
    )


def test_matrix_preserves_roster_order_and_continues_after_failure(tmp_path: Path) -> None:
    tasks = (
        _task(tmp_path, 0, "slow-pass", "import time; time.sleep(0.15); print('slow')"),
        _task(tmp_path, 1, "fail", "print('failed'); raise SystemExit(3)"),
        _task(tmp_path, 2, "fast-pass", "print('fast')"),
    )

    results = run_project_test_matrix(tasks, workers=3)

    assert [result.project_name for result in results] == ["slow-pass", "fail", "fast-pass"]
    assert [result.returncode for result in results] == [0, 3, 0]
    assert "slow" in results[0].output_tail
    assert "failed" in results[1].output_tail
    assert results[2].duration_seconds >= 0


def test_matrix_marks_timeout_without_cancelling_other_tasks(tmp_path: Path) -> None:
    tasks = (
        _task(tmp_path, 0, "timeout", "import time; time.sleep(1)", timeout=1),
        _task(tmp_path, 1, "survivor", "print('survived')", timeout=5),
    )

    results = run_project_test_matrix(tasks, workers=2)

    assert results[0].timed_out is True
    assert results[0].returncode == 124
    assert results[1].returncode == 0
    assert "survived" in results[1].output_tail


def test_matrix_timeout_terminates_descendant_processes(tmp_path: Path) -> None:
    marker = tmp_path / "leaked-child.txt"
    child_body = f"import pathlib,time; time.sleep(2); pathlib.Path({str(marker)!r}).write_text('leaked')"
    parent_body = (
        f"import subprocess,sys,time; subprocess.Popen([sys.executable, '-c', {child_body!r}]); time.sleep(30)"
    )

    result = run_project_test_matrix((_task(tmp_path, 0, "descendant", parent_body, timeout=1),))[0]

    assert result.timed_out is True
    time.sleep(2.2)
    assert not marker.exists()


def test_matrix_rejects_non_positive_worker_count(tmp_path: Path) -> None:
    task = _task(tmp_path, 0, "one", "pass")

    with pytest.raises(ValueError, match="workers must be positive"):
        run_project_test_matrix((task,), workers=0)
