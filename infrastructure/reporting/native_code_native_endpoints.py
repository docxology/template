"""Selected Code endpoints in existing complete own-format native witnesses.

No number/text search chooses a native location. Actual ordinal AST sites
select complete containing roles; every selected descendant must have an
existing native witness. Enclosing Source, controls/style/science/library
qualification remains mandatory before any baseline residual is reconciled.
"""

from __future__ import annotations

import hashlib
from typing import Any

from infrastructure.reporting.native_format_pdf_semantic_plan import strict_ast


def _path(path: tuple[str | int, ...]) -> str:
    return "/".join(map(str, path))


def selected_ast_roles(ast: bytes, mapping: dict[str, Any]) -> list[dict[str, Any]]:
    """Retain exact whole roles intersecting actual ordered AST boundaries."""
    document = strict_ast(ast)
    sites = (mapping["start"], mapping["end"])
    positions: dict[int, int] = {}
    roles = []
    cursor = 0
    visited = 0

    def boundary(path: tuple[str | int, ...], offset: int, value: Any) -> None:
        for index, site in enumerate(sites):
            if tuple(site["ast_path"]) == path and site["offset"] == offset:
                if index in positions:
                    raise ValueError("selected AST endpoint repeated a boundary")
                if site["kind"] not in {"literal-codepoint", "ordered-list-boundary", "containing-table-boundary"}:
                    raise ValueError("selected AST endpoint has an unsupported boundary kind")
                if site["kind"] == "literal-codepoint" and not isinstance(value, str):
                    raise ValueError("selected literal endpoint is not an actual AST string")
                if site["kind"] != "literal-codepoint" and not isinstance(value, list):
                    raise ValueError("selected ordered endpoint is not an actual AST list")
                positions[index] = cursor

    def walk(value: Any, path: tuple[str | int, ...]) -> None:
        nonlocal cursor, visited
        visited += 1
        if visited > 100000 or len(path) > 100:
            raise ValueError("selected endpoint exceeded its complete AST traversal budget")
        start = cursor
        cursor += 1
        if isinstance(value, list):
            boundary(path, 0, value)
            for index, child in enumerate(value):
                walk(child, (*path, index))
                boundary(path, index + 1, value)
        elif isinstance(value, dict):
            for key, child in value.items():
                walk(child, (*path, key))
            kind = value.get("t")
            if kind in {
                "Str",
                "Space",
                "SoftBreak",
                "LineBreak",
                "Math",
                "Code",
                "CodeBlock",
                "Table",
                "RawInline",
                "RawBlock",
            }:
                roles.append({"ast_path": list(path), "kind": kind, "first": start, "last": cursor, "node": value})
        elif isinstance(value, str):
            for index, site in enumerate(sites):
                if tuple(site["ast_path"]) == path:
                    if site["kind"] != "literal-codepoint":
                        raise ValueError("selected AST string endpoint has no literal boundary kind")
                    offset = site["offset"]
                    if type(offset) is not int or not 0 <= offset <= len(value):
                        raise ValueError("selected AST literal offset escaped its complete actual string")
                    positions[index] = cursor + offset
            cursor += len(value)
        cursor += 1

    walk(document["blocks"], ("blocks",))
    if set(positions) != {0, 1} or positions[0] >= positions[1]:
        raise ValueError("selected AST occurrence lacks two genuine forward boundaries")
    selected = [row for row in roles if row["first"] < positions[1] and row["last"] > positions[0]]
    selected.sort(key=lambda row: row["first"])
    if not selected:
        raise ValueError("selected Source value has no supported containing AST role")
    if mapping.get("boundary_kind") == "containing-table":
        path = mapping["container_ast_path"]
        tables = [row for row in selected if row["kind"] == "Table" and row["ast_path"] == path]
        if len(tables) != 1 or any(row["ast_path"][: len(path)] != path for row in selected):
            raise ValueError("selected containing-Table carrier differs from its complete actual AST")
    return [{key: row[key] for key in ("ast_path", "kind")} for row in selected]


def pdf_native_endpoints(ast: bytes, mapping: dict[str, Any], predicates: dict[str, Any]) -> dict[str, Any]:
    """Join actual AST members to complete text/cell/Math/caption witnesses."""
    plan, witness = predicates["source_plan"], predicates["witness"]
    if plan["source_ast_sha256"] != hashlib.sha256(ast).hexdigest() or predicates["findings"] or witness["findings"]:
        raise ValueError("selected PDF endpoints changed their qualified own Source AST/native witness")
    result = []
    residuals = []
    literal = {row["block_id"]: row for row in witness["literal"]["matches"]}
    words = {row["word_index"]: row for row in witness["literal"]["supported_words"]}
    equations = {row["identity"]: row for row in (witness.get("equations") or {}).get("observations", [])}
    tables = {row["identity"]: row for row in plan["tables"]}
    for role in selected_ast_roles(ast, mapping):
        identity, kind = _path(tuple(role["ast_path"])), role["kind"]
        endpoints = []
        if kind in {"Code", "CodeBlock"}:
            for row in witness["literal_roles"]["observations"]:
                if row["identity"] == identity and row["kind"] == kind:
                    endpoints.append({"role": "complete-PDF-exact-literal-role", "observation": row})
        elif kind in {"Str", "Space", "SoftBreak", "LineBreak"}:
            for member in plan["literal_members"]:
                if identity not in member["ast_paths"] or member["context"] == "footnote":
                    continue
                actual = literal.get(member["block_id"])
                if (
                    actual is not None
                    and actual["word_indices"]
                    and all(index in words for index in actual["word_indices"])
                ):
                    endpoints.append(
                        {
                            "role": "complete-PDF-containing-text-block",
                            "block_id": member["block_id"],
                            "match": actual,
                            "words": [words[index] for index in actual["word_indices"]],
                        }
                    )
        elif kind == "Math" and identity in equations:
            endpoints.append({"role": "complete-PDF-Math", "observation": equations[identity]})
        elif kind == "Table" and identity in tables:
            table = tables[identity]
            observed = [row for row in witness["tables"]["rows"] if row["table_identity"] == identity]
            expected_cells = [cell["identity"] for row in table["rows"] for cell in row["cells"]]
            observed_cells = [cell["identity"] for row in observed for cell in row["cells"]]
            if expected_cells == observed_cells and expected_cells:
                endpoints.append({"role": "complete-PDF-Table", "rows": observed})
        if endpoints:
            result.append({**role, "endpoints": endpoints})
        else:
            residuals.append("selected-PDF-native-containing-role:" + identity + ":" + kind)
    return {"roles": result, "residuals": residuals}


def office_native_endpoints(ast: bytes, mapping: dict[str, Any], survival: dict[str, Any]) -> dict[str, Any]:
    """Own filtered AST paths map through whole ordered package roles."""
    if survival["filtered_ast_sha256"] != hashlib.sha256(ast).hexdigest() or survival["findings"]:
        raise ValueError("selected Office endpoints changed its genuine own filtered AST/native predicate")
    ordered = survival["ordered_blocks"]
    if ordered["findings"] or ordered["blockers"]:
        return {"roles": [], "residuals": ["selected-Office-complete-ordered-native-block-correspondence"]}
    math_map = {tuple(row["filtered_ast_path"]): row for row in survival["filtered_math_to_source"]}
    native_math = {row["ordinal"]: row for row in survival["native_math_locations"]}
    tables = list(zip(survival["filtered_table_locations"], survival["native_table_locations"]))
    result, residuals = [], []
    for role in selected_ast_roles(ast, mapping):
        path, kind = role["ast_path"], role["kind"]
        endpoints = []
        if kind in {"Str", "Space", "SoftBreak", "LineBreak", "Code", "CodeBlock"}:
            for row in ordered["witnesses"]:
                containing = row["filtered"]["ast_path"]
                if path[: len(containing)] == containing:
                    endpoints.append({"role": "complete-Office-containing-block", **row})
        elif kind == "Math":
            original = math_map.get(tuple(path))
            if original is not None:
                for row in survival["witnesses"]:
                    if row["source_occurrence"] != original["source_occurrence"]:
                        continue
                    if row["kind"] == "ImageCaptionMath":
                        matches = [
                            visible
                            for visible in survival["witnesses"]
                            if visible["kind"] == "Math"
                            and visible["source_occurrence"] == row["visible_source_occurrence"]
                        ]
                    else:
                        matches = [row] if row["kind"] == "Math" else []
                    for match in matches:
                        native = native_math.get(match["native_occurrence"])
                        if native is not None:
                            endpoints.append(
                                {"role": "complete-Office-Math", "source": original, "witness": match, "native": native}
                            )
        elif kind == "Table" and len(survival["filtered_table_locations"]) == len(survival["native_table_locations"]):
            for expected, observed in tables:
                if expected["ast_path"] == path:
                    endpoints.append({"role": "complete-Office-Table", "filtered": expected, "native": observed})
        if endpoints:
            result.append({**role, "endpoints": endpoints})
        else:
            residuals.append("selected-Office-native-containing-role:" + _path(tuple(path)) + ":" + kind)
    return {"roles": result, "residuals": residuals}
