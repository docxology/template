"""A bounded predicate for the gold-to-manuscript analogy."""

from __future__ import annotations

from typing import Any


def analogy_boundary_theorem(profile: Any) -> bool:
    """Return whether a domain profile satisfies the local boundary theorem.

    The predicate is deliberately modest: it proves only that a profile has
    executable stage mappings, measurable dimensions, and explicit limits and
    non-claims. It does not prove domain truth or the universality of the
    analogy.
    """
    return bool(
        profile.stage_mappings
        and profile.metrics
        and profile.analogy_boundary_thesis.strip()
        and profile.analogy_boundary_limits
        and profile.analogy_boundary_non_claims
        and all(stage.evidence_surface.strip() for stage in profile.stage_mappings)
    )


def validate_analogy_boundary(profile: Any) -> dict[str, Any]:
    """Build a machine-readable boundary receipt, failing closed on omissions."""
    if not analogy_boundary_theorem(profile):
        raise ValueError(
            "analogy boundary requires stage mappings, metric dimensions, a thesis, limits, non-claims, and evidence surfaces"
        )
    return {
        "schema_version": 1,
        "status": "pass",
        "scope": "local source-owned analogy boundary",
        "stage_count": len(profile.stage_mappings),
        "metric_count": len(profile.metrics),
        "limits": list(profile.analogy_boundary_limits),
        "non_claims": list(profile.analogy_boundary_non_claims),
    }


__all__ = ["analogy_boundary_theorem", "validate_analogy_boundary"]
