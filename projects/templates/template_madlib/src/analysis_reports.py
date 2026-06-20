from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis_fields import configured_field_counts, configured_field_inventory
from composition import (
    build_authoring_obligation_table,
    build_audit_rule_table,
    build_configured_field_summary_table,
    build_configured_field_table,
    build_configuration_figure_markdown,
    build_contribution_table,
    build_design_principle_table,
    build_evaluation_figure_markdown,
    build_evaluation_criteria_table,
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
from config import MadlibConfig, load_madlib_config
from tokens import TokenPlan, generate_token_plan


def artifact_markdown_tables(project_root: Path | str) -> dict[str, str]:
    config = load_madlib_config(project_root)
    plan = generate_token_plan(config)
    inventory = configured_field_inventory(config, plan)
    counts = configured_field_counts(config, inventory)
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


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _summary_markdown(config: MadlibConfig, plan: TokenPlan) -> str:
    density = "\n".join(f"- `{category}`: {count}" for category, count in sorted(plan.category_counts.items()))
    steps = "\n".join(f"- `{step.name}` -> `{step.output}`" for step in config.method_protocol)
    return "\n".join(
        [
            f"# {config.title} Madlib Generation Summary",
            "",
            f"- Seed: `{plan.seed}`",
            f"- Token choices: `{len(plan.choices)}`",
            f"- Enabled sections: `{len(config.enabled_sections)}`",
            f"- Method steps: `{len(config.method_protocol)}`",
            f"- Design principles: `{len(config.design_principles)}`",
            f"- Pipeline phases: `{len(config.pipeline_phases)}`",
            f"- Quality probes: `{len(config.quality_probes)}`",
            f"- Authoring obligations: `{len(config.authoring_obligations)}`",
            "- Category density:",
            density,
            "",
            "## Method Protocol",
            "",
            steps,
            "",
        ]
    )


def _configured_field_summary_markdown(
    config: MadlibConfig,
    counts: dict[str, int],
    inventory: list[dict[str, str]],
) -> str:
    rows = "\n".join(f"- `{row['path']}`: {row['origin']} ({row['scope']})" for row in inventory[:25])
    return "\n".join(
        [
            "# Configured Field Summary",
            "",
            f"- Explicit paths: `{counts['explicit']}`",
            f"- Defaulted paths: `{counts['defaulted']}`",
            f"- Enabled visualization flags: `{counts['visualized']}`",
            f"- Visualization flags: `{', '.join(config.visualizations.enabled_flags) or 'none'}`",
            "",
            "## First Inventory Rows",
            "",
            rows,
            "",
        ]
    )
