"""Preserve complete whole-PDF diagnostic DATA without granting native authority.

The producer calls this after actual observations. The current reader calls it
only after genuine original admission and fresh complete Source replay. Every
residual occurrence and full structured unsupported row is retained in order.
"""

from __future__ import annotations

import json
from typing import Any


def _reason(value: object) -> str:
    if isinstance(value, str) and value:
        return value
    if isinstance(value, dict) and value:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    raise ValueError("whole PDF diagnostics require complete nonempty original reasons")


def whole_pdf_diagnostics(
    observation: dict[str, Any], *, control_suite: bool
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Project every validated residual/finding; these DATA never create an owner."""
    label = "Whole PDF controls" if control_suite else "Whole PDF cohort"
    remaining, rows = observation.get("remaining"), observation.get("artifacts")
    if not isinstance(remaining, list) or not isinstance(rows, list) or not rows:
        raise ValueError("whole PDF diagnostics lack their complete residual/artifact roster")
    blockers: list[dict[str, str]] = []
    findings: list[dict[str, str]] = []
    for reason in remaining:
        if not isinstance(reason, str) or not reason:
            raise ValueError("whole PDF residual is missing its complete Source reason")
        blockers.append({"tool": label, "reason": reason})
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"] or row["id"] in seen:
            raise ValueError("whole PDF diagnostic artifact identities are absent or duplicate")
        seen.add(row["id"])
        tool = label + " " + row["id"]
        reasons = row.get("unsupported" if control_suite else "blockers")
        if not isinstance(reasons, list):
            raise ValueError("whole PDF diagnostic artifact omits its original residual list")
        for reason in reasons:
            if (
                control_suite
                and isinstance(reason, dict)
                and (not isinstance(reason.get("unsupported"), str) or not reason["unsupported"])
            ):
                raise ValueError("whole PDF unsupported control lost its complete Source reason")
            blockers.append({"tool": tool, "reason": _reason(reason)})
        if not control_suite:
            actual_findings = row.get("findings")
            if not isinstance(actual_findings, list):
                raise ValueError("whole PDF cohort omitted its actual native findings")
            for finding in actual_findings:
                diagnostic = {"tool": tool, "reason": _reason(finding)}
                blockers.append(diagnostic)
                findings.append(diagnostic)
    if control_suite:
        if observation.get("status") not in (None, "blocked"):
            raise ValueError("whole PDF controls changed their unresolved current status")
    elif observation.get("status") != ("fail" if findings else "blocked"):
        raise ValueError("whole PDF cohort status conceals actual native findings")
    if not blockers:
        raise ValueError("whole PDF engineering observation omitted its required remaining obligations")
    return blockers, findings
