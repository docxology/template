#!/usr/bin/env python3
"""Integration tests for `run.sh` CLI surface.

These tests intentionally avoid running the full pipeline (slow) and focus on:
- argument parsing
- error handling
- help output stability

No mocks: subprocess calls execute the real script.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).parent.parent.parent


@pytest.fixture
def script_path(repo_root: Path) -> Path:
    return repo_root / "run.sh"


def run_script(script_path: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    cmd = ["bash", str(script_path), *args]
    return subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy())


def test_script_exists(script_path: Path) -> None:
    assert script_path.exists()
    assert os.access(script_path, os.X_OK)


def test_help_option(script_path: Path) -> None:
    """``run.sh`` forwards to ``python -m infrastructure.orchestration`` (argparse)."""
    result = run_script(script_path, ["--help"])
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "pipeline" in result.stdout
    pl = run_script(script_path, ["pipeline", "--help"])
    assert pl.returncode == 0
    assert "--project" in pl.stdout


def test_invalid_option(script_path: Path) -> None:
    result = run_script(script_path, ["--invalid-option"])
    assert result.returncode == 2
    combined = (result.stdout or "") + (result.stderr or "")
    assert "unrecognized arguments: --invalid-option" in combined


def test_project_option_missing_value(script_path: Path) -> None:
    result = run_script(script_path, ["pipeline", "--project"])
    assert result.returncode == 2
    combined = (result.stdout or "") + (result.stderr or "")
    assert "expected one argument" in combined


def test_project_option_invalid_project(script_path: Path) -> None:
    result = run_script(script_path, ["pipeline", "--project", "nonexistent_project_name_12345"])
    assert result.returncode == 1
    combined = (result.stdout or "") + (result.stderr or "")
    assert "nonexistent_project_name_12345" in combined
    assert "not found" in combined


def test_pipeline_resume_without_pipeline(script_path: Path) -> None:
    """``--resume`` is only defined on the ``pipeline`` subcommand, not at top level."""
    result = run_script(script_path, ["--resume"])
    assert result.returncode == 2
    combined = (result.stdout or "") + (result.stderr or "")
    assert "unrecognized arguments: --resume" in combined


def test_all_projects_help(script_path: Path) -> None:
    # `--all-projects` is accepted; help should still work and exit 0.
    result = run_script(script_path, ["--all-projects", "--help"])
    assert result.returncode == 0
