"""Smoke tests for the tracked generated-artifact guard."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from infrastructure.project.git_guards import (
    is_empty_public_template_output,
    is_generated_artifact_path,
    is_hidden_public_template_output,
    tracked_secret_findings,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_generated_artifact_path_matcher() -> None:
    """Matcher catches disposable paths without flagging source files."""
    assert not is_generated_artifact_path("projects/templates/template_code_project/output/data/results.json")
    assert is_generated_artifact_path("projects/templates/template_code_project/.DS_Store")
    assert is_generated_artifact_path("projects/demo/src/demo.egg-info/PKG-INFO")
    assert is_generated_artifact_path("coverage_project.json")

    assert not is_generated_artifact_path("projects/templates/template_code_project/src/optimizer.py")
    assert not is_generated_artifact_path("docs/_generated/COUNTS.md")

    assert is_generated_artifact_path("output/templates/template_code_project/pdf/template_code_project_combined.pdf")
    assert is_generated_artifact_path("output/templates/template_prose_project/figures/wordcount.png")
    assert is_generated_artifact_path("output/actinf_policy_entanglement_lean/pdf/x.pdf")
    assert is_generated_artifact_path("projects/working/private_project/output/data/x.csv")


def test_public_output_guard_rejects_hidden_and_empty_payloads(tmp_path: Path) -> None:
    """Portable public evidence cannot include dotfiles or empty payloads."""
    repo_root = tmp_path / "repo"
    hidden = "projects/templates/template_code_project/output/figures/.trace.png"
    empty = "projects/templates/template_code_project/output/figures/trace.png"
    (repo_root / hidden).parent.mkdir(parents=True)
    (repo_root / hidden).write_bytes(b"leftover")
    (repo_root / empty).touch()

    assert is_hidden_public_template_output(hidden)
    assert not is_hidden_public_template_output("projects/templates/template_code_project/output/figures/trace.png")
    assert is_empty_public_template_output(repo_root, empty)
    assert not is_empty_public_template_output(
        repo_root,
        "projects/templates/template_code_project/output/figures/__init__.py",
    )


@pytest.mark.timeout(240)  # repo-wide index scan measures ~40s here (measured 2026-08-21)
@pytest.mark.timeout(150)
def test_current_repo_has_no_tracked_generated_artifacts() -> None:
    """Repository index must stay free of regeneratable output artifacts."""
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/audit/check_tracked_generated_artifacts.py",
            "--repo-root",
            str(_repo_root()),
        ],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
        # The repo-wide index scan measures ~40s on this checkout (measured
        # 2026-08-21); a 30s cap made this smoke test flaky under load.
        timeout=120,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.timeout(120)  # full-tree tracked-blob scan measures ~23s here (measured 2026-08-21)
def test_current_repo_has_no_high_confidence_tracked_secrets() -> None:
    """Credential examples remain fixture-safe and real tokens are rejected."""
    repo_root = _repo_root()
    assert tracked_secret_findings(repo_root) == []


def test_tracked_secret_scan_reports_path_line_and_kind(tmp_path: Path) -> None:
    """The scanner reports evidence metadata without exposing the token value."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    secret = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
    note = repo_root / "note.txt"
    note.write_text(f"reviewed\n{secret}\n", encoding="utf-8")
    subprocess.run(["git", "init", "--quiet"], cwd=repo_root, check=True, timeout=30)
    subprocess.run(["git", "add", "note.txt"], cwd=repo_root, check=True, timeout=30)

    findings = tracked_secret_findings(repo_root)
    assert findings == ["note.txt:2:github-token"]
    assert secret not in "\n".join(findings)


def test_staged_secret_cli_reports_metadata_without_exposing_value(tmp_path: Path) -> None:
    """The pre-commit command reads the index and never echoes the credential."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    secret = "ghp_" + "Z9y8X7w6V5u4T3s2R1q0N9m8L7k6J5h4G3f2E1d0"
    note = repo_root / "note.txt"
    note.write_text(f"reviewed\n{secret}\n", encoding="utf-8")
    subprocess.run(["git", "init", "--quiet"], cwd=repo_root, check=True, timeout=30)
    subprocess.run(["git", "add", "note.txt"], cwd=repo_root, check=True, timeout=30)
    note.write_text("safe unstaged replacement\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/audit/check_staged_secrets.py",
            "--repo-root",
            str(repo_root),
        ],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode == 1
    assert "note.txt:2:github-token" in proc.stdout
    assert secret not in proc.stdout
    assert secret not in proc.stderr


def test_staged_secret_hook_is_index_scoped_and_always_runs() -> None:
    """The local guard runs before commit and through the manual hook surface."""
    config = yaml.safe_load((_repo_root() / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    hooks = {
        hook["id"]: hook
        for repository in config["repos"]
        if repository["repo"] == "local"
        for hook in repository["hooks"]
    }
    staged = hooks["staged-secret-scan"]
    command = " ".join(str(arg) for arg in staged["args"])

    assert "scripts/audit/check_staged_secrets.py" in command
    assert set(staged["stages"]) == {"pre-commit", "manual"}
    assert staged["pass_filenames"] is False
    assert staged["always_run"] is True


def test_projects_docs_are_trackable_while_rotating_projects_remain_ignored() -> None:
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
    public_output_proc = subprocess.run(
        [
            "git",
            "check-ignore",
            "--no-index",
            "projects/templates/template_code_project/output/data/results.json",
            "output/templates/template_code_project/pdf/template_code_project_combined.pdf",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert docs_proc.stdout == ""
    assert private_proc.returncode == 0
    assert (
        public_output_proc.stdout.strip()
        == "output/templates/template_code_project/pdf/template_code_project_combined.pdf"
    )


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
