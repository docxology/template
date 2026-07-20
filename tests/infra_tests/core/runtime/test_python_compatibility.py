"""Real-file tests for the Python 3.10 compatibility audit."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.runtime.python_compatibility import scan_python_310_compatibility
from infrastructure.project.public_scope import public_ci_source_paths


def test_public_python_surface_is_python_310_compatible(repo_root: Path) -> None:
    paths = [repo_root / relative for relative in public_ci_source_paths(repo_root)]

    issues = scan_python_310_compatibility(paths, repo_root=repo_root)

    assert issues == ()


def test_scanner_rejects_new_syntax_and_unguarded_standard_library(tmp_path: Path) -> None:
    (tmp_path / "future_syntax.py").write_text(
        "try:\n    pass\nexcept* ValueError:\n    pass\n",
        encoding="utf-8",
    )
    (tmp_path / "future_api.py").write_text("import tomllib\nfrom enum import StrEnum\n", encoding="utf-8")

    issues = scan_python_310_compatibility([tmp_path], repo_root=tmp_path)

    assert {issue.rule for issue in issues} == {"PY310.API", "PY310.SYNTAX"}


def test_scanner_accepts_guarded_backports(tmp_path: Path) -> None:
    source = tmp_path / "guarded.py"
    source.write_text(
        """try:
    import tomllib
    from typing import NotRequired
except ImportError:
    import tomli as tomllib
    from typing_extensions import NotRequired
""",
        encoding="utf-8",
    )

    assert scan_python_310_compatibility([source], repo_root=tmp_path) == ()
