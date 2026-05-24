"""Public grader API."""

from __future__ import annotations

from skill_eval.grader.rules import check_negative_expectation, check_positive_expectation


def grade_output(text: str, expectations: list[str], *, negative: bool = False) -> dict:
    lower = text.lower()
    results = []
    for exp in expectations:
        if negative:
            passed = check_negative_expectation(lower, exp.lower())
        else:
            passed = check_positive_expectation(lower, exp.lower(), exp)
        results.append(
            {
                "text": exp,
                "passed": passed,
                "evidence": _evidence(exp, passed),
            }
        )
    passed_n = sum(1 for r in results if r["passed"])
    return {
        "expectations": results,
        "summary": {
            "passed": passed_n,
            "failed": len(results) - passed_n,
            "total": len(results),
            "pass_rate": passed_n / len(results) if results else 0.0,
        },
    }


def _evidence(exp: str, passed: bool) -> str:
    if passed:
        return f"Matched heuristic for: {exp[:60]}"
    return f"No match for: {exp[:60]}"
