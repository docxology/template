"""Smoke tests for the tracked generated-artifact guard."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.check_tracked_generated_artifacts import is_generated_artifact_path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_generated_artifact_path_matcher() -> None:
    """Matcher catches disposable paths without flagging source files."""
    assert is_generated_artifact_path("projects/template_code_project/output/data/results.json")
    assert is_generated_artifact_path("projects/template_code_project/.DS_Store")
    assert is_generated_artifact_path("projects/demo/src/demo.egg-info/PKG-INFO")
    assert is_generated_artifact_path("coverage_project.json")

    assert not is_generated_artifact_path("projects/template_code_project/src/optimizer.py")
    assert not is_generated_artifact_path("docs/_generated/canonical_facts.md")


def test_current_repo_has_no_tracked_generated_artifacts() -> None:
    """Repository index must stay free of regeneratable output artifacts."""
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/check_tracked_generated_artifacts.py",
            "--repo-root",
            str(_repo_root()),
        ],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
