"""Reuse project evidence validators instead of accepting arbitrary JSON."""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from pathlib import Path

import yaml

from infrastructure.core.pipeline.artifacts import output_inventory_mode_for_project
from infrastructure.methods._plan_validation import _issue
from infrastructure.methods.models import MethodsIssue, MethodsOrchestrationPlan
from infrastructure.project.experiment_plan import load_experiment_plan, validate_experiment_plan
from infrastructure.validation.evidence_registry import (
    EVIDENCE_REGISTRY_REPORT_SCHEMA,
    EvidenceFact,
    build_project_evidence_registry,
    missing_evidence_source_paths,
)


def _fact_identity(row: dict[str, object]) -> str:
    return json.dumps({key: value for key, value in row.items() if key != "checked_at"}, sort_keys=True)


def _validate_evidence_registry(
    root: Path,
    path: Path,
    *,
    project_root: Path,
    issues: list[MethodsIssue],
) -> None:
    """Validate report schema and bind its sampled facts to current sources.

    A compact report is a summary, not a complete proof of every claim. The
    current shared registry supplies the full source-path validation boundary.
    """
    code = "METHODS.EVIDENCE_REGISTRY_INVALID"
    try:
        payload = json.loads((root / path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("schema") != EVIDENCE_REGISTRY_REPORT_SCHEMA:
            raise ValueError(f"evidence registry must use schema {EVIDENCE_REGISTRY_REPORT_SCHEMA}")
        count, omitted, rows = payload.get("fact_count"), payload.get("omitted_fact_count"), payload.get("sample_facts")
        if (
            type(count) is not int
            or count < 0
            or type(omitted) is not int
            or omitted < 0
            or not isinstance(rows, list)
            or count != len(rows) + omitted
        ):
            raise ValueError("evidence registry counts must describe its sample and omitted facts")
        for key in ("kind_counts", "source_tiers"):
            values = payload.get(key)
            if (
                not isinstance(values, dict)
                or any(
                    not isinstance(name, str) or type(value) is not int or value < 0 for name, value in values.items()
                )
                or sum(values.values()) != count
            ):
                raise ValueError(f"evidence registry {key} must contain non-negative counts totaling fact_count")
        for row in rows:
            if not isinstance(row, dict) or set(row) != set(EvidenceFact.__dataclass_fields__):
                raise ValueError("evidence registry sample facts must use the shared EvidenceFact schema")
            for key in ("kind", "value", "source", "source_path", "source_field", "source_tier", "checked_at"):
                if not isinstance(row[key], str):
                    raise ValueError(f"evidence fact {key} must be a string")
            if (
                type(row["active"]) is not bool
                or type(row["stale"]) is not bool
                or type(row["tolerance"]) not in {int, float}
                or not math.isfinite(row["tolerance"])
                or row["tolerance"] < 0
            ):
                raise ValueError("evidence fact flags and tolerance have invalid types")
        current = build_project_evidence_registry(
            project_root, output_inventory_mode=output_inventory_mode_for_project(root, project_root)
        )
        current_summary = current.to_compact_dict(sample_limit=0)
        for key in ("fact_count", "kind_counts", "source_tiers", "freshness_warnings"):
            if payload.get(key) != current_summary[key]:
                raise ValueError(f"evidence registry {key} no longer describes current sources")
        identities = {_fact_identity(asdict(fact)) for fact in current.facts()}
        if any(_fact_identity(row) not in identities for row in rows):
            raise ValueError("evidence registry contains a sampled fact not supported by current sources")
        missing = missing_evidence_source_paths(project_root, current, repo_root=root)
        if missing:
            raise ValueError(f"evidence registry references missing or unauthorized sources: {', '.join(missing)}")
    except FileNotFoundError:
        code = "METHODS.EVIDENCE_REGISTRY_MISSING"
        detail = f"required methods evidence file is missing: {path.as_posix()}"
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        detail = f"evidence registry is invalid: {exc}"
    else:
        return
    issues.append(
        _issue(
            "error",
            code,
            detail,
            path.as_posix(),
            "Regenerate the evidence report from current validated project artifacts.",
        )
    )


def _validate_optional_evidence(
    root: Path,
    plan: MethodsOrchestrationPlan,
    *,
    project_root: Path,
    issues: list[MethodsIssue],
) -> None:
    """Validate source-owned optional experiment plans with the shared validator."""
    if plan.experiment_plan is None:
        return
    try:
        result = validate_experiment_plan(load_experiment_plan(project_root))
        details = result.issues
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
        details = (str(exc),)
    for detail in details:
        issues.append(
            _issue(
                "error",
                "METHODS.EXPERIMENT_PLAN_INVALID",
                detail,
                plan.experiment_plan.as_posix(),
                "Repair the source-owned experiment plan against the shared project schema.",
            )
        )
