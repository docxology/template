"""Mechanical Python source improvements for cognitive_integrity sources.

This module contains the AST-aware text transformations used by
``scripts/batch_cogsec_improve.py``. Keeping the logic here lets the script
stay a thin orchestrator (parse args → call function → exit) and gives us a
unit-tested entry point.

Transformations applied (best-effort, idempotent):

1. Insert ``from __future__ import annotations`` at the top of the file
   (after a module docstring, if present), unless already present.
2. Replace bare ``except:`` with ``except Exception:`` while preserving
   indentation.
3. Insert a minimal Google-ish module docstring if none exists after the
   future-import insert.

The functions are deliberately conservative — they operate on text plus a
single :func:`ast.parse` round-trip, so a file that already conforms is
left byte-for-byte unchanged.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import TypedDict

__all__ = [
    "FileImprovementResult",
    "BatchImprovementSummary",
    "improve_file",
    "improve_tree",
]


class FileImprovementResult(TypedDict, total=False):
    """Result of improving a single Python file."""

    file: str
    future: bool
    docstring: bool
    except_: int  # number of bare-except replacements
    modified: bool
    error: str


class BatchImprovementSummary(TypedDict):
    """Aggregate counters for a batch run over a source tree."""

    files: int
    future: int
    docstring: int
    except_: int
    modified: int
    errors: list[str]


_BARE_EXCEPT_RE = re.compile(r"^(\s*)except\s*:")


def improve_file(path: Path) -> FileImprovementResult:
    """Apply mechanical improvements to a single Python file in-place.

    Args:
        path: Path to a ``.py`` file.

    Returns:
        A :class:`FileImprovementResult` describing what changed. The file is
        only rewritten when ``modified`` is true. If the file fails to parse,
        the result contains an ``error`` key and ``modified`` is false.
    """
    source = path.read_text()
    lines = source.splitlines(keepends=True)
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"file": str(path), "error": str(e), "modified": False}

    changes: FileImprovementResult = {
        "file": str(path),
        "future": False,
        "docstring": False,
        "except_": 0,
        "modified": False,
    }

    # 1. __future__ import (after module docstring, if any)
    if "from __future__ import annotations" not in source:
        insert_line = 1
        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)
        ):
            insert_line = 2  # after docstring
        lines.insert(insert_line - 1, "from __future__ import annotations\n\n")
        changes["future"] = True
        changes["modified"] = True

    # 2. Bare except → except Exception
    new_lines: list[str] = []
    for line in lines:
        m = _BARE_EXCEPT_RE.match(line)
        if m:
            new_line = f"{m.group(1)}except Exception:\n"
            new_lines.append(new_line)
            if new_line != line:
                changes["except_"] = (changes.get("except_", 0) or 0) + 1
                changes["modified"] = True
        else:
            new_lines.append(line)

    # 3. Module docstring (only if still missing after future-insert)
    combined = "".join(new_lines)
    try:
        tree2: ast.Module | None = ast.parse(combined)
    except SyntaxError:
        tree2 = None
    has_docstring = bool(
        tree2
        and tree2.body
        and isinstance(tree2.body[0], ast.Expr)
        and isinstance(tree2.body[0].value, ast.Constant)
        and isinstance(tree2.body[0].value.value, str)
    )
    if tree2 is not None and not has_docstring:
        doc = f'"""{path.stem.replace("_", " ").title()} module.\n\nPart of the Cognitive Integrity Framework.\n"""\n\n'
        new_lines.insert(0, doc)
        changes["docstring"] = True
        changes["modified"] = True

    if changes["modified"]:
        path.write_text("".join(new_lines))
    return changes


def improve_tree(root: Path) -> BatchImprovementSummary:
    """Apply :func:`improve_file` to every ``*.py`` under ``root``.

    Skips ``tests/``, ``.venv/``, and ``__pycache__/`` segments. Errors are
    collected and reported but do not abort the run.

    Args:
        root: Directory to walk recursively.

    Returns:
        A :class:`BatchImprovementSummary` with aggregate counters.
    """
    summary: BatchImprovementSummary = {
        "files": 0,
        "future": 0,
        "docstring": 0,
        "except_": 0,
        "modified": 0,
        "errors": [],
    }

    for pyfile in sorted(root.rglob("*.py")):
        if "tests" in pyfile.parts or ".venv" in pyfile.parts or "__pycache__" in pyfile.parts:
            continue
        result = improve_file(pyfile)
        summary["files"] += 1
        if "error" in result:
            summary["errors"].append(f"{result['file']}: {result['error']}")
            continue
        if result.get("future"):
            summary["future"] += 1
        if result.get("docstring"):
            summary["docstring"] += 1
        summary["except_"] += int(result.get("except_", 0) or 0)
        if result.get("modified"):
            summary["modified"] += 1

    return summary
