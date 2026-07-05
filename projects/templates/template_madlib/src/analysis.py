from __future__ import annotations

from pathlib import Path

from analysis_figures import _figure_registry_entry, write_cover_overview_figure, write_token_density_figure
from analysis_reports import _configured_field_summary_markdown, _summary_markdown, _write_json
from figure_specs import CONDITIONAL_FIGURE_SPECS, write_conditional_figures
from run import build_run


def generate_artifacts(project_root: Path | str) -> dict[str, Path]:
    run = build_run(project_root)
    config = run.config
    plan = run.plan
    sections = run.sections
    field_inventory = run.field_inventory
    field_counts = run.field_counts

    data_dir = run.project_root / "output" / "data"
    reports_dir = run.project_root / "output" / "reports"
    figures_dir = run.project_root / "output" / "figures"
    for directory in (data_dir, reports_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)

    token_inventory = data_dir / "token_inventory.json"
    section_plan = data_dir / "section_plan.json"
    configured_field_inventory_path = data_dir / "configured_field_inventory.json"
    injection_trace = reports_dir / "injection_trace.json"
    summary = reports_dir / "madlib_summary.md"
    configured_field_summary = reports_dir / "configured_field_summary.md"
    cover_overview = figures_dir / "madlib_cover_overview.png"
    figure = figures_dir / "token_density.png"
    figure_registry = figures_dir / "figure_registry.json"

    _write_json(token_inventory, [choice.as_dict() for choice in plan.choices])
    _write_json(configured_field_inventory_path, field_inventory)
    _write_json(
        section_plan,
        {
            "enabled_sections": list(config.enabled_sections),
            "section_titles": config.section_titles,
            "section_conditions": config.section_conditions,
            "section_token_counts": plan.section_counts,
            "section_variables": sorted(sections),
            "explicit_paths": sorted(config.explicit_paths),
            "defaulted_paths": sorted(config.defaulted_paths),
            "configured_field_counts": field_counts,
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
        },
    )
    _write_json(
        injection_trace,
        {"seed": config.seed, "composition_depth": config.composition_depth, "provenance": plan.provenance},
    )
    summary.write_text(_summary_markdown(config, plan), encoding="utf-8")
    configured_field_summary.write_text(
        _configured_field_summary_markdown(config, field_counts, field_inventory),
        encoding="utf-8",
    )
    write_cover_overview_figure(config, plan, field_counts, cover_overview)
    write_token_density_figure(plan, figure)
    registry = {
        "fig:madlib-cover-overview": _figure_registry_entry(
            cover_overview.name,
            "Configuration-to-manuscript audit overview for the Madlib exemplar",
            "fig:madlib-cover-overview",
            "Cover",
        ),
        "fig:token-density": _figure_registry_entry(
            figure.name,
            "Token choices by lexicon category",
            "fig:token-density",
            "Results",
        ),
    }
    conditional_registry = write_conditional_figures(
        run,
        {spec.artifact_key: figures_dir / spec.filename for spec in CONDITIONAL_FIGURE_SPECS},
    )
    registry.update(conditional_registry)
    _write_json(figure_registry, registry)

    conditional_paths = {spec.artifact_key: figures_dir / spec.filename for spec in CONDITIONAL_FIGURE_SPECS}
    return {
        "token_inventory": token_inventory,
        "section_plan": section_plan,
        "configured_field_inventory": configured_field_inventory_path,
        "injection_trace": injection_trace,
        "summary": summary,
        "configured_field_summary": configured_field_summary,
        "cover_overview": cover_overview,
        "figure": figure,
        "figure_registry": figure_registry,
        **conditional_paths,
    }


__all__ = ["generate_artifacts"]
