"""Small deterministic adapter registry proving the loop is task-agnostic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ADAPTER_RESULT_SCHEMA = "template-autoresearch-adapter-result-v1"


@dataclass(frozen=True)
class AdapterResult:
    """Common evidence envelope emitted by offline task adapters."""

    adapter_id: str
    metric_name: str
    metric_direction: str
    baseline_metric: float
    selected_parameter: float
    selected_metric: float
    candidate_count: int
    budget: int
    offline: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": ADAPTER_RESULT_SCHEMA,
            "adapter_id": self.adapter_id,
            "metric": {
                "name": self.metric_name,
                "direction": self.metric_direction,
                "baseline": self.baseline_metric,
                "selected": self.selected_metric,
            },
            "selected_parameter": self.selected_parameter,
            "candidate_count": self.candidate_count,
            "budget": self.budget,
            "offline": self.offline,
            "claim_boundary": "Deterministic adapter behavior is a fixture contract, not an empirical result.",
        }


def run_quadratic_adapter(*, budget: int = 3) -> AdapterResult:
    """Run a tiny deterministic optimization task with a distinct task shape."""
    if budget <= 0:
        raise ValueError("budget must be positive")
    candidates = (-2.0, -1.0, 0.0, 1.0, 2.0)
    evaluated = candidates[:budget]

    def score(value: float) -> float:
        return -((value - 1.0) ** 2)

    selected = max(evaluated, key=score)
    return AdapterResult(
        adapter_id="quadratic_fixture",
        metric_name="negative_squared_error",
        metric_direction="maximize",
        baseline_metric=score(0.0),
        selected_parameter=selected,
        selected_metric=score(selected),
        candidate_count=len(evaluated),
        budget=budget,
    )


def available_adapters() -> tuple[str, ...]:
    """Return task adapters available without network or generated code."""
    return ("mnist", "quadratic_fixture")


__all__ = ["ADAPTER_RESULT_SCHEMA", "AdapterResult", "available_adapters", "run_quadratic_adapter"]
