"""Independent table-cell accounting without granting native layout admission."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from infrastructure.reporting.native_office_source_coverage import scientific_source_occurrences


def _cell_text(value: Any) -> str:
    """Retain ordered literal text; scientific nested content is not flattened."""
    if isinstance(value, dict):
        kind = value.get("t")
        if kind == "Str":
            text = value.get("c")
            if not isinstance(text, str):
                raise ValueError("Office table literal text is malformed")
            return text
        if kind in {"Space", "SoftBreak", "LineBreak"}:
            return " "
        if kind in {"Math", "Cite", "Image", "RawBlock", "RawInline", "Note", "Table"}:
            raise ValueError(f"Office table nested {kind} needs its own native witness")
        return _cell_text(value.get("c", []))
    if isinstance(value, list):
        return "".join(_cell_text(child) for child in value)
    if value is None:
        return ""
    # Literal attributes are outside the cell-content traversal below.
    raise ValueError("Office table contains unsupported cell content")


def office_table_cells(ast: bytes) -> tuple[dict[str, Any], ...]:
    """Compile source/readback grids from actual Pandoc's declared table schema.

    No cell omission, row reordering or span normalization is permitted. Column
    geometry and nested scientific forms remain separate explicit requirements.
    """
    tables = []
    for occurrence in scientific_source_occurrences(ast):
        if occurrence.kind != "Table":
            continue
        value = json.loads(occurrence.content_json)
        if not isinstance(value, list) or len(value) != 6:
            raise ValueError("Office table requires the declared six-field Pandoc schema")
        _, caption, columns, head, bodies, foot = value
        if not isinstance(columns, list) or not columns:
            raise ValueError("Office table has no columns")
        if not isinstance(head, list) or len(head) != 2 or not isinstance(foot, list) or len(foot) != 2:
            raise ValueError("Office table head/foot schema is unsupported")
        groups = [("head", head[1])]
        if not isinstance(bodies, list):
            raise ValueError("Office table body schema is unsupported")
        for body in bodies:
            if not isinstance(body, list) or len(body) != 4 or type(body[1]) is not int:
                raise ValueError("Office table body row-header schema is unsupported")
            groups.extend((("body-head", body[2]), ("body", body[3])))
        groups.append(("foot", foot[1]))
        rows = []
        for group, group_rows in groups:
            if not isinstance(group_rows, list):
                raise ValueError("Office table rows are malformed")
            for row in group_rows:
                if not isinstance(row, list) or len(row) != 2 or not isinstance(row[1], list):
                    raise ValueError("Office table row schema is unsupported")
                cells = []
                for cell in row[1]:
                    if not isinstance(cell, list) or len(cell) != 5:
                        raise ValueError("Office table cell schema is unsupported")
                    if any(type(span) is not int or span < 1 for span in cell[2:4]):
                        raise ValueError("Office table cell spans are invalid")
                    blocks = cell[4]
                    if not isinstance(blocks, list):
                        raise ValueError("Office table cell blocks are malformed")
                    text = []
                    for block in blocks:
                        if not isinstance(block, dict) or block.get("t") not in {"Plain", "Para"}:
                            raise ValueError("Office table cell requires independently supported paragraphs")
                        text.append(_cell_text(block.get("c", [])))
                    cells.append({"row_span": cell[2], "column_span": cell[3], "paragraphs": text})
                rows.append({"group": group, "cells": cells})
        tables.append(
            {"source_occurrence": occurrence.ordinal, "columns": len(columns), "caption": caption, "rows": rows}
        )
    return tuple(tables)


def inspect_office_table_readback(source_ast: bytes, native_ast: bytes) -> dict[str, Any]:
    """Prove bounded plain-cell package survival; native geometry stays blocked."""
    blockers = []
    try:
        source = office_table_cells(source_ast)
        native = office_table_cells(native_ast)
    except ValueError as error:
        return {"status": "blocked", "findings": [], "blockers": [str(error)]}
    findings = []
    if len(source) != len(native):
        findings.append({"code": "office.table.count", "expected": len(source), "observed": len(native)})
    for ordinal, (expected, observed) in enumerate(zip(source, native)):
        for field in ("columns", "caption", "rows"):
            if expected[field] != observed[field]:
                findings.append({"code": f"office.table.{field}", "table": ordinal})
        blockers.append(
            f"Table source occurrence {expected['source_occurrence']} requires independent native cell geometry/ink"
        )
    return {
        "schema_version": "template-native-office-table-readback-v1",
        "source_ast_sha256": hashlib.sha256(source_ast).hexdigest(),
        "native_ast_sha256": hashlib.sha256(native_ast).hexdigest(),
        "status": "failed" if findings else "blocked" if blockers else "observed",
        "findings": findings,
        "blockers": blockers,
        "source_tables": source,
        "native_tables": native,
    }
