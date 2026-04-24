#!/usr/bin/env python3
"""CLI surface tests for `scripts/execute_pipeline.py` (fast, no heavy stages)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).parent.parent.parent


def test_execute_pipeline_help_includes_stage(repo_root: Path) -> None:
    script = repo_root / "scripts" / "execute_pipeline.py"
    result = subprocess.run(
        ["python3", str(script), "--help"],
        cwd=str(repo_root),
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--stage" in result.stdout
    assert "--core-only" in result.stdout


def test_execute_pipeline_unknown_stage_is_error(repo_root: Path) -> None:
    script = repo_root / "scripts" / "execute_pipeline.py"
    result = subprocess.run(
        ["python3", str(script), "--project", "project", "--stage", "not_a_stage"],
        cwd=str(repo_root),
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Unknown stage" in combined


def test_execute_pipeline_missing_project_is_error(repo_root: Path) -> None:
    """Invoking without --project should produce a non-zero exit or usage message."""
    script = repo_root / "scripts" / "execute_pipeline.py"
    result = subprocess.run(
        ["python3", str(script)],
        cwd=str(repo_root),
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )
    # Either exits with error or prints usage; must not silently succeed
    combined = (result.stdout or "") + (result.stderr or "")
    assert result.returncode != 0 or "usage" in combined.lower() or "--project" in combined


def test_execute_pipeline_help_mentions_core_only(repo_root: Path) -> None:
    """--core-only flag must be documented in help text."""
    script = repo_root / "scripts" / "execute_pipeline.py"
    result = subprocess.run(
        ["python3", str(script), "--help"],
        cwd=str(repo_root),
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--core-only" in result.stdout


def test_execute_pipeline_script_is_importable(repo_root: Path) -> None:
    """The pipeline script must compile cleanly (no syntax errors)."""
    script = repo_root / "scripts" / "execute_pipeline.py"
    result = subprocess.run(
        ["python3", "-m", "py_compile", str(script)],
        cwd=str(repo_root),
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax error in execute_pipeline.py:\n{result.stderr}"
