"""Independent source-cell and source-note browser layout reconstruction."""

from __future__ import annotations

import math
from typing import Any

from infrastructure.reporting.native_format_content_contracts import SemanticContentContract, text_tokens


from infrastructure.reporting.native_format_html_table_witness import TABLE_ATTRIBUTE_SCRIPT

STRUCTURE_SCRIPT = r"""
 const finiteBox=e=>(b=>[b.x,b.y,b.width,b.height])(e.getBoundingClientRect());
 const noteOwner=p=>p.closest('section.footnotes li[id],.footnotes li[id],li[role="doc-endnote"][id]');
 const textIndices=e=>rows.flatMap((r,i)=>e.contains(textNodes[i])?[i]:[]);
 const elementState=e=>{const ancestors=[];for(let a=e;a;a=a.parentElement)ancestors.push(a);
  const b=e.getBoundingClientRect();return {box:finiteBox(e),
   hidden:ancestors.some(a=>{const s=getComputedStyle(a);
    return s.display==='none'||s.visibility!=='visible'||parseFloat(s.opacity)===0}),
   clipped:ancestors.some(a=>{const s=getComputedStyle(a),c=a.getBoundingClientRect();
    return ['hidden','clip'].includes(s.overflow)&&
    (b.x<c.x-2||b.y<c.y-2||b.right>c.right+2||b.bottom>c.bottom+2)})};};
 const tables=[...document.querySelectorAll('table')].map(t=>({...elementState(t),
  rows:[...t.rows].map(r=>({section:r.parentElement.tagName.toLowerCase(),box:finiteBox(r),
   cells:[...r.cells].map(c=>({...elementState(c),header:c.tagName==='TH',
    row_span:c.rowSpan,col_span:c.colSpan,text_indices:textIndices(c)}))}))}));
 const footnotes=[...document.querySelectorAll('section.footnotes li[id],.footnotes li[id],li[role="doc-endnote"][id]')]
  .map(n=>({...elementState(n),id:n.id,text_indices:textIndices(n),
   backlinks:[...n.querySelectorAll('a.footnote-back,a[role="doc-backlink"]')].map(a=>a.getAttribute('href'))}));
 const footnote_refs=[...document.querySelectorAll('a.footnote-ref,a[role="doc-noteref"]')]
  .map(a=>({...elementState(a),id:a.id,target:a.getAttribute('href'),font_px:parseFloat(getComputedStyle(a).fontSize)}));
"""

STRUCTURE_SCRIPT += TABLE_ATTRIBUTE_SCRIPT


def _match_blocks(rows: list[dict[str, Any]], indices: list[int], blocks: list[dict[str, Any]]) -> set[int] | None:
    tokens: list[str]
    owners: list[int]
    tokens, owners = [], []
    for index in indices:
        current = text_tokens(rows[index]["text"])
        tokens.extend(current)
        owners.extend([index] * len(current))
    cursor = 0
    matched: set[int] = set()
    for block in blocks:
        required = tuple(block["tokens"])
        if not required:
            continue
        position = next(
            (
                i
                for i in range(cursor, len(tokens) - len(required) + 1)
                if tuple(tokens[i : i + len(required)]) == required
            ),
            None,
        )
        if position is None:
            return None
        matched.update(owners[position : position + len(required)])
        cursor = position + len(required)
    return matched


def _box_findings(element: dict[str, Any], dom: dict[str, Any], code: str, source_id: str) -> list[dict[str, Any]]:
    box = element.get("box")
    if (
        not isinstance(box, list)
        or len(box) != 4
        or not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in box)
    ):
        raise ValueError("scientific browser structure omitted finite actual geometry")
    x, y, width, height = box
    findings = []
    if min(width, height) <= 0 or element.get("hidden") or element.get("clipped"):
        findings.append({"code": f"html.{code}.visibility", "source_id": source_id})
    if x < -2 or y < 0 or x + width > dom["width"] + 2 or y + height > dom["height"] + 2:
        findings.append({"code": f"html.{code}.crop", "source_id": source_id})
    return findings


def inspect_browser_structure(dom: dict[str, Any], contract: SemanticContentContract) -> dict[str, Any]:
    """Bind every table cell and footer occurrence to actual DOM text and boxes."""
    rows = dom["text"]
    findings: list[dict[str, Any]] = []
    required: set[int] = set()
    tables, notes = dom.get("tables"), dom.get("footnotes")
    if not isinstance(tables, list) or not isinstance(notes, list):
        raise ValueError("browser omitted scientific table/note structure census")
    if len(tables) != len(contract.table_sources):
        findings.append({"code": "html.table.source"})
    table_observations = []
    blockers = []
    from infrastructure.reporting.native_format_html_table_witness import (
        inspect_table_attributes,
        inspect_table_alignment,
        inspect_table_columns,
    )

    block_map = {block.id: block for block in contract.blocks}
    block_map.update({block["id"]: block for note in contract.footnote_sources for block in note["blocks"]})
    for source, actual in zip(contract.table_sources, tables):
        identity = source["source_id"]
        findings.extend(_box_findings(actual, dom, "table", identity))
        attribute_observation = inspect_table_attributes(source["attributes"], actual, identity)
        column_observation = inspect_table_columns(source, actual)
        for witness in (attribute_observation, column_observation):
            findings.extend(witness["findings"])
            blockers.extend(witness["blockers"])
        for section in source["section_attributes"]:
            attrs = section["attributes"]
            if attrs["id"] or attrs["classes"] or attrs["key_values"]:
                blockers.append(f"{identity}: table section attributes require occurrence-specific native witness")
        caption = actual.get("caption")
        if source["caption_block_ids"]:
            if not isinstance(caption, dict):
                findings.append({"code": "html.table.caption", "source_id": identity})
            else:
                findings.extend(_box_findings(caption, dom, "table", identity))
                blocks = []
                for block_id in source["caption_block_ids"]:
                    item = block_map[block_id]
                    blocks.append(item if isinstance(item, dict) else {"tokens": list(item.tokens)})
                matched = _match_blocks(rows, caption["text_indices"], blocks)
                if matched is None:
                    findings.append({"code": "html.table.caption", "source_id": identity})
                else:
                    required.update(matched)
        if len(actual["rows"]) != len(source["rows"]):
            findings.append({"code": "html.table.rows", "source_id": identity})
        cell_observations = []
        occupied: dict[tuple[int, int], str] = {}
        for row_index, (source_row, actual_row) in enumerate(zip(source["rows"], actual["rows"])):
            section = {"head": "thead", "body-head": "tbody", "body": "tbody", "foot": "tfoot"}[source_row["section"]]
            if actual_row.get("section") != section or len(source_row["cells"]) != len(actual_row["cells"]):
                findings.append({"code": "html.table.cells", "source_id": identity, "row_index": row_index})
            row_witness = inspect_table_attributes(source_row["attributes"], actual_row, source_row["source_id"])
            findings.extend(row_witness["findings"])
            blockers.extend(row_witness["blockers"])
            column = 0
            previous_box = None
            for expected, cell in zip(source_row["cells"], actual_row["cells"]):
                cell_id = expected["source_id"]
                while (row_index, column) in occupied:
                    column += 1
                attribute_witness = inspect_table_attributes(expected["attributes"], cell, cell_id)
                alignment_witness = inspect_table_alignment(expected, cell, column, source["column_specs"])
                for witness in (attribute_witness, alignment_witness):
                    findings.extend(witness["findings"])
                    blockers.extend(witness["blockers"])
                if any(cell.get(key) != expected[key] for key in ("row_span", "col_span", "header")):
                    findings.append({"code": "html.table.span", "source_id": cell_id})
                if min(expected["row_span"], expected["col_span"]) < 1:
                    raise ValueError("source table spans must be positive")
                for y in range(row_index, row_index + expected["row_span"]):
                    for x in range(column, column + expected["col_span"]):
                        if (y, x) in occupied or x >= source["columns"] or y >= len(source["rows"]):
                            findings.append({"code": "html.table.grid", "source_id": cell_id})
                        occupied[(y, x)] = cell_id
                column += expected["col_span"]
                findings.extend(_box_findings(cell, dom, "table", cell_id))
                box = cell["box"]
                if previous_box and box[0] < previous_box[0] + previous_box[2] - 2:
                    findings.append({"code": "html.table.overlap", "source_id": cell_id})
                previous_box = box
                blocks = []
                for block_id in expected["block_ids"]:
                    item = block_map[block_id]
                    blocks.append(item if isinstance(item, dict) else {"tokens": list(item.tokens)})
                indices = cell["text_indices"]
                if not isinstance(indices, list) or any(
                    not isinstance(i, int) or i < 0 or i >= len(rows) for i in indices
                ):
                    raise ValueError("browser cell text indices escape actual census")
                matched = _match_blocks(rows, indices, blocks)
                if matched is None:
                    findings.append({"code": "html.table.content", "source_id": cell_id})
                else:
                    required.update(matched)
                cell_observations.append(
                    {
                        "source_id": cell_id,
                        "box_px": box,
                        "text_indices": indices,
                        "grid_column": column - expected["col_span"],
                        "attributes": attribute_witness,
                        "alignment": alignment_witness,
                    }
                )
        table_observations.append(
            {
                "source_id": identity,
                "cells": cell_observations,
                "attributes": attribute_observation,
                "columns": column_observation,
            }
        )
    refs = dom.get("footnote_refs", [])
    if len(notes) != len(contract.footnote_sources) or len(refs) != len(contract.footnote_sources):
        findings.append({"code": "html.footnote.source"})
    note_observations = []
    for source, note, reference in zip(contract.footnote_sources, notes, refs):
        identity = source["source_id"]
        findings.extend(_box_findings(note, dom, "footnote", identity))
        findings.extend(_box_findings(reference, dom, "footnote", identity))
        if reference.get("target") != f"#{note.get('id')}" or f"#{reference.get('id')}" not in note.get(
            "backlinks", []
        ):
            findings.append({"code": "html.footnote.target", "source_id": identity})
        indices = note["text_indices"]
        if not isinstance(indices, list) or any(not isinstance(i, int) or i < 0 or i >= len(rows) for i in indices):
            raise ValueError("browser note text indices escape actual census")
        matched = _match_blocks(rows, indices, source["blocks"])
        if matched is None:
            findings.append({"code": "html.footnote.content", "source_id": identity})
        else:
            required.update(matched)
        note_observations.append(
            {
                "source_id": identity,
                "ordinal": source["ordinal"],
                "note_id": note["id"],
                "reference_id": reference["id"],
                "text_indices": indices,
                "box_px": note["box"],
            }
        )
    return {
        "tables": table_observations,
        "footnotes": note_observations,
        "source_text_indices": sorted(required),
        "findings": findings,
        "blockers": blockers,
    }
