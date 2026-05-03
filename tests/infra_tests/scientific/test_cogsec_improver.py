"""Tests for :mod:`infrastructure.scientific.cogsec_improver` (no mocks).

All tests use ``tmp_path`` and exercise the real AST round-trip.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from infrastructure.scientific.cogsec_improver import improve_file, improve_tree


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def test_improve_file_inserts_future_import_and_docstring(tmp_path: Path) -> None:
    """A bare module with no docstring or future import gets both inserted."""
    target = _write(tmp_path / "raw.py", "x = 1\n")

    result = improve_file(target)

    assert result["modified"] is True
    assert result["future"] is True
    assert result["docstring"] is True

    text = target.read_text()
    # Real AST round-trip: file is still valid Python
    tree = ast.parse(text)
    # First statement is the docstring expression
    assert (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    )
    assert "from __future__ import annotations" in text


def test_improve_file_replaces_bare_except(tmp_path: Path) -> None:
    """Bare ``except:`` becomes ``except Exception:`` with indentation preserved."""
    src = (
        '"""Existing docstring."""\n'
        "from __future__ import annotations\n"
        "\n"
        "def f():\n"
        "    try:\n"
        "        return 1\n"
        "    except:\n"
        "        return 0\n"
    )
    target = _write(tmp_path / "withexcept.py", src)

    result = improve_file(target)

    assert result["modified"] is True
    assert result["except_"] == 1
    assert result["future"] is False  # already present
    assert result["docstring"] is False  # already present

    text = target.read_text()
    assert "except Exception:" in text
    assert "    except Exception:\n" in text  # indentation preserved
    # Still parses
    ast.parse(text)


def test_improve_file_idempotent_on_clean_source(tmp_path: Path) -> None:
    """A file that already conforms is not rewritten."""
    src = (
        '"""Already fine."""\n'
        "from __future__ import annotations\n"
        "\n"
        "x = 1\n"
    )
    target = _write(tmp_path / "clean.py", src)
    before = target.read_text()

    result = improve_file(target)

    assert result["modified"] is False
    assert target.read_text() == before


def test_improve_file_handles_syntax_error(tmp_path: Path) -> None:
    """Invalid Python returns an ``error`` field and does not modify the file."""
    target = _write(tmp_path / "broken.py", "def (\n")
    before = target.read_text()

    result = improve_file(target)

    assert "error" in result
    assert result["modified"] is False
    assert target.read_text() == before


def test_improve_tree_skips_tests_and_aggregates(tmp_path: Path) -> None:
    """``improve_tree`` walks the source root and skips ``tests/``."""
    # Source file that needs all three transformations
    _write(tmp_path / "src" / "a.py", "x = 1\n")
    # Source file that already conforms
    _write(
        tmp_path / "src" / "b.py",
        '"""b."""\nfrom __future__ import annotations\n\ny = 2\n',
    )
    # Tests directory should be skipped — leave it broken to prove it's untouched
    broken_test = _write(tmp_path / "src" / "tests" / "test_x.py", "def (\n")

    summary = improve_tree(tmp_path / "src")

    assert summary["files"] == 2  # tests/ skipped
    assert summary["modified"] == 1
    assert summary["future"] == 1
    assert summary["docstring"] == 1
    assert summary["except_"] == 0
    assert summary["errors"] == []
    # tests/ file untouched
    assert broken_test.read_text() == "def (\n"


def test_improve_file_does_not_double_insert_future_import(tmp_path: Path) -> None:
    """Re-running ``improve_file`` on its own output is a no-op."""
    target = _write(tmp_path / "x.py", "x = 1\n")

    improve_file(target)
    after_first = target.read_text()
    second = improve_file(target)

    assert second["modified"] is False
    assert target.read_text() == after_first
    assert after_first.count("from __future__ import annotations") == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
