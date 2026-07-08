from __future__ import annotations

from collections.abc import Mapping, Sequence

from .composition_helpers import _comma_join
from .config import MadlibConfig, SECTION_KEYS
from .tokens import TokenPlan


def build_section_plan_table(config: MadlibConfig, token_plan: TokenPlan) -> str:
    """Build section plan table."""
    rows = [
        "| Section | Render title | Enabled | Token choices | Narrative moves |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    counts = token_plan.section_counts
    for section in SECTION_KEYS:
        rows.append(
            f"| {section} | {config.section_titles[section]} | "
            f"{str(config.section_conditions.get(section, True))} | {counts.get(section, 0)} | "
            f"{_comma_join(config.narrative_moves[section])} |"
        )
    return "\n".join(rows)


def build_section_title_table(config: MadlibConfig) -> str:
    """Build section title table."""
    rows = ["| Section key | Rendered title | Enabled |", "| --- | --- | ---: |"]
    for section in SECTION_KEYS:
        rows.append(f"| `{section}` | {config.section_titles[section]} | {config.section_conditions[section]} |")
    return "\n".join(rows)


def build_token_inventory_table(token_plan: TokenPlan) -> str:
    """Build token inventory table."""
    rows = ["| Variable | Category | Value | Section | Source |", "| --- | --- | --- | --- | --- |"]
    for choice in token_plan.choices:
        rows.append(
            f"| `{choice.variable_name}` | {choice.category} | {choice.value} | "
            f"{choice.section} | `{choice.source_key}` |"
        )
    return "\n".join(rows)


def build_method_protocol_table(config: MadlibConfig) -> str:
    """Build method protocol table."""
    rows = ["| Step | Action | Evidence | Output |", "| --- | --- | --- | --- |"]
    for step in config.method_protocol:
        rows.append(f"| {step.name} | {step.action} | {step.evidence} | `{step.output}` |")
    return "\n".join(rows)


def build_audit_rule_table(config: MadlibConfig) -> str:
    """Build audit rule table."""
    rows = ["| Rule | Enforcement surface |", "| --- | --- |"]
    for index, rule in enumerate(config.audit_rules, start=1):
        rows.append(f"| R{index} | {rule} |")
    return "\n".join(rows)


def build_evaluation_criteria_table(config: MadlibConfig) -> str:
    """Build evaluation criteria table."""
    rows = ["| Criterion | Target | Evidence | Gate |", "| --- | --- | --- | --- |"]
    for criterion in config.evaluation_criteria:
        rows.append(f"| {criterion.name} | {criterion.target} | {criterion.evidence} | `{criterion.gate}` |")
    return "\n".join(rows)


def build_failure_mode_table(config: MadlibConfig) -> str:
    """Build failure mode table."""
    rows = ["| Failure mode | Risk | Detection | Mitigation |", "| --- | --- | --- | --- |"]
    for mode in config.failure_modes:
        rows.append(f"| {mode.name} | {mode.risk} | {mode.detection} | {mode.mitigation} |")
    return "\n".join(rows)


def build_configured_field_table(rows: Sequence[Mapping[str, str]]) -> str:
    """Build configured field table."""
    table = ["| Path | Origin | Scope | Summary |", "| --- | --- | --- | --- |"]
    for row in rows:
        table.append(f"| `{row['path']}` | {row['origin']} | {row['scope']} | {row['summary']} |")
    return "\n".join(table)


def build_configured_field_summary_table(counts: Mapping[str, int]) -> str:
    """Build configured field summary table."""
    rows = ["| Measure | Count |", "| --- | ---: |"]
    labels = (
        ("total", "Total tracked field paths"),
        ("explicit", "Explicit YAML paths"),
        ("defaulted", "Loader-defaulted paths"),
        ("visualized", "Enabled visualization flags"),
        ("section_level", "Section-level paths"),
        ("lexicon_level", "Lexicon-level paths"),
        ("slot_level", "Slot-level paths"),
        ("visualization_level", "Visualization-control paths"),
        ("schema_level", "Top-level schema paths"),
    )
    for key, label in labels:
        rows.append(f"| {label} | {counts.get(key, 0)} |")
    return "\n".join(rows)


def build_design_principle_table(config: MadlibConfig) -> str:
    """Build design principle table."""
    rows = ["| Principle | Rationale | Manuscript effect |", "| --- | --- | --- |"]
    for principle in config.design_principles:
        rows.append(f"| {principle.name} | {principle.rationale} | {principle.manuscript_effect} |")
    return "\n".join(rows)


def build_pipeline_phase_table(config: MadlibConfig) -> str:
    """Build pipeline phase table."""
    rows = [
        "| Phase | Input | Transformation | Output | Guard |",
        "| --- | --- | --- | --- | --- |",
    ]
    for phase in config.pipeline_phases:
        rows.append(
            f"| {phase.name} | `{phase.input_artifact}` | {phase.transformation} | "
            f"`{phase.output_artifact}` | {phase.guard} |"
        )
    return "\n".join(rows)


def build_quality_probe_table(config: MadlibConfig) -> str:
    """Build quality probe table."""
    rows = [
        "| Probe | Question | Passing signal | Artifact |",
        "| --- | --- | --- | --- |",
    ]
    for probe in config.quality_probes:
        rows.append(f"| {probe.name} | {probe.question} | {probe.passing_signal} | `{probe.artifact}` |")
    return "\n".join(rows)


def build_authoring_obligation_table(config: MadlibConfig) -> str:
    """Build authoring obligation table."""
    rows = ["| Obligation | Required action | Review surface |", "| --- | --- | --- |"]
    for obligation in config.authoring_obligations:
        rows.append(f"| {obligation.name} | {obligation.obligation} | `{obligation.review_surface}` |")
    return "\n".join(rows)


def build_contribution_table(config: MadlibConfig) -> str:
    """Build contribution table."""
    rows = ["| Claim | Boundary |", "| --- | --- |"]
    for claim in config.contribution_claims:
        rows.append(f"| {claim} | Local exemplar claim; no live DOI or standalone release implied. |")
    return "\n".join(rows)


def build_provenance_matrix_table(config: MadlibConfig, token_plan: TokenPlan) -> str:
    """Build provenance matrix table."""
    rows = ["| Section | Token variables | Source categories |", "| --- | ---: | --- |"]
    for section in SECTION_KEYS:
        choices = tuple(choice for choice in token_plan.choices if choice.section == section)
        categories = sorted({choice.category for choice in choices})
        variables = ", ".join(f"`{choice.variable_name}`" for choice in choices) or "none"
        rows.append(f"| {config.section_titles[section]} | {variables} | {_comma_join(categories)} |")
    return "\n".join(rows)
