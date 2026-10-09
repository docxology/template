"""Plan genuine source/SVG controls without inventing their process receipts."""

from __future__ import annotations

from typing import Any

from infrastructure.reporting.native_mermaid_svg_controls import CONTROL_CODES


def original_mermaid_svg_control_plan(reference: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    """Require every original positive plus one meaningful negative per role.

    Root first admits the original source-only producer/paint/runtime record.
    Each returned invocation runs under the existing actual bootstrap child
    supervisor and original budgets. Plans are never acceptance receipts.
    """
    if reference.get("schema_version") != "template-native-mermaid-original-source-reference-v1":
        raise ValueError("original Mermaid control plan requires the genuine source reference schema")
    rows = reference.get("occurrences")
    if not isinstance(rows, list) or not 0 < len(rows) <= 100 or reference.get("blockers"):
        raise ValueError("original Mermaid control plan requires complete bounded source occurrences")
    families: dict[str, dict[str, Any]] = {}
    plan: list[dict[str, Any]] = []

    def append(row: dict[str, Any], control: str) -> None:
        plan.append(
            {
                "identity": row["identity"],
                "family": row["source_graph"]["family"],
                "control": control,
                "module": "infrastructure.reporting.native_mermaid_svg_controls",
                "source": row["source"],
                "svg": row["artifacts"]["svg"],
                "expected_original_exit_code": int(control != "baseline"),
                "required_code": CONTROL_CODES[control],
                "original_actual_child_receipt_required": True,
            }
        )

    for row in rows:
        if row["topology"]["status"] != "pass" or row["topology"]["findings"] or row["topology"]["blockers"]:
            raise ValueError("original Mermaid control plan has an unproved actual SVG baseline")
        append(row, "baseline")
        families.setdefault(row["source_graph"]["family"], row)
    for family, row in families.items():
        for control in ("changed-label", "moved-node", "removed-edge", "changed-endpoint"):
            append(row, control)
        if family != "erDiagram":
            append(row, "reversed-arrow")
        if family == "classDiagram":
            append(row, "changed-member")
            cardinal_rows = [
                candidate
                for candidate in rows
                if candidate["source_graph"]["family"] == family
                and any(edge.get("to_cardinality") == "*" for edge in candidate["source_graph"]["edges"])
            ]
            if cardinal_rows:
                append(cardinal_rows[0], "changed-class-cardinality")
        elif family == "sequenceDiagram":
            append(row, "changed-message-order")
        elif family == "stateDiagram-v2":
            append(row, "lost-state-start")
        elif family == "erDiagram":
            append(row, "changed-cardinality")
    return tuple(plan)
