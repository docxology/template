"""Glossary generation utilities for building an API index from `src/`.

Functions:
- build_api_index(src_dir): Parse Python files under src and extract public APIs
- generate_markdown_table(entries): Build a Markdown table from entries
- inject_between_markers(text, begin_marker, end_marker, content): Replace content between markers
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class ApiEntry:
    """Represents a public API entry from source code.

    Attributes:
        module: The module name where the API is defined
        name: The name of the function or class
        kind: The type of API ("function" or "class")
        summary: A brief description extracted from the docstring
    """

    module: str
    name: str
    kind: str  # "function" | "class"
    summary: str


def _first_sentence(doc: str | None) -> str:
    if not doc:
        return ""
    # Split on double newline or period for a short summary
    parts = doc.strip().split("\n\n", 1)
    first = parts[0]
    # Keep it short
    if len(first) > 200:
        first = first[:197] + "..."
    return " ".join(first.split())


def _iter_py_files(root: str) -> Iterable[str]:
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(".py") and (
                not fname.startswith("_") or fname == "__init__.py"
            ):
                yield os.path.join(dirpath, fname)


def build_api_index(src_dir: str) -> List[ApiEntry]:
    """Scan `src_dir` and collect public functions/classes with summaries.

    - Public = names not starting with underscore
    - Uses AST, no imports executed
    """
    entries: List[ApiEntry] = []
    for py_path in _iter_py_files(src_dir):
        try:
            with open(py_path, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=py_path)
        except Exception:
            # Skip files that fail to parse
            continue
        module = os.path.relpath(py_path, src_dir).replace(os.sep, ".")
        # Normalize module names deterministically without branching
        module = module.removesuffix(".py").removesuffix(".__init__")

        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                entries.append(
                    ApiEntry(
                        module=module,
                        name=node.name,
                        kind="function",
                        summary=_first_sentence(ast.get_docstring(node)),
                    )
                )
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                entries.append(
                    ApiEntry(
                        module=module,
                        name=node.name,
                        kind="class",
                        summary=_first_sentence(ast.get_docstring(node)),
                    )
                )
    # Sort by module then name
    entries.sort(key=lambda e: (e.module, e.name))
    return entries


def generate_markdown_table(entries: List[ApiEntry]) -> str:
    """Generate a Markdown table from API entries.

    Args:
        entries: List of API entries to format

    Returns:
        Markdown table string with headers and data rows
    """
    if not entries:
        return "No public APIs detected in `src/`."
    lines = [
        "| Module | Name | Kind | Summary |",
        "|---|---|---|---|",
    ]
    for e in entries:
        lines.append(f"| `{e.module}` | `{e.name}` | {e.kind} | {e.summary} |")
    return "\n".join(lines) + "\n"


def inject_between_markers(
    text: str, begin_marker: str, end_marker: str, content: str
) -> str:
    """Replace content between begin_marker and end_marker (inclusive markers preserved)."""
    start = text.find(begin_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1 or end <= start:
        # If markers not found, append a new block
        block = f"\n\n{begin_marker}\n{content}\n{end_marker}\n"
        return text + ("\n" if not text.endswith("\n") else "") + block
    start_end = start + len(begin_marker)
    return (
        text[:start_end]
        + "\n"
        + content
        + ("\n" if not content.endswith("\n") else "")
        + text[end:]
    )
