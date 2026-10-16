"""The actual auxiliary CLI rejects invalid workers before Source or I/O."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("workers", ("0", "4", "-1", "many"))
def test_actual_auxiliary_cli_refuses_invalid_worker_count_without_outputs(tmp_path: Path, workers: str) -> None:
    _assert_invalid_worker_count(tmp_path, workers, "--installed-workers")


@pytest.mark.parametrize("workers", ("0", "4", "-1", "many"))
def test_actual_auxiliary_cli_refuses_invalid_auxiliary_workers_without_outputs(tmp_path: Path, workers: str) -> None:
    _assert_invalid_worker_count(tmp_path, workers, "--auxiliary-workers")


def _assert_invalid_worker_count(tmp_path: Path, workers: str, flag: str) -> None:
    root = Path(__file__).resolve().parents[3]
    evidence = tmp_path / "never-created"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "infrastructure.project.public_acceptance_auxiliary_cli",
            "--repo-root",
            str(tmp_path / "absent-source"),
            "--installed",
            flag,
            workers,
            "--evidence-dir",
            str(evidence),
        ],
        cwd=root,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 2
    assert flag in result.stderr
    assert "invalid choice" in result.stderr or "invalid int value" in result.stderr
    assert not tuple(tmp_path.iterdir())
