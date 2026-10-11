"""Independent original-column allocation for a finite CSS fixed-table form."""

from __future__ import annotations

import math
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_html_source_metadata import remaining_seconds

ALLOCATION_SCHEMA = "template-native-html-original-column-allocation-v1"
ALLOCATION_SCRIPT = r"""
 const zeroTableEdges=e=>{const s=getComputedStyle(e);return {
  borders:[s.borderLeftWidth,s.borderRightWidth,s.borderTopWidth,s.borderBottomWidth].map(parseFloat),
  padding:[s.paddingLeft,s.paddingRight,s.paddingTop,s.paddingBottom].map(parseFloat),
  min_width:s.minWidth,max_width:s.maxWidth,box_sizing:s.boxSizing,display:s.display,
  transform:s.transform,writing_mode:s.writingMode,direction:s.direction};};
 for(const [ti,t] of [...document.querySelectorAll('table')].entries()){
  const s=getComputedStyle(t);
  tables[ti].allocation={...zeroTableEdges(t),table_layout:s.tableLayout,
   border_collapse:s.borderCollapse,border_spacing:s.borderSpacing,width:s.width};
  for(const [ri,r] of [...t.rows].entries())for(const [ci,c] of [...r.cells].entries())
   tables[ti].rows[ri].cells[ci].allocation=zeroTableEdges(c);
 }
"""


def _box(value: Any) -> tuple[float, float, float, float]:
    if (
        not isinstance(value, list)
        or len(value) != 4
        or any(type(v) not in {int, float} or not math.isfinite(v) for v in value)
    ):
        raise ValueError("table allocation requires complete finite native box geometry")
    return float(value[0]), float(value[1]), float(value[2]), float(value[3])


def compile_column_allocation(
    original: dict[str, Any], projected: dict[str, Any], *, deadline: float
) -> dict[str, Any]:
    """Preserve original AST fractions; permit no writer-selected replacement.

    Caller authenticates both ASTs through original-source parsing and survival
    replay. Only all-explicit, integral percentages summing exactly to 100 are
    modeled; unspecified, rounded, spanning and other layouts remain blocked.
    """
    remaining_seconds(deadline)
    identity = original["source_id"]
    specifications = original["column_specs"]
    blockers = []
    findings = []
    fractions = [row["width"] for row in specifications]
    if projected["column_specs"] != specifications:
        findings.append({"code": "html.table.original-column-specs", "source_id": identity})
    if (
        not fractions
        or len(fractions) > 128
        or any(type(v) not in {int, float} or not math.isfinite(v) or not 0 < v <= 1 for v in fractions)
    ):
        blockers.append(f"{identity}: mixed/default/unknown original column fractions need a separate allocation model")
    elif abs(sum(fractions) - 1) > 1e-12 or any(abs(v * 100 - round(v * 100)) > 1e-10 for v in fractions):
        blockers.append(
            f"{identity}: nonintegral percentage/remaining-space allocation requires exact writer and native model"
        )
    if any(cell["col_span"] != 1 or cell["row_span"] != 1 for row in original["rows"] for cell in row["cells"]):
        blockers.append(f"{identity}: original column/row spans require a separate fixed allocation model")
    result = {
        "schema_version": ALLOCATION_SCHEMA,
        "source_id": identity,
        "original_column_specs": specifications,
        "projected_column_specs": projected["column_specs"],
        "fractions": fractions,
        "findings": findings,
        "blockers": blockers,
    }
    result = {**result, "digest": canonical_digest(result)}
    remaining_seconds(deadline)
    return result


def _edges_supported(style: dict[str, Any], display: str) -> bool:
    return (
        style.get("borders") == [0, 0, 0, 0]
        and style.get("padding") == [0, 0, 0, 0]
        and style.get("transform") == "none"
        and style.get("writing_mode") == "horizontal-tb"
        and style.get("direction") == "ltr"
        and style.get("display") == display
        and style.get("min_width") == "0px"
        and style.get("max_width") == "none"
    )


def inspect_column_allocation(source: dict[str, Any], actual: dict[str, Any], *, deadline: float) -> dict[str, Any]:
    """Predict each column/cell boundary from original fractions and table extent.

    A matching style declaration or bbox contrast is never this proof. Native
    auto/intrinsic sizing, borders, padding, spanning or transforms remain
    unsupported even when aggregate ratios happen to match.
    """
    remaining_seconds(deadline)
    if source.get("schema_version") != ALLOCATION_SCHEMA or source.get("digest") != canonical_digest(
        {key: value for key, value in source.items() if key != "digest"}
    ):
        raise ValueError("original source column allocation contract changed")
    findings = list(source["findings"])
    blockers = list(source["blockers"])
    identity = source["source_id"]
    style = actual.get("allocation")
    if not isinstance(style, dict):
        raise ValueError("actual native table omitted fixed-layout presentation")
    if (
        not _edges_supported(style, "table")
        or style.get("table_layout") != "fixed"
        or style.get("border_collapse") != "separate"
        or style.get("border_spacing") not in {"0px", "0px 0px"}
    ):
        blockers.append(
            f"{identity}: native auto/intrinsic/border/padding table algorithm is outside the fixed zero-edge model"
        )
    columns = actual.get("colgroup")
    if not isinstance(columns, list):
        raise ValueError("native table omitted complete column geometry")
    expected = []
    if not blockers:
        x, _, width, _ = _box(actual["box"])
        if width <= 0 or len(columns) != len(source["fractions"]):
            findings.append({"code": "html.table.column-allocation-count", "source_id": identity})
        else:
            cursor = x
            for index, (fraction, column) in enumerate(zip(source["fractions"], columns, strict=True)):
                allocated = width * fraction
                left, _, measured, _ = _box(column["box"])
                # Browser layout quantization is the sole finite tolerance, not
                # an image error mean or adjustable percentage acceptance band.
                if abs(left - cursor) > 1 / 64 or abs(measured - allocated) > 1 / 64:
                    findings.append({"code": "html.table.column-allocation", "source_id": identity, "column": index})
                expected.append(
                    {"column": index, "left_px": cursor, "width_px": allocated, "source_fraction": fraction}
                )
                cursor += allocated
            for row_index, row in enumerate(actual["rows"]):
                remaining_seconds(deadline)
                if len(row["cells"]) != len(expected):
                    findings.append(
                        {"code": "html.table.cell-allocation-count", "source_id": identity, "row": row_index}
                    )
                    continue
                for index, cell in enumerate(row["cells"]):
                    cell_style = cell.get("allocation")
                    if (
                        not isinstance(cell_style, dict)
                        or not _edges_supported(cell_style, "table-cell")
                        or cell["col_span"] != 1
                        or cell["row_span"] != 1
                    ):
                        blockers.append(f"{identity}: native spanned/styled cell needs its own allocation model")
                        continue
                    left, _, measured, _ = _box(cell["box"])
                    if (
                        abs(left - expected[index]["left_px"]) > 1 / 64
                        or abs(measured - expected[index]["width_px"]) > 1 / 64
                    ):
                        findings.append(
                            {
                                "code": "html.table.cell-allocation",
                                "source_id": identity,
                                "row": row_index,
                                "column": index,
                            }
                        )
    remaining_seconds(deadline)
    return {
        "source_digest": source["digest"],
        "expected_columns": expected,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }


def replay_column_allocation(
    original: dict[str, Any], projected: dict[str, Any], actual: dict[str, Any], raw: dict[str, Any], *, deadline: float
) -> dict[str, Any]:
    """Derive reader expectations from independently reparsed original AST."""
    result = inspect_column_allocation(
        compile_column_allocation(original, projected, deadline=deadline), actual, deadline=deadline
    )
    if raw != result:
        raise ValueError("independent original AST column allocation replay differs")
    remaining_seconds(deadline)
    return result
