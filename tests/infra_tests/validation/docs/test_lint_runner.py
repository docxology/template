"""Tests for repository-wide documentation lint orchestration."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.validation.docs.lint_runner import doc_roots


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
