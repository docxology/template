"""Validate-only CLI for SIA tasks."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_cli_validate_task(tmp_path: Path) -> None:
    task = tmp_path / "task"
    (task / "data" / "public").mkdir(parents=True)
    (task / "data" / "private").mkdir(parents=True)
    (task / "reference").mkdir(parents=True)
    (task / "data" / "public" / "task.md").write_text("# T\n", encoding="utf-8")
    (task / "reference" / "reference_target_agent.py").write_text("# a\n", encoding="utf-8")
    repo = Path(__file__).resolve().parents[3]
    proc = subprocess.run(
        [sys.executable, "-m", "infrastructure.sia.cli", str(task)],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert str(task) in proc.stdout


def test_cli_validate_missing_dir_fails_cleanly(tmp_path: Path) -> None:
    """Negative control: an invalid task dir exits 1 with a message, not a traceback.

    `validate_task_dir` raises `ValidationError` (not a `ValueError`); the CLI
    must catch it so the acceptance command degrades cleanly.
    """
    repo = Path(__file__).resolve().parents[3]
    proc = subprocess.run(
        [sys.executable, "-m", "infrastructure.sia.cli", str(tmp_path / "does_not_exist")],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    assert "Traceback (most recent call last)" not in proc.stderr
    assert proc.stderr.strip()  # a human-readable message was printed


def test_cli_validate_missing_dir_json_emits_error_object(tmp_path: Path) -> None:
    """--json on an invalid dir emits {"error": ...}, never a raw traceback."""
    import json

    repo = Path(__file__).resolve().parents[3]
    proc = subprocess.run(
        [sys.executable, "-m", "infrastructure.sia.cli", str(tmp_path / "nope"), "--json"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    assert "Traceback (most recent call last)" not in proc.stderr
    payload = json.loads(proc.stdout)
    assert "error" in payload


def test_cli_validate_task_defaults_to_cwd(tmp_path: Path) -> None:
    task = tmp_path / "task"
    (task / "data" / "public").mkdir(parents=True)
    (task / "data" / "private").mkdir(parents=True)
    (task / "reference").mkdir(parents=True)
    (task / "data" / "public" / "task.md").write_text("# T\n", encoding="utf-8")
    (task / "reference" / "reference_target_agent.py").write_text("# a\n", encoding="utf-8")
    repo = Path(__file__).resolve().parents[3]
    proc = subprocess.run(
        [sys.executable, "-m", "infrastructure.sia.cli", "validate"],
        cwd=str(task),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(repo)},
    )
    assert proc.returncode == 0
    assert str(task) in proc.stdout
