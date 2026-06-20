from __future__ import annotations

from pathlib import Path

from analysis_fields import configured_field_counts, configured_field_inventory
from analysis_figures import (
    _figure_registry_entry,
    write_configured_field_matrix,
    write_cover_overview_figure,
    write_field_origin_summary,
    write_provenance_trace_map,
    write_quality_gate_matrix,
    write_section_configuration_heatmap,
    write_section_token_allocation_figure,
    write_token_density_figure,
    write_token_injection_flow_figure,
)
from analysis_reports import (
    _configured_field_summary_markdown,
    _summary_markdown,
    _write_json,
    artifact_markdown_tables,
)
from composition import build_imrad_sections
from config import load_madlib_config
from tokens import generate_token_plan


def generate_artifacts(project_root: Path | str) -> dict[str, Path]:
    root = Path(project_root)
    config = load_madlib_config(root)
    plan = generate_token_plan(config)
    sections = build_imrad_sections(config, plan)

    data_dir = root / "output" / "data"
    reports_dir = root / "output" / "reports"
    figures_dir = root / "output" / "figures"
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
    configured_field_matrix = figures_dir / "configured_field_matrix.png"
    section_configuration_heatmap = figures_dir / "section_configuration_heatmap.png"
    field_origin_summary = figures_dir / "field_origin_summary.png"
    token_injection_flow = figures_dir / "token_injection_flow.png"
    section_token_allocation = figures_dir / "section_token_allocation.png"
    provenance_trace_map = figures_dir / "provenance_trace_map.png"
    quality_gate_matrix = figures_dir / "quality_gate_matrix.png"
    figure_registry = figures_dir / "figure_registry.json"
    field_inventory = configured_field_inventory(config, plan)
    field_counts = configured_field_counts(config, field_inventory)

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
        {
            "seed": config.seed,
            "composition_depth": config.composition_depth,
            "provenance": plan.provenance,
        },
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
    if config.visualizations.enabled and config.visualizations.token_injection_flow:
        write_token_injection_flow_figure(config, plan, token_injection_flow)
        registry["fig:token-injection-flow"] = _figure_registry_entry(
            token_injection_flow.name,
            "Deterministic token-injection pipeline from config to rendered outputs",
            "fig:token-injection-flow",
            "Methods",
        )
    if config.visualizations.enabled and config.visualizations.section_token_allocation:
        write_section_token_allocation_figure(config, plan, section_token_allocation)
        registry["fig:section-token-allocation"] = _figure_registry_entry(
            section_token_allocation.name,
            "Section-level token allocation and enablement",
            "fig:section-token-allocation",
            "Results",
        )
    if config.visualizations.enabled and config.visualizations.provenance_trace_map:
        write_provenance_trace_map(config, plan, provenance_trace_map)
        registry["fig:provenance-trace-map"] = _figure_registry_entry(
            provenance_trace_map.name,
            "Token provenance by section and lexicon category",
            "fig:provenance-trace-map",
            "Results",
        )
    if config.visualizations.enabled and config.visualizations.quality_gate_matrix:
        write_quality_gate_matrix(config, quality_gate_matrix)
        registry["fig:quality-gate-matrix"] = _figure_registry_entry(
            quality_gate_matrix.name,
            "Quality gates, probes, and failure-boundary coverage",
            "fig:quality-gate-matrix",
            "Evaluation",
        )
    if config.visualizations.enabled and config.visualizations.configured_field_matrix:
        write_configured_field_matrix(field_inventory, configured_field_matrix)
        registry["fig:configured-field-matrix"] = _figure_registry_entry(
            configured_field_matrix.name,
            "Configured field origins by schema scope",
            "fig:configured-field-matrix",
            "Configuration",
        )
    if config.visualizations.enabled and config.visualizations.section_configuration_heatmap:
        write_section_configuration_heatmap(config, plan, section_configuration_heatmap)
        registry["fig:section-configuration-heatmap"] = _figure_registry_entry(
            section_configuration_heatmap.name,
            "Section-level configured field coverage",
            "fig:section-configuration-heatmap",
            "Configuration",
        )
    if config.visualizations.enabled and config.visualizations.field_origin_summary:
        write_field_origin_summary(field_counts, field_origin_summary)
        registry["fig:field-origin-summary"] = _figure_registry_entry(
            field_origin_summary.name,
            "Explicit versus defaulted configured fields",
            "fig:field-origin-summary",
            "Configuration",
        )
    _write_json(figure_registry, registry)

    return {
        "token_inventory": token_inventory,
        "section_plan": section_plan,
        "configured_field_inventory": configured_field_inventory_path,
        "injection_trace": injection_trace,
        "summary": summary,
        "configured_field_summary": configured_field_summary,
        "cover_overview": cover_overview,
        "figure": figure,
        "configured_field_matrix": configured_field_matrix,
        "section_configuration_heatmap": section_configuration_heatmap,
        "field_origin_summary": field_origin_summary,
        "token_injection_flow": token_injection_flow,
        "section_token_allocation": section_token_allocation,
        "provenance_trace_map": provenance_trace_map,
        "quality_gate_matrix": quality_gate_matrix,
        "figure_registry": figure_registry,
    }


__all__ = [
    "artifact_markdown_tables",
    "configured_field_counts",
    "configured_field_inventory",
    "generate_artifacts",
    "write_configured_field_matrix",
    "write_cover_overview_figure",
    "write_field_origin_summary",
    "write_provenance_trace_map",
    "write_quality_gate_matrix",
    "write_section_configuration_heatmap",
    "write_section_token_allocation_figure",
    "write_token_density_figure",
    "write_token_injection_flow_figure",
]
