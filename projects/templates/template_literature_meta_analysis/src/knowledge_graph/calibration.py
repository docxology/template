"""Offline calibration fixtures for knowledge-graph score direction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from knowledge_graph.hypothesis import score_hypothesis
from knowledge_graph.nanopublication import Assertion


def evaluate_calibration_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Score fixture cases and return a deterministic direction report."""
    rows: list[dict[str, Any]] = []
    issues: list[str] = []
    for case in cases:
        case_id = str(case.get("case_id", ""))
        expected = str(case.get("expected", ""))
        hypothesis_id = str(case.get("hypothesis_id", "PRIMARY_EFFICACY"))
        assertions: list[Assertion] = []
        for index, raw in enumerate(case.get("assertions", [])):
            if not isinstance(raw, dict):
                issues.append(f"{case_id}: assertion {index} is not a mapping")
                continue
            assertions.append(
                Assertion(
                    assertion_id=f"{case_id}-{index}",
                    paper_id=f"fixture:{case_id}-{index}",
                    claim="calibration fixture",
                    assertion_type=str(raw.get("assertion_type", "")),
                    hypothesis_id=hypothesis_id,
                    confidence=float(raw.get("confidence", 0.0)),
                    citation_count=int(raw.get("citation_count", 0)),
                )
            )
        score = score_hypothesis(assertions, hypothesis_id)
        actual = "positive" if score > 1e-12 else "negative" if score < -1e-12 else "zero"
        if expected not in {"positive", "negative", "zero"}:
            issues.append(f"{case_id}: invalid expected direction")
        elif actual != expected:
            issues.append(f"{case_id}: expected {expected}, observed {actual}")
        rows.append({"case_id": case_id, "expected": expected, "actual": actual, "score": round(score, 12)})
    return {
        "schema_version": "template-literature-kg-calibration-v1",
        "case_count": len(cases),
        "status": "pass" if not issues and cases else "fail",
        "issues": issues,
        "cases": rows,
    }


def validate_calibration_fixture(path: Path) -> dict[str, Any]:
    """Load and evaluate a JSON calibration fixture without network or LLM use."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != "template-literature-kg-calibration-fixture-v1"
    ):
        return {
            "schema_version": "template-literature-kg-calibration-v1",
            "status": "fail",
            "issues": ["bad fixture schema"],
        }
    cases = payload.get("cases")
    if not isinstance(cases, list):
        return {
            "schema_version": "template-literature-kg-calibration-v1",
            "status": "fail",
            "issues": ["cases must be a list"],
        }
    return evaluate_calibration_cases([case for case in cases if isinstance(case, dict)])


__all__ = ["evaluate_calibration_cases", "validate_calibration_fixture"]
