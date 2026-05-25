"""Smoke tests for the tracked generated-artifact guard."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from infrastructure.project.git_guards import is_generated_artifact_path


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

    # Scoped exception: the two exemplars' TOP-LEVEL output is tracked render-proof.
    assert not is_generated_artifact_path("output/template_code_project/pdf/template_code_project_combined.pdf")
    assert not is_generated_artifact_path("output/template_prose_project/figures/wordcount.png")
    # But a confidential/active project's top-level output stays guarded.
    assert is_generated_artifact_path("output/actinf_policy_entanglement_lean/pdf/x.pdf")


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


def test_projects_docs_are_trackable_while_rotating_projects_remain_ignored() -> None:
    """Gitignore keeps repo-level projects docs visible without exposing project trees."""
    repo_root = _repo_root()

    docs_proc = subprocess.run(
        ["git", "ls-files", "-ci", "--exclude-standard", "projects/*.md"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    private_proc = subprocess.run(
        ["git", "check-ignore", "-q", "--no-index", "projects/confidential_project/src/private.py"],
        cwd=repo_root,
        check=False,
        timeout=30,
    )

    assert docs_proc.stdout == ""
    assert private_proc.returncode == 0


def test_generated_fixture_payloads_are_ignored_but_committed_fixture_docs_are_visible() -> None:
    """Gitignore keeps downloaded fixture payloads out while leaving fixture docs/stubs trackable."""
    repo_root = _repo_root()
    generated_paths = [
        "tests/fixtures/real_codebases/requests/src/requests/__init__.py",
        "tests/fixtures/real_codebases/fastapi/fastapi/__init__.py",
        "tests/fixtures/timeseries/synthetic/series.json",
    ]
    committed_paths = [
        "tests/fixtures/real_codebases/README.md",
        "tests/fixtures/real_codebases/AGENTS.md",
        "tests/fixtures/private_project/cogant/tools/check_coverage_table.py",
    ]

    ignored_results = [
        subprocess.run(
            ["git", "check-ignore", "-q", "--no-index", path],
            cwd=repo_root,
            check=False,
            timeout=30,
        ).returncode
        for path in generated_paths
    ]
    visible_proc = subprocess.run(
        ["git", "check-ignore", "--no-index", *committed_paths],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert ignored_results == [0, 0, 0]
    assert visible_proc.stdout == ""
