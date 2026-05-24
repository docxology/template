"""Tests for folder-level AGENTS.md / README.md coverage."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from infrastructure.validation.docs.doc_pair_lint import (
    find_doc_pair_issues,
    is_doc_pair_excluded_path,
)


def _write(path: Path, body: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_find_doc_pair_issues_flags_missing_pairs(tmp_path: Path) -> None:
    """Content directories need both docs; generated dirs are ignored."""
    _write(tmp_path / "README.md")
    _write(tmp_path / "AGENTS.md")

    _write(tmp_path / "docs" / "README.md")
    _write(tmp_path / "docs" / "guide.md")

    _write(tmp_path / "tests" / "unit" / "test_example.py")
    _write(tmp_path / "projects" / "template_code_project" / "src" / "pkg.egg-info" / "PKG-INFO")
    _write(tmp_path / "projects" / "template_code_project" / "output" / "report.md")

    issues = find_doc_pair_issues(
        tmp_path,
        roots=("docs", "tests", "projects/template_code_project"),
    )

    by_path = {issue.path: issue for issue in issues}
    assert by_path[Path("docs")].missing_readme is False
    assert by_path[Path("docs")].missing_agents is True
    assert by_path[Path("tests")].missing_readme is True
    assert by_path[Path("tests")].missing_agents is True
    assert by_path[Path("tests/unit")].missing_readme is True
    assert by_path[Path("tests/unit")].missing_agents is True
    assert all("egg-info" not in str(path) for path in by_path)
    assert all("output" not in str(path) for path in by_path)


def test_generated_and_local_paths_are_excluded() -> None:
    """The matcher excludes local/generated paths used by the template."""
    assert is_doc_pair_excluded_path(Path("projects/demo/src/demo.egg-info"))
    assert is_doc_pair_excluded_path(Path("projects/demo/output"))
    assert is_doc_pair_excluded_path(Path(".cursor/hooks/state"))
    assert is_doc_pair_excluded_path(Path("docs/prompts/_skill-eval/latest/with_skill/outputs"))
    assert not is_doc_pair_excluded_path(Path(".github/ISSUE_TEMPLATE"))


def test_find_doc_pair_issues_skips_skill_eval_workspace(tmp_path: Path) -> None:
    """Nested _skill-eval harness dirs must not require README/AGENTS pairs."""
    _write(tmp_path / "docs" / "README.md")
    _write(tmp_path / "docs" / "AGENTS.md")
    _write(tmp_path / "docs" / "prompts" / "_skill-eval" / "latest" / "with_skill" / "outputs" / "response.md")
    issues = find_doc_pair_issues(tmp_path, roots=("docs",))
    assert all("_skill-eval" not in str(issue.path) for issue in issues)


def test_current_repo_has_complete_permanent_template_doc_pairs() -> None:
    """Regression guard for the permanent template documentation surface."""
    repo_root = Path(__file__).resolve().parents[4]
    assert find_doc_pair_issues(repo_root) == []


def test_lint_docs_doc_pairs_only_json() -> None:
    """The public lint_docs entrypoint exposes doc-pair diagnostics."""
    repo_root = Path(__file__).resolve().parents[4]
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/lint_docs.py",
            "--doc-pairs-only",
            "--quiet",
            "--json",
            "--repo-root",
            str(repo_root),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["doc_pairs"] == []
