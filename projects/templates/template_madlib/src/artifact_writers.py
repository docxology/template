"""Registry of JSON and report artifact writers for Madlib analysis."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .analysis_reports import _configured_field_summary_markdown, _summary_markdown, _write_json
from .run import MadlibRun

__all__ = ["JsonArtifactSpec", "ReportArtifactSpec", "write_core_artifacts"]


@dataclass(frozen=True)
class JsonArtifactSpec:
    """Data container for JsonArtifactSpec."""

    key: str
    filename: str
    builder: Callable[[MadlibRun], object]


@dataclass(frozen=True)
class ReportArtifactSpec:
    """Data container for ReportArtifactSpec."""

    key: str
    filename: str
    builder: Callable[[MadlibRun], str]


def _section_plan_payload(run: MadlibRun) -> dict[str, object]:
    config = run.config
    plan = run.plan
    return {
        "enabled_sections": list(config.enabled_sections),
        "section_titles": config.section_titles,
        "section_conditions": config.section_conditions,
        "section_token_counts": plan.section_counts,
        "section_variables": sorted(run.sections),
        "explicit_paths": sorted(config.explicit_paths),
        "defaulted_paths": sorted(config.defaulted_paths),
        "configured_field_counts": run.field_counts,
        "visualizations": config.visualizations.__dict__,
        "narrative_moves": config.narrative_moves,
        "method_protocol": [step.__dict__ for step in config.method_protocol],
        "evaluation_criteria": [criterion.__dict__ for criterion in config.evaluation_criteria],
        "failure_modes": [mode.__dict__ for mode in config.failure_modes],
        "design_principles": [principle.__dict__ for principle in config.design_principles],
        "pipeline_phases": [phase.__dict__ for phase in config.pipeline_phases],
        "quality_probes": [probe.__dict__ for probe in config.quality_probes],
        "authoring_obligations": [obligation.__dict__ for obligation in config.authoring_obligations],
        "audit_rules": list(config.audit_rules),
        "contribution_claims": list(config.contribution_claims),
    }


JSON_ARTIFACTS: tuple[JsonArtifactSpec, ...] = (
    JsonArtifactSpec(
        "token_inventory",
        "token_inventory.json",
        lambda run: [choice.as_dict() for choice in run.plan.choices],
    ),
    JsonArtifactSpec(
        "configured_field_inventory",
        "configured_field_inventory.json",
        lambda run: run.field_inventory,
    ),
    JsonArtifactSpec(
        "section_plan",
        "section_plan.json",
        _section_plan_payload,
    ),
    JsonArtifactSpec(
        "injection_trace",
        "injection_trace.json",
        lambda run: {
            "seed": run.config.seed,
            "composition_depth": run.config.composition_depth,
            "provenance": run.plan.provenance,
        },
    ),
)

REPORT_ARTIFACTS: tuple[ReportArtifactSpec, ...] = (
    ReportArtifactSpec(
        "summary",
        "madlib_summary.md",
        lambda run: _summary_markdown(run.config, run.plan),
    ),
    ReportArtifactSpec(
        "configured_field_summary",
        "configured_field_summary.md",
        lambda run: _configured_field_summary_markdown(
            run.config,
            run.field_counts,
            run.field_inventory,
        ),
    ),
)


def write_core_artifacts(run: MadlibRun) -> dict[str, Path]:
    """Write JSON and Markdown report artifacts declared in the registries."""
    data_dir = run.project_root / "output" / "data"
    reports_dir = run.project_root / "output" / "reports"
    paths: dict[str, Path] = {}

    for json_spec in JSON_ARTIFACTS:
        target = (reports_dir if json_spec.filename == "injection_trace.json" else data_dir) / json_spec.filename
        _write_json(target, json_spec.builder(run))
        paths[json_spec.key] = target

    for report_spec in REPORT_ARTIFACTS:
        target = reports_dir / report_spec.filename
        target.write_text(report_spec.builder(run), encoding="utf-8")
        paths[report_spec.key] = target

    return paths
