"""Reusable rubric scoring for template benchmark checks."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class RubricDimension:
    """One weighted benchmark dimension."""

    name: str
    weight: float = 1.0


@dataclass(frozen=True)
class RubricSet:
    """A named set of weighted benchmark dimensions."""

    name: str
    dimensions: tuple[RubricDimension, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RubricSet":
        """Parse a rubric mapping from a benchmark manifest."""
        dimensions: list[RubricDimension] = []
        seen_names: set[str] = set()
        for row in payload.get("dimensions", ()):
            if not isinstance(row, Mapping):
                raise ValueError("rubric dimensions must be mappings")
            name = str(row.get("name", "") or "")
            if not name:
                raise ValueError("rubric dimension names must not be empty")
            if name in seen_names:
                raise ValueError(f"duplicate rubric dimension: {name}")
            seen_names.add(name)
            try:
                weight = float(row.get("weight", 1.0))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"rubric weight for {name!r} must be numeric") from exc
            if not math.isfinite(weight) or weight <= 0:
                raise ValueError(f"rubric weight for {name!r} must be finite and greater than zero")
            dimensions.append(RubricDimension(name=name, weight=weight))
        return cls(
            name=str(payload.get("name", "benchmark-rubric") or "benchmark-rubric"),
            dimensions=tuple(dimensions),
        )


@dataclass(frozen=True)
class RubricScore:
    """Weighted score result for a rubric."""

    score: float
    max_score: float
    passed_dimensions: tuple[str, ...] = field(default_factory=tuple)
    failed_dimensions: tuple[str, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        """Return true when every rubric dimension passed."""
        return not self.failed_dimensions


def score_rubric(results: Mapping[str, bool], rubric: RubricSet) -> RubricScore:
    """Score boolean check results against a weighted rubric."""
    score = 0.0
    max_score = 0.0
    passed: list[str] = []
    failed: list[str] = []
    for dimension in rubric.dimensions:
        max_score += dimension.weight
        if results.get(dimension.name, False):
            score += dimension.weight
            passed.append(dimension.name)
        else:
            failed.append(dimension.name)
    return RubricScore(
        score=score,
        max_score=max_score,
        passed_dimensions=tuple(passed),
        failed_dimensions=tuple(failed),
    )
