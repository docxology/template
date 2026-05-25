"""Configuration loading for AutoResearch readiness checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from infrastructure.autoresearch.models import (
    AutoResearchConfig,
    BenchmarkTask,
    BudgetPolicy,
    DEFAULT_QUALITY_CHECKS,
    ReviewGate,
)

_AUTONOMY_LEVELS = frozenset({"proposal_only", "human_approved", "sandboxed_execute"})
_METRIC_DIRECTIONS = frozenset({"maximize", "minimize", "target"})

_CONFIG_KEYS = frozenset(
    {
        "acceptance_policy",
        "autonomy_level",
        "benchmark_tasks",
        "budget",
        "disclosure_required",
        "disclosure_text",
        "edit_allowlist",
        "enabled",
        "metric_direction",
        "strict",
        "topic",
        "quality_checks",
        "review_gates",
        "source_manifests",
        "stage_gates",
        "required_artifacts",
    }
)


def load_autoresearch_config(project_root: Path) -> AutoResearchConfig:
    """Load optional ``autoresearch.yaml`` from a project root."""
    path = project_root / "autoresearch.yaml"
    if not path.exists():
        return AutoResearchConfig()

    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"autoresearch.yaml must be a mapping: {path}")
    unknown = set(payload) - _CONFIG_KEYS
    if unknown:
        keys = ", ".join(sorted(str(key) for key in unknown))
        raise ValueError(f"unsupported autoresearch key(s): {keys}")

    return AutoResearchConfig(
        enabled=_bool_value(payload.get("enabled", True), "enabled"),
        strict=_bool_value(payload.get("strict", False), "strict"),
        topic=str(payload.get("topic", "") or ""),
        autonomy_level=_choice_value(
            payload.get("autonomy_level", "proposal_only"),
            "autonomy_level",
            _AUTONOMY_LEVELS,
        ),
        budget_policy=_parse_budget_policy(payload.get("budget")),
        edit_allowlist=parse_string_sequence(payload.get("edit_allowlist"), default=()),
        metric_direction=_choice_value(
            payload.get("metric_direction", "maximize"),
            "metric_direction",
            _METRIC_DIRECTIONS,
        ),
        acceptance_policy=str(payload.get("acceptance_policy", "") or ""),
        review_gates=_parse_review_gates(payload.get("review_gates")),
        source_manifests=parse_string_sequence(payload.get("source_manifests"), default=()),
        benchmark_tasks=_parse_benchmark_tasks(payload.get("benchmark_tasks")),
        disclosure_required=_bool_value(payload.get("disclosure_required", False), "disclosure_required"),
        disclosure_text=str(payload.get("disclosure_text", "AI-assisted AutoResearch") or ""),
        quality_checks=parse_string_sequence(payload.get("quality_checks"), default=DEFAULT_QUALITY_CHECKS),
        stage_gates=parse_string_sequence(payload.get("stage_gates"), default=()),
        required_artifacts=parse_string_sequence(payload.get("required_artifacts"), default=()),
        source_path=str(path),
    )


def _bool_value(value: Any, key: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ValueError(f"autoresearch {key} must be a boolean")


def _choice_value(value: Any, key: str, choices: frozenset[str]) -> str:
    if not isinstance(value, str):
        raise ValueError(f"autoresearch {key} must be a string")
    normalized = value.strip()
    if normalized not in choices:
        allowed = ", ".join(sorted(choices))
        raise ValueError(f"autoresearch {key} must be one of: {allowed}")
    return normalized


def _parse_budget_policy(value: Any) -> BudgetPolicy:
    if value is None:
        return BudgetPolicy()
    if not isinstance(value, dict):
        raise ValueError("autoresearch budget must be a mapping")
    return BudgetPolicy(
        max_iterations=_nonnegative_int(value.get("max_iterations", 1), "budget.max_iterations"),
        max_wall_clock_minutes=_nonnegative_int(
            value.get("max_wall_clock_minutes", 30),
            "budget.max_wall_clock_minutes",
        ),
        max_llm_calls=_nonnegative_int(value.get("max_llm_calls", 0), "budget.max_llm_calls"),
        max_cost_usd=_nonnegative_float(value.get("max_cost_usd", 0.0), "budget.max_cost_usd"),
    )


def _nonnegative_int(value: Any, key: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"autoresearch {key} must be a non-negative integer")
    return int(value)


def _nonnegative_float(value: Any, key: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or value < 0:
        raise ValueError(f"autoresearch {key} must be a non-negative number")
    return float(value)


def _parse_review_gates(value: Any) -> tuple[ReviewGate, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("autoresearch review_gates must be a list")
    gates: list[ReviewGate] = []
    for row in value:
        if not isinstance(row, dict):
            raise ValueError("autoresearch review_gates entries must be mappings")
        name = str(row.get("name", "") or "").strip()
        if not name:
            raise ValueError("autoresearch review_gates entries must declare name")
        required = row.get("required", True)
        if not isinstance(required, bool):
            raise ValueError("autoresearch review_gates required must be a boolean")
        gates.append(
            ReviewGate(
                name=name,
                required=required,
                decision=str(row.get("decision", "") or ""),
            )
        )
    return tuple(gates)


def _parse_benchmark_tasks(value: Any) -> tuple[BenchmarkTask, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("autoresearch benchmark_tasks must be a list")
    tasks: list[BenchmarkTask] = []
    for row in value:
        if not isinstance(row, dict):
            raise ValueError("autoresearch benchmark_tasks entries must be mappings")
        identifier = str(row.get("id") or row.get("identifier") or "").strip()
        description = str(row.get("description", "") or "").strip()
        grading_output = str(row.get("grading_output", "") or "").strip()
        if not identifier or not description or not grading_output:
            raise ValueError("autoresearch benchmark_tasks entries must declare id, description, and grading_output")
        tasks.append(
            BenchmarkTask(
                identifier=identifier,
                description=description,
                grading_output=grading_output,
            )
        )
    return tuple(tasks)


def parse_string_sequence(value: Any, *, default: tuple[str, ...]) -> tuple[str, ...]:
    """Parse YAML sequence values into a tuple of strings."""
    if value is None:
        return default
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list | tuple):
        if not all(isinstance(item, str) for item in value):
            raise ValueError("autoresearch list values must be strings")
        return tuple(value)
    raise ValueError("autoresearch sequence values must be strings or lists of strings")
