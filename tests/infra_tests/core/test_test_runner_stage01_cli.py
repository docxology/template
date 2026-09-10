"""Stage 01 CLI contract tests for the public-projects testing pipeline.

These tests pin the ``scripts/pipeline/stage_01_test.py`` CLI surface via real
subprocess invocations: the public-projects and parallel flags are documented
in ``--help``, mode/worker constraints fail closed, and profiles and
project-workers are validated. The combined-union ``DEFAULT_FAIL_UNDER``
constant is reconciled here alongside the CLI.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.core.testing.test_runner import DEFAULT_FAIL_UNDER

REPO_ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.timeout(120)


def test_default_fail_under_constant_matches_repo_threshold() -> None:
    """Combined-union project gate, reconciled to measured reality.

    Deliberately distinct from — and lower than — the per-project standalone
    90% floor (which exemplar projects meet). The combined number is
    structurally lower because per-project suites only cover their own
    ``src/`` while the union denominator spans every project included in the
    run. CI uses the public project scope; local runs may include rotating
    symlinked projects. Kept in lockstep with the ``DEFAULT_FAIL_UNDER``
    docstring/comment and the coverage docs in CLAUDE.md / AGENTS.md /
    .github/AGENTS.md (maintainer decision 2026-05-15).
    """
    assert DEFAULT_FAIL_UNDER == 75


def test_stage01_public_projects_flag_is_documented_in_help() -> None:
    """The Stage 01 CLI exposes public-scope all-projects validation."""
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "scripts/pipeline/stage_01_test.py", "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode == 0
    assert "--public-projects" in proc.stdout
    assert "--profile" in proc.stdout
    assert "--project-workers" in proc.stdout


def test_stage01_parallel_flag_is_documented_in_help() -> None:
    """The Stage 01 CLI exposes opt-in pytest-xdist parallelism via -n/--parallel."""
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "scripts/pipeline/stage_01_test.py", "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode == 0
    assert "--parallel" in proc.stdout
    assert "PYTEST_XDIST_WORKERS" in proc.stdout


def test_stage01_public_projects_requires_all_projects_mode() -> None:
    """The public-scope flag is not silently ignored on the wrong command."""
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "scripts/pipeline/stage_01_test.py", "--public-projects"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode != 0
    assert "--public-projects requires --project-only --all-projects" in proc.stderr


def test_stage01_invalid_profile_is_rejected() -> None:
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "scripts/pipeline/stage_01_test.py", "--profile", "bogus"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode != 0
    assert "invalid choice" in proc.stderr


def test_stage01_invalid_project_workers_is_rejected() -> None:
    proc = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "scripts/pipeline/stage_01_test.py",
            "--project-only",
            "--all-projects",
            "--project-workers",
            "0",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode != 0
    assert "project-workers" in proc.stderr


def test_stage01_project_workers_requires_all_projects_mode() -> None:
    proc = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "scripts/pipeline/stage_01_test.py",
            "--project-workers",
            "2",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode != 0
    assert "--project-workers requires --project-only --all-projects" in proc.stderr


def test_stage01_rejects_hidden_nested_concurrency_from_env() -> None:
    env = os.environ.copy()
    env["PYTEST_XDIST_WORKERS"] = "2"
    proc = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "scripts/pipeline/stage_01_test.py",
            "--project-only",
            "--all-projects",
            "--project-workers",
            "2",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode != 0
    assert "--project-workers=2" in proc.stderr
    assert "PYTEST_XDIST_WORKERS" in proc.stderr
