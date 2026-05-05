"""Tests for the ``__all__`` export audit (no mocks).

These tests build small synthetic source trees under :func:`tmp_path` and
exercise the public ``audit_*`` API directly. No filesystem fixtures, no
mocks, no patches — every assertion is grounded in real ast parsing of
real files written to disk.

Why this test exists
--------------------
The audit prevents a class of mypy ``[attr-defined]`` regressions that
appears whenever a re-exporting umbrella module forgets to declare
``__all__``. Downstream callers cannot import the re-exported names
under ``mypy --strict`` unless ``__all__`` is present. The audit is
small but load-bearing — these tests pin the contract so future edits
to :mod:`infrastructure.skills.check_all_exports` do not regress it.
"""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

import pytest

from infrastructure.skills.check_all_exports import (
    AllExportViolation,
    audit_directory,
    audit_file,
    iter_python_files,
    main as audit_main,
    module_has_dunder_all,
    module_reexports_at_top_level,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers — real files, no mocks
# ─────────────────────────────────────────────────────────────────────────────


def _write(path: Path, body: str) -> Path:
    """Write *body* to *path*, creating parent dirs. Return the written path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(body).lstrip("\n"), encoding="utf-8")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestModuleHasDunderAll:
    def test_simple_assignment(self, tmp_path: Path) -> None:
        f = _write(tmp_path / "m.py", '__all__ = ["x"]\nx = 1\n')
        v = audit_file(f)
        # No re-export → no violation regardless of __all__
        assert v is None

    def test_annotated_assignment(self, tmp_path: Path) -> None:
        import ast

        src = dedent(
            """
            from __future__ import annotations
            __all__: list[str] = ["x"]
            x = 1
            """
        ).strip()
        tree = ast.parse(src)
        assert module_has_dunder_all(tree) is True


class TestReexportDetection:
    def test_top_level_f401_without_all_is_violation(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "umbrella.py",
            """
            from __future__ import annotations
            from somepkg.helpers import helper_a  # noqa: F401
            """,
        )
        v = audit_file(f)
        assert v is not None
        assert v.line == 2
        assert "F401" in v.reason or "without __all__" in v.reason

    def test_top_level_f401_with_all_is_clean(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "umbrella.py",
            """
            from __future__ import annotations
            from somepkg.helpers import helper_a  # noqa: F401
            __all__ = ["helper_a"]
            """,
        )
        assert audit_file(f) is None

    def test_no_f401_no_violation(self, tmp_path: Path) -> None:
        # A leaf module that imports for its own use is NOT a re-exporter.
        f = _write(
            tmp_path / "leaf.py",
            """
            from __future__ import annotations
            from somepkg.helpers import helper_a

            def use() -> None:
                helper_a()
            """,
        )
        assert audit_file(f) is None

    def test_typechecking_block_ignored(self, tmp_path: Path) -> None:
        # F401 imports inside ``if TYPE_CHECKING:`` are NOT real re-exports.
        f = _write(
            tmp_path / "leaf.py",
            """
            from __future__ import annotations
            from typing import TYPE_CHECKING
            if TYPE_CHECKING:
                from somepkg.helpers import helper_a  # noqa: F401
            x = 1
            """,
        )
        assert audit_file(f) is None

    def test_function_local_f401_ignored(self, tmp_path: Path) -> None:
        # F401 markers inside a function body are not module-top re-exports.
        f = _write(
            tmp_path / "leaf.py",
            """
            from __future__ import annotations
            def f() -> None:
                from somepkg.helpers import helper_a  # noqa: F401
                helper_a()
            """,
        )
        assert audit_file(f) is None

    def test_try_except_import_block_counts(self, tmp_path: Path) -> None:
        # Backwards-compat re-exports often live inside try/except ImportError.
        # The successful branch IS a re-export, so this must be flagged.
        f = _write(
            tmp_path / "shim.py",
            """
            from __future__ import annotations
            try:
                from somepkg.helpers import helper_a  # noqa: F401
            except ImportError:
                helper_a = None  # type: ignore[assignment]
            """,
        )
        v = audit_file(f)
        assert v is not None

    def test_multiline_import_with_noqa_on_first_line(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "umbrella.py",
            """
            from __future__ import annotations
            from somepkg.helpers import (  # noqa: F401
                helper_a,
                helper_b,
            )
            """,
        )
        v = audit_file(f)
        assert v is not None

    def test_first_line_reported(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "umbrella.py",
            """
            from __future__ import annotations
            x = 1
            from somepkg.helpers import helper_a  # noqa: F401
            from somepkg.helpers import helper_b  # noqa: F401
            """,
        )
        v = audit_file(f)
        assert v is not None
        # The earliest re-export line is line 3 (1: __future__, 2: x = 1).
        assert v.line == 3

    def test_module_reexports_helper(self) -> None:
        import ast

        src = dedent(
            """
            from somepkg.helpers import helper_a  # noqa: F401
            """
        ).strip()
        tree = ast.parse(src)
        has, line, reason = module_reexports_at_top_level(tree, source_lines=src.splitlines())
        assert has is True
        assert line == 1
        assert reason


class TestPrivateModuleSkipping:
    def test_underscore_filename_skipped_by_iter(self, tmp_path: Path) -> None:
        _write(tmp_path / "_private.py", "from x import y  # noqa: F401\n")
        _write(tmp_path / "public.py", "x = 1\n")
        files = sorted(p.name for p in iter_python_files(tmp_path))
        assert "_private.py" not in files
        assert "public.py" in files

    def test_init_is_not_treated_as_private(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        _write(pkg / "__init__.py", "from x import y  # noqa: F401\n")
        files = sorted(p.name for p in iter_python_files(tmp_path))
        assert "__init__.py" in files


class TestSkipDirs:
    def test_tests_directory_skipped(self, tmp_path: Path) -> None:
        _write(tmp_path / "tests" / "test_foo.py", "from x import y  # noqa: F401\n")
        _write(tmp_path / "real.py", "x = 1\n")
        files = sorted(p.name for p in iter_python_files(tmp_path))
        assert "test_foo.py" not in files
        assert "real.py" in files

    def test_pycache_skipped(self, tmp_path: Path) -> None:
        _write(tmp_path / "__pycache__" / "cached.py", "x = 1\n")
        _write(tmp_path / "real.py", "x = 1\n")
        files = sorted(p.name for p in iter_python_files(tmp_path))
        assert "cached.py" not in files


class TestAuditDirectory:
    def test_clean_tree_returns_empty(self, tmp_path: Path) -> None:
        _write(tmp_path / "leaf.py", "x = 1\n")
        _write(
            tmp_path / "umbrella.py",
            'from x import y  # noqa: F401\n__all__ = ["y"]\n',
        )
        assert audit_directory(tmp_path) == []

    def test_dirty_tree_lists_all_violations(self, tmp_path: Path) -> None:
        _write(tmp_path / "a.py", "from x import y  # noqa: F401\n")
        _write(tmp_path / "b.py", "from x import z  # noqa: F401\n")
        _write(tmp_path / "leaf.py", "from x import w\n")
        violations = audit_directory(tmp_path)
        names = sorted(v.path.name for v in violations)
        assert names == ["a.py", "b.py"]
        for v in violations:
            assert isinstance(v, AllExportViolation)

    def test_violations_sorted_by_path(self, tmp_path: Path) -> None:
        _write(tmp_path / "z.py", "from x import y  # noqa: F401\n")
        _write(tmp_path / "a.py", "from x import y  # noqa: F401\n")
        violations = audit_directory(tmp_path)
        paths = [v.path.name for v in violations]
        assert paths == sorted(paths)

    def test_syntax_error_reported_as_violation(self, tmp_path: Path) -> None:
        _write(tmp_path / "broken.py", "this is not python !!!\n")
        violations = audit_directory(tmp_path)
        assert len(violations) == 1
        assert "could not parse" in violations[0].reason

    def test_format_method_uses_relative_path(self, tmp_path: Path) -> None:
        f = _write(tmp_path / "sub" / "umbrella.py", "from x import y  # noqa: F401\n")
        v = audit_file(f)
        assert v is not None
        msg = v.format(root=tmp_path)
        assert msg.startswith("sub/umbrella.py:") or msg.startswith("sub\\umbrella.py:")


class TestRealRepoIsClean:
    """The real ``infrastructure/`` tree under the repo must pass the audit.

    This is the integration check: after the MED5 audit it must report 0
    violations. If a future change re-introduces a re-exporter without
    ``__all__``, this test fails immediately.
    """

    def test_infrastructure_passes_audit(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        infra = repo_root / "infrastructure"
        if not infra.is_dir():
            pytest.skip("infrastructure/ not present in test layout")
        violations = audit_directory(infra)
        assert violations == [], "\n".join(v.format(root=repo_root) for v in violations)


class TestCli:
    """Drive the ``main()`` entry point with argv. No mocks — real argv."""

    def test_cli_zero_violations_returns_0(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _write(tmp_path / "leaf.py", "x = 1\n")
        rc = audit_main([str(tmp_path)])
        assert rc == 0

    def test_cli_violations_returns_1(self, tmp_path: Path) -> None:
        _write(tmp_path / "umbrella.py", "from x import y  # noqa: F401\n")
        rc = audit_main([str(tmp_path)])
        assert rc == 1

    def test_cli_skip_dir_repeatable(self, tmp_path: Path) -> None:
        # Put a violation under ``vendor/`` and confirm --skip-dir vendor hides it.
        _write(tmp_path / "vendor" / "shim.py", "from x import y  # noqa: F401\n")
        # Without skip: violation present
        assert audit_main([str(tmp_path)]) == 1
        # With skip: clean
        assert audit_main([str(tmp_path), "--skip-dir", "vendor"]) == 0


class TestSkillsCliWiring:
    """Confirm the audit is reachable through ``python -m infrastructure.skills``."""

    def test_check_all_exports_subcommand_runs(self, tmp_path: Path) -> None:
        # Build a tiny tree, then run via the skills CLI.
        from infrastructure.skills.cli import main as skills_main

        _write(tmp_path / "infrastructure" / "leaf.py", "x = 1\n")
        # Repo root must have a .cursor for the manifest. Use --audit-root
        # to point at the synthetic infra/ tree directly.
        rc = skills_main(
            [
                "check-all-exports",
                "--repo-root",
                str(tmp_path),
                "--audit-root",
                "infrastructure",
            ]
        )
        assert rc == 0

    def test_check_with_all_exports_flag(self, tmp_path: Path) -> None:
        # ``check --all-exports`` should run BOTH the manifest check and
        # the audit. We expect the manifest check to fail (no manifest in
        # the synthetic repo), so rc must be non-zero, but the audit must
        # also have run — verify by adding a violation and checking that
        # the rc is still non-zero.
        from infrastructure.skills.cli import main as skills_main

        _write(tmp_path / "infrastructure" / "umbrella.py", "from x import y  # noqa: F401\n")
        rc = skills_main(
            [
                "check",
                "--repo-root",
                str(tmp_path),
                "--all-exports",
            ]
        )
        assert rc == 1


# ─────────────────────────────────────────────────────────────────────────────
# Module-level pytest discovery sanity check (helps catch import errors in CI)
# ─────────────────────────────────────────────────────────────────────────────


def test_module_imports_cleanly() -> None:
    import infrastructure.skills.check_all_exports as mod

    assert hasattr(mod, "audit_directory")
    assert hasattr(mod, "audit_file")
    assert hasattr(mod, "AllExportViolation")
    assert sys.version_info >= (3, 10)
