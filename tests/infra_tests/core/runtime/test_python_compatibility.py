"""Real-file tests for the Python 3.12 compatibility audit."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.runtime.python_compatibility import scan_python_312_compatibility
from infrastructure.project.public_scope import public_ci_source_paths


def test_public_python_surface_is_python_312_compatible(repo_root: Path) -> None:
    paths = [repo_root / relative for relative in public_ci_source_paths(repo_root)]

    issues = scan_python_312_compatibility(paths, repo_root=repo_root)

    assert issues == ()


def test_scanner_rejects_new_syntax_and_unguarded_standard_library(tmp_path: Path) -> None:
    (tmp_path / "future_syntax.py").write_text(
        "def identity[T = int](value: T) -> T:\n    return value\n",
        encoding="utf-8",
    )
    (tmp_path / "future_api.py").write_text("from typing import TypeIs\n", encoding="utf-8")

    issues = scan_python_312_compatibility([tmp_path], repo_root=tmp_path)

    assert {issue.rule for issue in issues} == {"PY312.API", "PY312.SYNTAX"}


def test_scanner_accepts_guarded_backports(tmp_path: Path) -> None:
    source = tmp_path / "guarded.py"
    source.write_text(
        """try:
    from typing import TypeIs
except ImportError:
    from typing_extensions import TypeIs
""",
        encoding="utf-8",
    )

    assert scan_python_312_compatibility([source], repo_root=tmp_path) == ()


def test_scanner_reports_repo_relative_display_paths(tmp_path: Path) -> None:
    """Reported ``path`` is repo-relative after the resolve-once optimization.

    Guard: the display path must stay identical to a `path.resolve()`
    relative-to `repo_root.resolve()` rendering even though the scanner now
    resolves each source file only once.
    """
    repo = tmp_path / "repo"
    (repo / "pkg").mkdir(parents=True)
    bad = repo / "pkg" / "bad.py"
    bad.write_text("from typing import TypeIs\n", encoding="utf-8")

    issues = scan_python_312_compatibility([repo / "pkg"], repo_root=repo)

    assert issues
    assert {issue.rule for issue in issues} == {"PY312.API"}
    assert all(issue.path == "pkg/bad.py" for issue in issues)
    assert all(not Path(issue.path).is_absolute() for issue in issues)


def test_python_312_stdlib_and_syntax_are_supported(tmp_path: Path) -> None:
    source = tmp_path / "supported.py"
    source.write_text(
        "import tomllib\nfrom datetime import UTC\nfrom typing import TypeAliasType\ntype Entry = str\n",
        encoding="utf-8",
    )
    assert scan_python_312_compatibility([source], repo_root=tmp_path) == ()
