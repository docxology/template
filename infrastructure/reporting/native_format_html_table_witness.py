"""Complete table attribute custody and finite alignment/caption witnesses."""

from __future__ import annotations

import math
from typing import Any

TABLE_ATTRIBUTE_SCRIPT = r"""
 const tableAttrs=e=>({id:e.id,classes:[...e.classList],
  attributes:Object.fromEntries([...e.attributes].map(a=>[a.name,a.value]))});
 const tablePresentation=e=>{const s=getComputedStyle(e);return {text_align:s.textAlign,direction:s.direction,
  transform:s.transform,filter:s.filter,writing_mode:s.writingMode};};
 for(const [ti,t] of [...document.querySelectorAll('table')].entries()){
  Object.assign(tables[ti],tableAttrs(t),{presentation:tablePresentation(t),
   caption:t.caption?{...elementState(t.caption),text_indices:textIndices(t.caption),...tableAttrs(t.caption)}:null,
   colgroup:[...t.querySelectorAll(':scope > colgroup > col')].map(c=>
   ({...tableAttrs(c),style_width:c.style.width,box:finiteBox(c)}))});
  for(const [ri,r] of [...t.rows].entries()){
   Object.assign(tables[ti].rows[ri],tableAttrs(r));
   for(const [ci,c] of [...r.cells].entries())Object.assign(tables[ti].rows[ri].cells[ci],tableAttrs(c),
   {presentation:tablePresentation(c)});
  }
 }
"""


def source_attributes(attr: Any) -> dict[str, Any]:
    """Preserve every source attribute; never drop unsupported styling/events."""
    if (
        not isinstance(attr, list)
        or len(attr) != 3
        or not isinstance(attr[0], str)
        or not isinstance(attr[1], list)
        or not isinstance(attr[2], list)
    ):
        raise ValueError("native table source requires a complete Pandoc attribute tuple")
    if any(not isinstance(item, str) for item in attr[1]) or any(
        not isinstance(item, list) or len(item) != 2 or any(not isinstance(value, str) for value in item)
        for item in attr[2]
    ):
        raise ValueError("malformed source table attribute occurrence")
    return {"id": attr[0], "classes": list(attr[1]), "key_values": [list(item) for item in attr[2]]}


def inspect_table_attributes(source: dict[str, Any], actual: dict[str, Any], identity: str) -> dict[str, Any]:
    """Compare source attrs to actual DOM attrs; unknown semantics stay blocked."""
    findings: list[dict[str, Any]] = []
    blockers = []
    if not isinstance(actual.get("attributes"), dict) or not isinstance(actual.get("classes"), list):
        raise ValueError("native table omitted actual attribute census")
    if source["id"] and actual.get("id") != source["id"]:
        findings.append({"code": "html.table.attribute", "source_id": identity, "attribute": "id"})
    if any(item not in actual["classes"] for item in source["classes"]):
        findings.append({"code": "html.table.attribute", "source_id": identity, "attribute": "class"})
    # CSS class semantics are witnessed by computed geometry/alignment and
    # localized ink below, but arbitrary style/event/ARIA meaning is separate.
    seen = set()
    for key, value in source["key_values"]:
        if key in seen:
            blockers.append(f"{identity}: duplicate table attribute {key} requires occurrence-specific witness")
        seen.add(key)
        if actual["attributes"].get(key) != value:
            findings.append({"code": "html.table.attribute", "source_id": identity, "attribute": key})
        if key not in {"title", "role"} and not key.startswith("data-"):
            blockers.append(f"{identity}: table attribute {key} requires specific native semantic proof")
        if key == "role" and value != "table":
            blockers.append(f"{identity}: table role {value} requires specific native semantic proof")
    return {
        "source_id": identity,
        "source": source,
        "actual_id": actual.get("id"),
        "actual_classes": actual["classes"],
        "findings": findings,
        "blockers": blockers,
    }


def inspect_table_alignment(
    source: dict[str, Any], actual: dict[str, Any], column: int, column_specs: list[dict[str, Any]]
) -> dict[str, Any]:
    """Require explicit column/cell alignment in real computed native styles."""
    identity = source["source_id"]
    findings: list[dict[str, Any]] = []
    blockers = []
    presentation = actual.get("presentation")
    if not isinstance(presentation, dict):
        raise ValueError("native source table cell omitted computed presentation")
    align = source["alignment"]
    if align == "AlignDefault" and column < len(column_specs):
        align = column_specs[column]["alignment"]
    expected = {"AlignLeft": "left", "AlignCenter": "center", "AlignRight": "right", "AlignDefault": None}.get(align)
    if align not in {"AlignLeft", "AlignCenter", "AlignRight", "AlignDefault"}:
        blockers.append(f"{identity}: unknown table alignment {align} requires source witness")
    elif expected is not None and presentation.get("text_align") != expected:
        findings.append({"code": "html.table.alignment", "source_id": identity})
    if any(
        presentation.get(key) != value
        for key, value in (
            ("direction", "ltr"),
            ("transform", "none"),
            ("filter", "none"),
            ("writing_mode", "horizontal-tb"),
        )
    ):
        blockers.append(f"{identity}: transformed/directional table placement requires specific source witness")
    return {
        "source_id": identity,
        "grid_column": column,
        "source_alignment": align,
        "computed_alignment": presentation.get("text_align"),
        "findings": findings,
        "blockers": blockers,
    }


def inspect_table_columns(source: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    """Retain widths and require writer declarations plus native column geometry."""
    findings: list[dict[str, Any]] = []
    blockers = []
    columns = actual.get("colgroup")
    if not isinstance(columns, list):
        raise ValueError("native table omitted full column presentation census")
    widths = source["column_specs"]
    declared = [item["width"] for item in widths]
    if any(width is not None for width in declared):
        if len(columns) != len(widths):
            findings.append({"code": "html.table.columns", "source_id": source["source_id"]})
        for expected, column in zip(widths, columns):
            if expected["width"] is None:
                continue
            style = column.get("style_width", "")
            try:
                fraction = float(style.removesuffix("%")) / 100 if style.endswith("%") else float("nan")
            except (ValueError, AttributeError):
                fraction = float("nan")
            # Pandoc rounds column percentages to an integer percentage.
            if not math.isfinite(fraction) or abs(fraction - expected["width"]) > 0.005001:
                findings.append({"code": "html.table.column-width", "source_id": source["source_id"]})
        # CSS min-content, spans and border layout can override the writer's
        # width. A declaration alone never grants source geometry approval.
        blockers.append(f"{source['source_id']}: explicit column widths require calibrated native allocation proof")
    return {
        "source_id": source["source_id"],
        "source_column_specs": widths,
        "native_columns": columns,
        "findings": findings,
        "blockers": blockers,
    }
