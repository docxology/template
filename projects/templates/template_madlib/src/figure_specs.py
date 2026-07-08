from __future__ import annotations

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


def write_conditional_figures(run: FigureRun, artifact_paths: dict[str, Path]) -> dict[str, dict[str, str]]:
    """Write conditional figures to the output path."""
    registry: dict[str, dict[str, str]] = {}
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
        )
    return registry


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
