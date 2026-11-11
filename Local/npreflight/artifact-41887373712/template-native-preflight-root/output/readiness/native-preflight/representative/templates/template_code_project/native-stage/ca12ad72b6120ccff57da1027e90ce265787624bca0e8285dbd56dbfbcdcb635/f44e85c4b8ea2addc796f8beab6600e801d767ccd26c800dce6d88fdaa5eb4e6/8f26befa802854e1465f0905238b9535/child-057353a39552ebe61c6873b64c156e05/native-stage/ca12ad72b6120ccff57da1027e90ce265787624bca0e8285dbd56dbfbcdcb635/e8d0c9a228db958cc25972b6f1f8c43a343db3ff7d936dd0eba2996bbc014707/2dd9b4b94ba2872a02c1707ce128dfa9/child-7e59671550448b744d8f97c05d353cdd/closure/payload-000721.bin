"""Resource bounds for the accessible Pandoc-AST composition boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import RenderingError


MAX_ACCESSIBLE_PANDOC_JSON_BYTES = 16 * 1024 * 1024
MAX_ACCESSIBLE_PANDOC_AST_NODES = 100_000
MAX_ACCESSIBLE_PANDOC_AST_DEPTH = 128


def validate_accessible_ast_limits(document: dict[str, Any], *, source: str) -> None:
    """Reject an AST whose size or nesting exceeds the renderer contract.

    Pandoc's normal JSON tree is shallow. Explicit bounds keep every recursive
    semantic helper below Python's recursion ceiling and prevent a hostile
    in-memory caller from turning writer-fallback projection into unbounded
    allocation work.
    """

    stack: list[tuple[object, int]] = [(document, 0)]
    observed_nodes = 0
    while stack:
        value, depth = stack.pop()
        observed_nodes += 1
        if observed_nodes > MAX_ACCESSIBLE_PANDOC_AST_NODES:
            raise RenderingError(
                "[slides.schema.pandoc-limits] Accessible Pandoc AST exceeds the node limit",
                context={
                    "source": source,
                    "diagnostic_code": "slides.schema.pandoc-limits",
                    "observed_nodes": observed_nodes,
                    "maximum_nodes": MAX_ACCESSIBLE_PANDOC_AST_NODES,
                },
            )
        if depth > MAX_ACCESSIBLE_PANDOC_AST_DEPTH:
            raise RenderingError(
                "[slides.schema.pandoc-limits] Accessible Pandoc AST exceeds the nesting limit",
                context={
                    "source": source,
                    "diagnostic_code": "slides.schema.pandoc-limits",
                    "observed_depth": depth,
                    "maximum_depth": MAX_ACCESSIBLE_PANDOC_AST_DEPTH,
                },
            )
        if isinstance(value, dict):
            stack.extend((item, depth + 1) for item in value.values())
        elif isinstance(value, list):
            stack.extend((item, depth + 1) for item in value)


def read_bounded_pandoc_json(path: Path, *, source: str) -> str:
    """Read one UTF-8 Pandoc JSON file only within the declared byte bound."""

    size = path.stat().st_size
    if size > MAX_ACCESSIBLE_PANDOC_JSON_BYTES:
        raise RenderingError(
            "[slides.schema.pandoc-limits] Accessible Pandoc JSON exceeds the byte limit",
            context={
                "source": source,
                "diagnostic_code": "slides.schema.pandoc-limits",
                "observed_bytes": size,
                "maximum_bytes": MAX_ACCESSIBLE_PANDOC_JSON_BYTES,
            },
        )
    return path.read_text(encoding="utf-8")


__all__ = [
    "MAX_ACCESSIBLE_PANDOC_AST_DEPTH",
    "MAX_ACCESSIBLE_PANDOC_AST_NODES",
    "MAX_ACCESSIBLE_PANDOC_JSON_BYTES",
    "read_bounded_pandoc_json",
    "validate_accessible_ast_limits",
]
