"""Tests for repository-wide documentation lint orchestration."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.validation.docs.lint_runner import doc_roots, run_docs_lint


def _write(path: Path, body: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_doc_roots_exclude_private_project_symlinks(tmp_path: Path) -> None:
    """Public lint roots must not traverse local sidecar project symlinks."""
    repo = tmp_path / "template"
    repo.mkdir()
    _write(repo / "README.md", "# template")
    _write(repo / "docs" / "README.md", "# docs")
    _write(repo / "tests" / "README.md", "# tests")

    public_project = repo / "projects" / PUBLIC_PROJECT_NAMES[0]
    _write(public_project / "README.md", "# public")

    sidecar_root = tmp_path / "projects-sidecar" / "active" / "private_project"
    _write(sidecar_root / "README.md", "# private")
    (repo / "projects").mkdir(exist_ok=True)
    (repo / "projects" / "private_project").symlink_to(sidecar_root, target_is_directory=True)

    roots = doc_roots(repo)
    resolved_roots = {root.resolve() for root in roots}

    assert public_project.resolve() in resolved_roots
    assert sidecar_root.resolve() not in resolved_roots
    assert (repo / "tests").resolve() in resolved_roots


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "template"
    repo.mkdir()
    _write(repo / "README.md", "# template\n")
    _write(repo / "docs" / "README.md", "# docs\n")
    return repo


def test_doc_roots_scoped_paths_limit_scope(tmp_path: Path) -> None:
    """Scoped --paths restricts discovery to the named entries only."""
    repo = _make_repo(tmp_path)
    roots = doc_roots(repo, paths=["README.md", "docs"])
    resolved = {root.resolve() for root in roots}
    assert (repo / "README.md").resolve() in resolved
    assert (repo / "docs").resolve() in resolved
    assert len(resolved) == 2


def test_doc_roots_rejects_missing_path(tmp_path: Path) -> None:
    """A nonexistent scoped path fails loudly instead of silently shrinking scope."""
    repo = _make_repo(tmp_path)
    with pytest.raises(ValueError, match="does not exist"):
        doc_roots(repo, paths=["nope/missing.md"])


def test_doc_roots_rejects_path_outside_repo(tmp_path: Path) -> None:
    """A scoped path escaping the repo root is rejected (fail closed)."""
    repo = _make_repo(tmp_path)
    outside = tmp_path / "outside.md"
    _write(outside, "# outside\n")
    with pytest.raises(ValueError, match="escapes the repo root"):
        doc_roots(repo, paths=[str(outside)])


def test_run_docs_lint_links_only_scoped(tmp_path: Path) -> None:
    """Scoped links-only lint runs real discovery over just the named paths."""
    repo = _make_repo(tmp_path)
    _write(repo / "notes.md", "[broken](./missing-target.md)\n")

    report = run_docs_lint(repo, links_only=True, paths=["notes.md"])
    assert report.broken_links is not None
    assert len(report.broken_links) == 1
    assert report.broken_links[0].file.name == "notes.md"


def test_run_docs_lint_links_only_scoped_clean(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    _write(repo / "docs" / "ok.md", "[fine](README.md)\n")

    report = run_docs_lint(repo, links_only=True, paths=["docs"])
    assert report.broken_links == []
    assert report.failed is False
