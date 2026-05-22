"""Reusable rubric scoring for template benchmark checks."""

from __future__ import annotations

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
        for row in payload.get("dimensions", ()):
            if not isinstance(row, Mapping):
                raise ValueError("rubric dimensions must be mappings")
            dimensions.append(
                RubricDimension(
                    name=str(row.get("name", "") or ""),
                    weight=float(row.get("weight", 1.0) or 0.0),
                )
            )
        if any(not dimension.name for dimension in dimensions):
            raise ValueError("rubric dimension names must not be empty")
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
