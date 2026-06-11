"""Mechanical Python source improvements (AST-aware, idempotent).

Used by ``scripts/maintenance/batch_cogsec_improve.py`` and available to any project
that wants conservative hygiene fixes without domain-specific logic.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import TypedDict

__all__ = [
    "BatchImprovementSummary",
    "FileImprovementResult",
    "improve_file",
    "improve_tree",
]


class FileImprovementResult(TypedDict, total=False):
    """Result of improving a single Python file."""

    file: str
    future: bool
    docstring: bool
    except_: int
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
    """Apply mechanical improvements to a single Python file in-place."""
    source = path.read_text()
    lines = source.splitlines(keepends=True)
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return {"file": str(path), "error": str(exc), "modified": False}

    changes: FileImprovementResult = {
        "file": str(path),
        "future": False,
        "docstring": False,
        "except_": 0,
        "modified": False,
    }

    if "from __future__ import annotations" not in source:
        insert_line = 1
        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)
        ):
            insert_line = 2
        lines.insert(insert_line - 1, "from __future__ import annotations\n\n")
        changes["future"] = True
        changes["modified"] = True

    new_lines: list[str] = []
    for line in lines:
        match = _BARE_EXCEPT_RE.match(line)
        if match:
            new_line = f"{match.group(1)}except Exception:\n"
            new_lines.append(new_line)
            if new_line != line:
                changes["except_"] = (changes.get("except_", 0) or 0) + 1
                changes["modified"] = True
        else:
            new_lines.append(line)

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
        doc = f'"""{path.stem.replace("_", " ").title()} module.\n\nAuto-generated module docstring.\n"""\n\n'
        new_lines.insert(0, doc)
        changes["docstring"] = True
        changes["modified"] = True

    if changes["modified"]:
        path.write_text("".join(new_lines))
    return changes


def improve_tree(root: Path) -> BatchImprovementSummary:
    """Apply :func:`improve_file` to every ``*.py`` under ``root``."""
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
