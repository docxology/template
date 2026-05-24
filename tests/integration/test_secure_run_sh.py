#!/usr/bin/env python3
"""Integration tests for `secure_run.sh` and `run.sh --secure-run` CLI surface.

These tests intentionally avoid running the full secure pipeline (slow) and
focus on help output, empty-arg handling, and argv shaping into the Python
orchestrator. No mocks: subprocess calls execute the real scripts.
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
def secure_script(repo_root: Path) -> Path:
    return repo_root / "secure_run.sh"


@pytest.fixture
def run_script(repo_root: Path) -> Path:
    return repo_root / "run.sh"


def run_script_cmd(script_path: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    cmd = ["bash", str(script_path), *args]
    return subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy())


def test_secure_script_exists(secure_script: Path) -> None:
    assert secure_script.exists()
    assert os.access(secure_script, os.X_OK)


def test_secure_help_option(secure_script: Path) -> None:
    result = run_script_cmd(secure_script, ["--help"])
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "--steganography-only" in result.stdout
    assert "--project" in result.stdout


def test_secure_no_args_exits_with_quick_start(secure_script: Path) -> None:
    result = run_script_cmd(secure_script, [])
    assert result.returncode == 2
    combined = (result.stdout or "") + (result.stderr or "")
    assert "no arguments given" in combined.lower()
    assert "--steganography-only" in combined


def test_run_sh_secure_run_help(run_script: Path) -> None:
    """``run.sh --secure-run --help`` shapes argv to the ``secure`` subcommand."""
    result = run_script_cmd(run_script, ["--secure-run", "--help"])
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "--steganography-only" in result.stdout


def test_run_sh_secure_run_invalid_option(run_script: Path) -> None:
    result = run_script_cmd(run_script, ["--secure-run", "--not-a-real-flag"])
    assert result.returncode == 2
    combined = (result.stdout or "") + (result.stderr or "")
    assert "unrecognized arguments" in combined
