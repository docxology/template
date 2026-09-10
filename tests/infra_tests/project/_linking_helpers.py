"""Shared scaffolding for the split infrastructure.project.linking test modules (formerly test_linking.py)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from infrastructure.project.linking import ACTIVE_SUBDIR, LIFECYCLE_SUBDIRS


def _make_repo(tmp_path: Path) -> Path:
    """A template repo root with a real projects/ dir."""
    repo = tmp_path / "template"
    (repo / "projects").mkdir(parents=True)
    return repo


def _make_private(tmp_path: Path, *, active: Sequence[str] = (), name: str = "projects") -> Path:
    """A private companion repo with every supported lifecycle folder."""
    private = tmp_path / name
    for sub in LIFECYCLE_SUBDIRS:
        (private / sub).mkdir(parents=True)
    for proj in active:
        _make_project(private / ACTIVE_SUBDIR / proj)
    return private


def _make_project(path: Path) -> Path:
    """A minimal valid project (src/ with a .py + tests/)."""
    (path / "src").mkdir(parents=True)
    (path / "src" / "__init__.py").write_text("", encoding="utf-8")
    (path / "src" / "calc.py").write_text("def answer() -> int:\n    return 42\n", encoding="utf-8")
    (path / "tests").mkdir()
    (path / "tests" / "__init__.py").write_text("", encoding="utf-8")
    return path


def _mirror(repo: Path, lifecycle: str = ACTIVE_SUBDIR) -> Path:
    """Ensure (and return) the local mirror dir ``projects/<lifecycle>``."""
    mirror = repo / "projects" / lifecycle
    mirror.mkdir(parents=True, exist_ok=True)
    return mirror
