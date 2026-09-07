"""Shared helpers for the ``test_counts_*`` modules (moved from test_counts_doc.py)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.documentation.counts_coverage import _COVERAGE_COPY_SUPPORT_SPECS


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _initialize_test_git_repository(repo_root: Path) -> str:
    """Create one committed temporary repository and return its exact HEAD."""
    subprocess.run(["git", "init", "-q", str(repo_root)], check=True)
    # The initial commit must not leave background maintenance racing a later
    # byte-and-mtime snapshot of canonical Git metadata.
    for key, value in (("maintenance.auto", "false"), ("gc.auto", "0")):
        subprocess.run(["git", "-C", str(repo_root), "config", key, value], check=True)
    subprocess.run(["git", "-C", str(repo_root), "config", "user.name", "Counts Test"], check=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "config", "user.email", "counts@example.invalid"],
        check=True,
    )
    subprocess.run(["git", "-C", str(repo_root), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "-c", "commit.gpgsign=false", "commit", "-qm", "initial"],
        check=True,
    )
    return subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write_test_coverage_support_closure(repo_root: Path) -> None:
    """Create real synthetic sources for every declared support-closure row."""
    for spec in _COVERAGE_COPY_SUPPORT_SPECS:
        path = repo_root / spec.relative_path
        if spec.kind == "directory":
            path.mkdir(parents=True, exist_ok=True)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {spec.relative_path.as_posix()}\n", encoding="utf-8")


def _regular_file_snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    """Capture regular-file bytes and mtimes without following symlinks."""
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def _coverage_support_file_snapshot(repo_root: Path) -> dict[str, tuple[bytes, int]]:
    """Capture the canonical support-file bytes and mtimes."""
    return {
        spec.relative_path.as_posix(): (
            (repo_root / spec.relative_path).read_bytes(),
            (repo_root / spec.relative_path).stat().st_mtime_ns,
        )
        for spec in _COVERAGE_COPY_SUPPORT_SPECS
        if spec.kind == "file"
    }


def _repo_root_anchor(spec) -> str:
    """Map a disposable-tree support spec to its canonical repo-root path."""
    return spec.relative_path.as_posix()
