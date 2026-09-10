from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .analysis_figures import (
    _figure_registry_entry,
    write_configured_field_matrix,
    write_field_origin_summary,
    write_provenance_trace_map,
    write_quality_gate_matrix,
    write_section_configuration_heatmap,
    write_section_token_allocation_figure,
    write_token_injection_flow_figure,
)
from .config import MadlibConfig
from .tokens import TokenPlan


class FigureRun(Protocol):
    @property
    def config(self) -> MadlibConfig: ...

    @property
    def plan(self) -> TokenPlan: ...

    @property
    def field_inventory(self) -> list[dict[str, str]]: ...

    @property
    def field_counts(self) -> dict[str, int]: ...


FigureWriter = Callable[[FigureRun, Path], Path]


@dataclass(frozen=True)
class ConditionalFigureSpec:
    """Data container for ConditionalFigureSpec."""

    flag: str
    artifact_key: str
    filename: str
    label: str
    caption: str
    section: str
    alt: str
    markdown_group: str


CONDITIONAL_FIGURE_SPECS: tuple[ConditionalFigureSpec, ...] = (
    ConditionalFigureSpec(
        flag="token_injection_flow",
        artifact_key="token_injection_flow",
        filename="token_injection_flow.png",
        label="fig:token-injection-flow",
        caption="Deterministic token-injection pipeline from config to rendered outputs",
        section="Methods",
        alt="Deterministic token-injection flow",
        markdown_group="methods",
    ),
    ConditionalFigureSpec(
        flag="section_token_allocation",
        artifact_key="section_token_allocation",
        filename="section_token_allocation.png",
        label="fig:section-token-allocation",
        caption="Section-level token allocation and enablement",
        section="Results",
        alt="Section token allocation",
        markdown_group="results",
    ),
    ConditionalFigureSpec(
        flag="provenance_trace_map",
        artifact_key="provenance_trace_map",
        filename="provenance_trace_map.png",
        label="fig:provenance-trace-map",
        caption="Token provenance by section and lexicon category",
        section="Results",
        alt="Provenance trace map",
        markdown_group="results",
    ),
    ConditionalFigureSpec(
        flag="quality_gate_matrix",
        artifact_key="quality_gate_matrix",
        filename="quality_gate_matrix.png",
        label="fig:quality-gate-matrix",
        caption="Quality gates, probes, and failure-boundary coverage",
        section="Evaluation",
        alt="Quality gate matrix",
        markdown_group="evaluation",
    ),
    ConditionalFigureSpec(
        flag="configured_field_matrix",
        artifact_key="configured_field_matrix",
        filename="configured_field_matrix.png",
        label="fig:configured-field-matrix",
        caption="Configured field origins by schema scope",
        section="Configuration",
        alt="Configured field origin matrix",
        markdown_group="configuration",
    ),
    ConditionalFigureSpec(
        flag="section_configuration_heatmap",
        artifact_key="section_configuration_heatmap",
        filename="section_configuration_heatmap.png",
        label="fig:section-configuration-heatmap",
        caption="Section-level configured field coverage",
        section="Configuration",
        alt="Section configuration heatmap",
        markdown_group="configuration",
    ),
    ConditionalFigureSpec(
        flag="field_origin_summary",
        artifact_key="field_origin_summary",
        filename="field_origin_summary.png",
        label="fig:field-origin-summary",
        caption="Explicit versus defaulted configured fields",
        section="Configuration",
        alt="Field origin summary",
        markdown_group="configuration",
    ),
)

_FIGURE_WRITERS: dict[str, FigureWriter] = {
    "token_injection_flow": lambda run, path: write_token_injection_flow_figure(run.config, run.plan, path),
    "section_token_allocation": lambda run, path: write_section_token_allocation_figure(run.config, run.plan, path),
    "provenance_trace_map": lambda run, path: write_provenance_trace_map(run.config, run.plan, path),
    "quality_gate_matrix": lambda run, path: write_quality_gate_matrix(run.config, path),
    "configured_field_matrix": lambda run, path: write_configured_field_matrix(run.field_inventory, path),
    "section_configuration_heatmap": lambda run, path: write_section_configuration_heatmap(run.config, run.plan, path),
    "field_origin_summary": lambda run, path: write_field_origin_summary(run.field_counts, path),
}


def visualization_enabled(config: MadlibConfig, flag: str) -> bool:
    """Process visualization enabled."""
    if not config.visualizations.enabled:
        return False
    return bool(getattr(config.visualizations, flag))


def write_conditional_figures(run: FigureRun, artifact_paths: dict[str, Path]) -> dict[str, dict[str, object]]:
    """Write conditional figures to the output path."""
    registry: dict[str, dict[str, object]] = {}
    for spec in CONDITIONAL_FIGURE_SPECS:
        if not visualization_enabled(run.config, spec.flag):
            continue
        output_path = artifact_paths[spec.artifact_key]
        _FIGURE_WRITERS[spec.artifact_key](run, output_path)
        registry[spec.label] = _figure_registry_entry(
            output_path.name,
            spec.caption,
            spec.label,
            spec.section,
            figure_alt_text(spec.artifact_key, run),
        )
    return registry


def figure_alt_text(artifact_key: str, run: FigureRun) -> str:
    """Describe a generated figure from the same run state used to draw it."""
    config = run.config
    plan = run.plan

    if artifact_key == "cover_overview":
        return (
            "Left-to-right configuration-to-publication overview with five boxes: "
            f"Config ({run.field_counts['explicit']} explicit paths and {len(config.lexicon)} lexicon lists), "
            f"TokenPlan ({len(plan.choices)} choices at seed {plan.seed}), IMRAD "
            f"({len(config.enabled_sections)} of {len(config.section_conditions)} sections enabled), Evidence "
            f"({len(config.method_protocol)} method steps and {len(config.quality_probes)} QA probes), and "
            "Outputs (PDF, HTML, slides, and copy). Four lower panels summarize field origins, token density, "
            "sections, and gates. This is a local generated audit view and does not imply external validation "
            "or reader quality."
        )

    if artifact_key == "token_density":
        counts = sorted(plan.category_counts.items(), key=lambda item: (item[1], item[0]))
        if not counts:
            return (
                "Empty horizontal token-density chart: the token plan contains no category choices, so no "
                "vocabulary allocation can be described."
            )
        bars = "; ".join(f"{category}: {count}" for category, count in counts)
        return (
            f"{len(counts)} horizontal bars encode selected token choices by lexicon category: {bars}. Counts "
            "come from the seeded token plan; they are not vocabulary-size or prose-quality scores."
        )

    if artifact_key == "token_injection_flow":
        return (
            "Five-stage left-to-right token-injection flow: schema parse; slot expansion "
            f"({len(config.slots)} rules and {len(plan.choices)} choices); section composition "
            f"({len(config.enabled_sections)} enabled sections); artifact writing; and render gates. Guard labels "
            "name parser tests, seed-stability tests, placeholder scanning, figure registry, and evidence "
            "registry. The diagram describes the configured method and does not assert that a particular render "
            "passed those gates."
        )

    if artifact_key == "section_token_allocation":
        rows = [
            f"{section}: {plan.section_counts.get(section, 0)} ({'enabled' if enabled else 'disabled'})"
            for section, enabled in config.section_conditions.items()
        ]
        if not rows:
            return (
                "Empty section-allocation chart: no manuscript sections are configured, so no token choices "
                "can be allocated."
            )
        return (
            f"{len(rows)} horizontal bars encode selected token choices and section enablement: "
            f"{'; '.join(rows)}. Muted rows are disabled; allocation counts do not measure prose quality."
        )

    if artifact_key == "provenance_trace_map":
        cells = Counter((choice.section, choice.category) for choice in plan.choices)
        if not cells:
            return (
                "Empty section-by-category provenance heatmap: the token plan contains no choices, so no "
                "provenance cells can be traced."
            )
        maximum = max(cells.values())
        strongest = sorted(f"{section}/{category}" for (section, category), count in cells.items() if count == maximum)
        return (
            f"Heatmap crossing {len(config.section_conditions)} manuscript sections with "
            f"{len(plan.category_counts)} lexicon categories. {len(plan.choices)} token choices occupy "
            f"{len(cells)} nonzero cells; the largest cell count is {maximum} at {', '.join(strongest)}. "
            "Cell counts trace generated choices and do not validate the truth of substituted prose."
        )

    if artifact_key == "quality_gate_matrix":
        criteria = ", ".join(criterion.name for criterion in config.evaluation_criteria) or "none"
        probes = ", ".join(probe.name for probe in config.quality_probes) or "none"
        failures = ", ".join(mode.name for mode in config.failure_modes) or "none"
        return (
            "Three declaration panels list configured review surfaces. Evaluation criteria "
            f"({len(config.evaluation_criteria)}): {criteria}. QA probes ({len(config.quality_probes)}): {probes}. "
            f"Failure modes ({len(config.failure_modes)}): {failures}. These are configured gates and failure "
            "boundaries, not results showing that the gates passed."
        )

    if artifact_key == "configured_field_matrix":
        scopes = ("schema", "section", "lexicon", "slot", "visualization")
        origin_cells = [
            (
                scope,
                sum(1 for row in run.field_inventory if row["scope"] == scope and row["origin"] == "explicit"),
                sum(1 for row in run.field_inventory if row["scope"] == scope and row["origin"] == "defaulted"),
            )
            for scope in scopes
        ]
        values = "; ".join(
            f"{scope}: {explicit} explicit, {defaulted} defaulted" for scope, explicit, defaulted in origin_cells
        )
        return (
            f"Five-by-two heatmap of tracked config-field paths by scope and origin: {values}. Counts describe "
            "configuration provenance and do not establish schema completeness."
        )

    if artifact_key == "section_configuration_heatmap":
        rows = []
        for section in config.section_conditions:
            prefix = "madlib"
            switch = "explicit" if f"{prefix}.section_conditions.{section}" in config.explicit_paths else "defaulted"
            title = "explicit" if f"{prefix}.section_titles.{section}" in config.explicit_paths else "defaulted"
            moves = "explicit" if f"{prefix}.narrative_moves.{section}" in config.explicit_paths else "defaulted"
            rows.append(
                f"{section}: switch {switch}, title {title}, moves {moves}, {plan.section_counts.get(section, 0)} slots"
            )
        if not rows:
            return (
                "Empty section-configuration heatmap: no section rows are configured, so no switch, title, "
                "move, or slot coverage can be shown."
            )
        return (
            f"{len(rows)}-row heatmap with columns for section switch, title, narrative moves, and slot count: "
            f"{'; '.join(rows)}. The matrix records configuration coverage, not manuscript quality."
        )

    if artifact_key == "field_origin_summary":
        return (
            "Two horizontal bars summarize configured-field provenance: "
            f"{run.field_counts['explicit']} explicit paths and {run.field_counts['defaulted']} defaulted paths, "
            f"out of {run.field_counts['total']} tracked paths. The counts identify origin and do not indicate "
            "validation status or research quality."
        )

    raise KeyError(f"unknown Madlib figure artifact key: {artifact_key!r}")


def specs_for_markdown_group(group: str) -> tuple[ConditionalFigureSpec, ...]:
    """Process specs for markdown group."""
    return tuple(spec for spec in CONDITIONAL_FIGURE_SPECS if spec.markdown_group == group)


def build_group_figure_markdown(config: MadlibConfig, group: str, *, disabled_message: str) -> str:
    """Build group figure markdown."""
    if group == "configuration" and not config.visualizations.enabled:
        return "Configured-field visualizations are disabled by `madlib.visualizations.enabled`."
    if group == "methods":
        if not visualization_enabled(config, "token_injection_flow"):
            return "Method pipeline visualization is disabled by `madlib.visualizations`."
    if group == "evaluation":
        if not visualization_enabled(config, "quality_gate_matrix"):
            return "Quality-gate visualization is disabled by `madlib.visualizations`."

    figures: list[str] = []
    if group == "results":
        figures.append(_figure_markdown("Token category density", "token_density.png", "fig:token-density"))

    for spec in specs_for_markdown_group(group):
        if visualization_enabled(config, spec.flag):
            figures.append(_figure_markdown(spec.alt, spec.filename, spec.label))

    if group == "configuration" and not figures:
        return "Configured-field visualizations are disabled by individual flags."
    return "\n\n".join(figures)


def _figure_markdown(alt: str, filename: str, label: str) -> str:
    return f"![{alt}](../output/figures/{filename}){{#{label}}}"
