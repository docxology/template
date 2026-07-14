"""Optional project-local experiment plan validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_VALID_ROLES = frozenset({"reference", "proposed", "variant"})
_VALID_DIRECTIONS = frozenset({"minimize", "maximize"})
_SUPPORTED_KEYS = frozenset(
    {
        "conditions",
        "metrics",
        "protocol",
        "expected_figures",
        "expected_tables",
        "baselines",
        "ablations",
        "sample_size",
    }
)


@dataclass(frozen=True)
class ExperimentCondition:
    """One declared experimental condition."""

    name: str
    role: str
    description: str = ""


@dataclass(frozen=True)
class ExperimentMetric:
    """Primary metric declaration."""

    name: str
    direction: str


@dataclass(frozen=True)
class ExperimentPlan:
    """Design-only experiment plan overlay."""

    conditions: tuple[ExperimentCondition, ...] = ()
    primary_metric: ExperimentMetric | None = None
    protocol: str = ""
    expected_figures: tuple[str, ...] = ()
    expected_tables: tuple[str, ...] = ()
    baselines: tuple[str, ...] = ()
    ablations: tuple[str, ...] = ()
    sample_size: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExperimentPlanValidation:
    """Validation result for an experiment plan."""

    valid: bool
    issues: tuple[str, ...] = field(default_factory=tuple)


def load_experiment_plan(project_root: Path) -> ExperimentPlan | None:
    """Load optional ``experiment_plan.yaml`` from a project root."""
    path = project_root / "experiment_plan.yaml"
    if not path.exists():
        return None
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"experiment_plan.yaml must be a mapping: {path}")
    unknown = set(payload) - _SUPPORTED_KEYS
    if unknown:
        keys = ", ".join(sorted(str(key) for key in unknown))
        raise ValueError(f"unsupported experiment_plan key(s): {keys}")
    return ExperimentPlan(
        conditions=_parse_conditions(payload.get("conditions", [])),
        primary_metric=_parse_primary_metric(payload.get("metrics", {})),
        protocol=str(payload.get("protocol", "") or ""),
        expected_figures=_tuple_of_strings(payload.get("expected_figures")),
        expected_tables=_tuple_of_strings(payload.get("expected_tables")),
        baselines=_tuple_of_strings(payload.get("baselines")),
        ablations=_tuple_of_strings(payload.get("ablations")),
        sample_size=_mapping(payload.get("sample_size")),
    )


def validate_experiment_plan(plan: ExperimentPlan | None) -> ExperimentPlanValidation:
    """Validate an optional experiment plan."""
    if plan is None:
        return ExperimentPlanValidation(valid=True)
    issues: list[str] = []
    if not plan.conditions:
        issues.append("experiment plan must declare at least one condition")
    for condition in plan.conditions:
        if not condition.name:
            issues.append("experiment plan condition names must not be empty")
        if condition.role not in _VALID_ROLES:
            issues.append(f"invalid condition role for {condition.name}: {condition.role}")
    if plan.primary_metric is None or not plan.primary_metric.name:
        issues.append("experiment plan must declare a primary metric")
    elif plan.primary_metric.direction not in _VALID_DIRECTIONS:
        issues.append(f"invalid primary metric direction: {plan.primary_metric.direction}")
    if not plan.protocol.strip():
        issues.append("experiment plan must describe an evaluation protocol")
    if not plan.baselines and not any(condition.role == "reference" for condition in plan.conditions):
        issues.append("experiment plan must declare at least one baseline or reference condition")
    if not plan.ablations and not any(condition.role == "variant" for condition in plan.conditions):
        issues.append("experiment plan should declare at least one ablation or variant condition")
    for figure_id in plan.expected_figures:
        if not figure_id.startswith("fig:"):
            issues.append(f"expected figure id must start with fig: {figure_id}")
    for table_id in plan.expected_tables:
        if not table_id.startswith("tbl:"):
            issues.append(f"expected table id must start with tbl: {table_id}")
    return ExperimentPlanValidation(valid=not issues, issues=tuple(issues))


def _parse_conditions(raw: Any) -> tuple[ExperimentCondition, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError("experiment_plan conditions must be a list")
    conditions: list[ExperimentCondition] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("experiment_plan condition entries must be mappings")
        conditions.append(
            ExperimentCondition(
                name=str(item.get("name", "") or ""),
                role=str(item.get("role", "") or ""),
                description=str(item.get("description", "") or ""),
            )
        )
    return tuple(conditions)


def _parse_primary_metric(raw: Any) -> ExperimentMetric | None:
    if not isinstance(raw, dict):
        return None
    primary = raw.get("primary")
    if not isinstance(primary, dict):
        return None
    return ExperimentMetric(
        name=str(primary.get("name", "") or ""),
        direction=str(primary.get("direction", "") or ""),
    )


def _tuple_of_strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list | tuple):
        if not all(isinstance(item, str) for item in value):
            raise ValueError("experiment_plan values must be strings")
        return tuple(value)
    raise ValueError("experiment_plan values must be strings or lists of strings")


def _mapping(value: Any) -> dict[str, Any]:
    """Return an optional design metadata mapping without interpreting its fields."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("experiment_plan sample_size must be a mapping")
    return dict(value)
