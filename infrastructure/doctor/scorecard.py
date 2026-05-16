"""Scorecard — convert findings into a 0-100 numeric score per dimension.

Ten dimensions, each scored 0–100, weighted into an overall score. The
weighting is deliberately simple so the math is auditable: each
dimension contributes its weight × score, then the result is
normalised by the total weight. There are no "soft factors" — every
input is a finding code, every output is reproducible from the
findings list.

A dimension's score is computed by:

1. Picking the findings whose ``code`` belongs to that dimension.
2. Mapping ``severity`` to a deduction (INFO=0, WARN=15, ERROR=40,
   CRITICAL=70).
3. ``score = clamp(100 - sum(deductions), 0, 100)`` for that dimension.

Healthy (``healthy=True``) findings always score 100 regardless of
severity, so a CRITICAL "X is installed" doesn't both get fixed and
keep deducting.
"""

from collections.abc import Iterable

from infrastructure.doctor.models import Finding, Severity


__all__ = [
    "DIMENSIONS",
    "DIMENSION_WEIGHTS",
    "compute_scorecard",
    "dimension_for_code",
]


# Mapping from prefix (DOC1xx, DOC2xx, ...) to dimension name.
# Stable: codes are dimension-stable so the scorecard stays comparable
# across runs even when individual findings shift severity.
DIMENSIONS: dict[str, str] = {
    "DOC1": "environment",
    "DOC2": "project_layout",
    "DOC3": "hygiene",
    "DOC4": "tooling_state",
    "DOC5": "optional_services",
    "DOC6": "safety_surface",
}

# Weights — must cover every dimension in :data:`DIMENSIONS`. Optional
# services are deliberately under-weighted because they're info-only.
DIMENSION_WEIGHTS: dict[str, float] = {
    "environment": 2.0,
    "project_layout": 2.0,
    "hygiene": 1.0,
    "tooling_state": 1.5,
    "optional_services": 0.5,
    "safety_surface": 3.0,
}

_SEVERITY_DEDUCTION: dict[Severity, float] = {
    Severity.INFO: 0.0,
    Severity.WARN: 15.0,
    Severity.ERROR: 40.0,
    Severity.CRITICAL: 70.0,
}


def dimension_for_code(code: str) -> str:
    """Return the dimension name for a finding code.

    Codes look like ``"DOC101"`` or ``"DOC201[my_project]"``. The first
    four characters identify the dimension.
    """
    key = code[:4]
    return DIMENSIONS.get(key, "uncategorised")


def compute_scorecard(findings: Iterable[Finding]) -> tuple[float, dict[str, float]]:
    """Return ``(overall, per_dimension)`` 0–100 scores.

    Args:
        findings: Findings produced by detectors.

    Returns:
        Tuple of ``(overall_score, {dimension: score})``. Dimensions
        with no findings are scored 100 (nothing to penalise).
    """
    # Bucket findings by dimension.
    buckets: dict[str, list[Finding]] = {d: [] for d in DIMENSION_WEIGHTS}
    buckets["uncategorised"] = []
    for f in findings:
        buckets.setdefault(dimension_for_code(f.code), []).append(f)

    dim_scores: dict[str, float] = {}
    for dim, items in buckets.items():
        if not items:
            dim_scores[dim] = 100.0
            continue
        deduction = 0.0
        for f in items:
            if f.healthy:
                continue
            deduction += _SEVERITY_DEDUCTION.get(f.severity, 0.0)
        dim_scores[dim] = max(0.0, min(100.0, 100.0 - deduction))

    # Weighted overall — only dimensions known to ``DIMENSION_WEIGHTS``
    # contribute. ``uncategorised`` is reported but not weighted (so a
    # new detector with an out-of-range code does not silently move the
    # score before it's wired into a dimension).
    total_weight = sum(DIMENSION_WEIGHTS.values())
    weighted = 0.0
    for dim, weight in DIMENSION_WEIGHTS.items():
        weighted += weight * dim_scores.get(dim, 100.0)
    overall = weighted / total_weight if total_weight > 0 else 100.0

    # Stable order for the returned dict: weighted dimensions first, then
    # ``uncategorised`` if it has any entries.
    ordered: dict[str, float] = {dim: dim_scores[dim] for dim in DIMENSION_WEIGHTS}
    if buckets.get("uncategorised"):
        ordered["uncategorised"] = dim_scores["uncategorised"]
    return overall, ordered
