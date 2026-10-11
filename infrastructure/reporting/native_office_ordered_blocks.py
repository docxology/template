"""Complete ordered Office block correspondence, subordinate to native controls.

The three ASTs come from the existing Source/filter/package readers. This
predicate enumerates complete roles before comparison; no selected number or
substring chooses a paragraph. A retained path is a native package endpoint,
not a claim about ink, layout, style or scientific interpretation.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from typing import Any

from infrastructure.reporting.native_office_source_coverage import MAX_AST_BYTES, MAX_AST_NODES


def _blocks(ast: bytes, text: Callable[[Any], str]) -> list[dict[str, Any]]:
    if not ast or len(ast) > MAX_AST_BYTES:
        raise ValueError("ordered Office blocks require bounded actual AST bytes")
    document = json.loads(ast)
    if not isinstance(document, dict) or not isinstance(document.get("blocks"), list):
        raise ValueError("ordered Office blocks require an actual complete document")
    rows: list[dict[str, Any]] = []
    visited = 0

    def visit(value: Any, path: tuple[str | int, ...], context: str) -> None:
        nonlocal visited
        visited += 1
        if visited > MAX_AST_NODES or len(path) > 100:
            raise ValueError("ordered Office block traversal exceeded its finite budget")
        if isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, (*path, index), context)
            return
        if not isinstance(value, dict):
            return
        kind = value.get("t")
        if kind in {"Para", "Plain", "Header", "CodeBlock"}:
            content = value["c"]
            body = " ".join(text(value).split())
            # A scientific-only paragraph is still accounted for by the
            # complete mathematical occurrence predicate. It contains no
            # literal generated-field endpoint for this component to confer.
            if body:
                rows.append(
                    {
                        "ordinal": len(rows),
                        "ast_path": list(path),
                        "kind": "paragraph" if kind in {"Para", "Plain"} else kind,
                        "context": context,
                        "heading_level": content[0] if kind == "Header" else None,
                        "text": body,
                        "text_sha256": hashlib.sha256(body.encode()).hexdigest(),
                        "node_sha256": hashlib.sha256(
                            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
                        ).hexdigest(),
                    }
                )
            return
        if kind == "Image":
            return  # Image alternatives are not painted paragraphs.
        if kind == "Figure":
            content = value["c"]
            visit(content[1][1], (*path, "c", 1, 1), "figure-caption")
            visit(content[2], (*path, "c", 2), context)
            return
        if kind == "Table":
            content = value["c"]
            visit(content[1], (*path, "c", 1), "table-caption")
            # Retain each actual cell's ordered structural context. Never
            # flatten the grid into one searchable prose string.
            groups = [(content[3][1], (*path, "c", 3, 1), "head")]
            for index, body in enumerate(content[4]):
                groups.extend(
                    ((body[2], (*path, "c", 4, index, 2), "body-head"), (body[3], (*path, "c", 4, index, 3), "body"))
                )
            groups.append((content[5][1], (*path, "c", 5, 1), "foot"))
            row_index = 0
            for group, group_path, name in groups:
                for local, row in enumerate(group):
                    column = 0
                    for index, cell in enumerate(row[1]):
                        cell_context = f"table:{row_index}:{column}:{cell[2]}:{cell[3]}:{name}"
                        visit(cell[4], (*group_path, local, 1, index, 4), cell_context)
                        column += cell[3]
                    row_index += 1
            return
        if kind in {"RawInline", "RawBlock"}:
            return  # Exact raw roles remain in the existing independent adapter.
        for key, child in value.items():
            visit(child, (*path, key), context)

    visit(document["blocks"], ("blocks",), "body")
    return rows


def ordered_office_block_correspondence(
    source_ast: bytes,
    filtered_ast: bytes,
    native_ast: bytes,
    *,
    text: Callable[[Any], str],
) -> dict[str, Any]:
    """Compare every containing block at its actual ordered structural slot.

    Exact Source byte-to-filtered-role identity is supplied separately by the
    genuine own-format ordinal filter parse. Native
    extra/missing/reordered/different blocks are findings, not a location grant.
    Existing source and native scientific/style/layout checks remain mandatory.
    """
    source, filtered, native = (_blocks(ast, text) for ast in (source_ast, filtered_ast, native_ast))
    findings = []
    blockers: list[str] = []
    witnesses = []
    if len(filtered) != len(native):
        findings.append(
            {"code": "office.source.ordered_block_count", "expected": len(filtered), "observed": len(native)}
        )
    for expected, observed in zip(filtered, native):
        fields = ("kind", "heading_level", "text")
        same_cell = (
            not expected["context"].startswith("table:")
            and not observed["context"].startswith("table:")
            or expected["context"] == observed["context"]
        )
        # Office readback exposes visible captions as actual paragraphs.
        # The complete ordered slot/text and separate caption/style predicates
        # retain both actual contexts instead of relabeling either AST path.
        if not same_cell or any(expected[name] != observed[name] for name in fields):
            findings.append({"code": "office.source.ordered_block", "filtered": expected, "native": observed})
    if not findings:
        witnesses = [
            {"filtered": expected, "native": observed} for expected, observed in zip(filtered, native, strict=True)
        ]
    return {
        "source_ast_sha256": hashlib.sha256(source_ast).hexdigest(),
        "filtered_ast_sha256": hashlib.sha256(filtered_ast).hexdigest(),
        "native_ast_sha256": hashlib.sha256(native_ast).hexdigest(),
        "source_blocks": source,
        "filtered_blocks": filtered,
        "native_blocks": native,
        "witnesses": witnesses,
        "findings": findings,
        "blockers": blockers,
    }
