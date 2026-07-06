from __future__ import annotations

from pathlib import Path

from .composition import (
    build_authoring_obligation_table,
    build_audit_rule_table,
    build_configured_field_summary_table,
    build_configured_field_table,
    build_configuration_figure_markdown,
    build_contribution_table,
    build_design_principle_table,
    build_evaluation_criteria_table,
    build_evaluation_figure_markdown,
    build_failure_mode_table,
    build_methods_figure_markdown,
    build_method_protocol_table,
    build_pipeline_phase_table,
    build_provenance_matrix_table,
    build_quality_probe_table,
    build_results_figure_markdown,
    build_section_plan_table,
    build_section_title_table,
    build_token_inventory_table,
)
from .run import MadlibRun, build_run


def artifact_markdown_tables(project_root: Path | str) -> dict[str, str]:
    return artifact_markdown_tables_from_run(build_run(project_root))


def artifact_markdown_tables_from_run(run: MadlibRun) -> dict[str, str]:
    config = run.config
    plan = run.plan
    inventory = run.field_inventory
    counts = run.field_counts
    return {
        "AUTHORING_OBLIGATION_TABLE": build_authoring_obligation_table(config),
        "AUDIT_RULE_TABLE": build_audit_rule_table(config),
        "CONFIGURATION_FIGURES": build_configuration_figure_markdown(config),
        "CONFIGURED_FIELD_FIGURES": build_configuration_figure_markdown(config),
        "CONFIGURED_FIELD_SUMMARY_TABLE": build_configured_field_summary_table(counts),
        "CONFIGURED_FIELD_TABLE": build_configured_field_table(inventory),
        "CONTRIBUTION_TABLE": build_contribution_table(config),
        "DESIGN_PRINCIPLE_TABLE": build_design_principle_table(config),
        "EVALUATION_FIGURES": build_evaluation_figure_markdown(config),
        "EVALUATION_CRITERIA_TABLE": build_evaluation_criteria_table(config),
        "FAILURE_MODE_TABLE": build_failure_mode_table(config),
        "METHODS_FIGURES": build_methods_figure_markdown(config),
        "METHOD_PROTOCOL_TABLE": build_method_protocol_table(config),
        "PIPELINE_PHASE_TABLE": build_pipeline_phase_table(config),
        "PROVENANCE_MATRIX_TABLE": build_provenance_matrix_table(config, plan),
        "QUALITY_PROBE_TABLE": build_quality_probe_table(config),
        "RESULTS_FIGURES": build_results_figure_markdown(config),
        "SECTION_PLAN_TABLE": build_section_plan_table(config, plan),
        "SECTION_TITLE_TABLE": build_section_title_table(config),
        "TOKEN_INVENTORY_TABLE": build_token_inventory_table(plan),
    }
